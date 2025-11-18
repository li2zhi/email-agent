import ast
import os
import random

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from langgraph.constants import END
from langgraph.store.base import BaseStore
from langgraph.types import Command, interrupt

from template.prompt import default_triage_instructions, triage_system_prompt, default_background, triage_user_prompt, \
    default_response_preferences, default_cal_preferences, \
    agent_system_prompt_hitl_memory, email_triage_preference_info, email_modify_preference_info
from template.protocol import State, RouterSchema, INTERRUPT_TRIAGE
from template.tools import agent_tools, tools_by_name
from util.memory_manager import MemoryManager
from util.utils import format_email_markdown, parse_email

load_dotenv(override=True)

llm_router = init_chat_model(
    model='deepseek-chat',
    model_provider='deepseek',
    api_key=os.getenv('DEEPSEEK_API_KEY')
).with_structured_output(RouterSchema)

llm_with_tools = init_chat_model(
    model='deepseek-chat',
    model_provider='deepseek',
    api_key=os.getenv('DEEPSEEK_API_KEY')
).bind_tools(agent_tools)

memoryManager = MemoryManager()

# 邮件分类
def email_triage(state: State, store: BaseStore) -> Command:
    author, to, subject, email_thread = parse_email(state["email_input"])
    email_markdown = format_email_markdown(subject, author, to, email_thread)

    # 从记忆中获取用户偏好
    triage_instructions = memoryManager.get_memory(store, "email_assistant", "triage_preferences",
                                                   default_triage_instructions)

    system_prompt = triage_system_prompt.format(
        background=default_background,
        triage_instructions=triage_instructions,
    )

    user_prompt = triage_user_prompt.format(
        author=author, to=to, subject=subject, email_thread=email_thread
    )

    result = llm_router.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )

    print(f"===========原邮件内容==========={email_markdown}")

    if result.classification == "respond":
        print("📧 RESPOND - 这封邮件需要进行回复")
        print(f"📧 分析：{result.reasoning}")

        update = {
            "classification_decision": result.classification,
            "messages": [{"role": "user", "content": f"请回复该邮件: {email_markdown}"}],
        }
    elif result.classification == "ignore":
        print("🚫 IGNORE - 这封邮件可以忽略")
        print(f"🚫 分析：{result.reasoning}")

        update = {"classification_decision": result.classification}
    elif result.classification == "notify":
        print("🔔 NOTIFY - 这封邮件包含重要信息")
        print(f"🔔 分析：{result.reasoning}")

        update = {"classification_decision": result.classification}
    else:
        raise ValueError(f"Invalid classification: {result.classification}")

    return Command(update=update)


# 分类结果路由
def route_triage_decision(state: State, store: BaseStore) -> str:
    """根据分类决策路由到不同节点"""
    classification = state.get("classification_decision")

    if classification == "respond":
        return "email_response"
    elif classification == "notify":
        return "end"
    elif classification == "ignore":
        return "end"
    else:
        # 默认回退
        return "email_response"


# 分类结果交互
def triage_interrupt_handler(state: State, store: BaseStore) -> Command:
    author, to, subject, email_thread = parse_email(state["email_input"])
    email_markdown = format_email_markdown(subject, author, to, email_thread)
    update = {}

    if random.random() < 0.6:
        return Command(update=update)

    request = {
        "action": f"请您确认邮件分类结果: {state['classification_decision']}",
        "tag": INTERRUPT_TRIAGE,
        "classification": state['classification_decision']
    }
    response = interrupt(request)

    if response["type"] != state['classification_decision']:
        messages = [{
            "role": "user",
            "content": email_triage_preference_info.format(
                system_result=state['classification_decision'],
                email=email_markdown,
                user_result=response["type"],
                reason=response["reason"],
            )
        }]

        memoryManager.update_memory(store, "email_assistant", "triage_preferences", messages)
        update['classification_decision'] = response["type"]

        if response["type"] == "respond":
            update["messages"] = [{"role": "user", "content": f"用户想要回复此邮件，给出的理由是: {response["reason"]}"}]

    return Command(update=update)


def llm_call(state: State, store: BaseStore):
    cal_preferences = memoryManager.get_memory(store, "email_assistant", "cal_preferences", default_cal_preferences)
    response_preferences = memoryManager.get_memory(store, "email_assistant", "response_preferences",
                                                    default_response_preferences)

    response = llm_with_tools.invoke(
        [
            {"role": "system", "content": agent_system_prompt_hitl_memory.format(
                background=default_background,
                response_preferences=response_preferences,
                cal_preferences=cal_preferences
            )}
        ]
        + state["messages"]
    )

    return {"messages": [response]}


def tool_execute(state: State, store: BaseStore) -> Command:
    result = []

    last_message = state["messages"][-1]
    if last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool = tools_by_name[tool_call["name"]]

            observation = tool.invoke(tool_call["args"])
            result.append({"role": "tool", "content": observation, "tool_call_id": tool_call["id"]})

    return Command(update={"messages": result})


def route_next_step(state: State, store: BaseStore):
    idx = len(state["messages"]) - 1
    last_message = state["messages"][idx]

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tool_execute"

    # find last AIMessage
    while idx > 0:
        if isinstance(last_message, AIMessage):
            break

        idx -= 1
        last_message = state["messages"][idx]

    if last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            if tool_call["name"] == "send_email":
                return END

            if tool_call["name"] == "ack_email_content":
                email_respond_modify(state, store)

    return "email_response"


def email_respond_modify(state: State, store: BaseStore):
    tool_msg = state["messages"][-1]
    ai_msg = state["messages"][-2]

    tool_content = tool_msg.content
    tool_content_dict = ast.literal_eval(tool_content)

    if tool_content_dict["modify"]:
        messages = [{
            "role": "user",
            "content": email_modify_preference_info.format(email=ai_msg.content,
                                                           suggestion=tool_content_dict["suggestion"])
        }]

        memoryManager.update_memory(store, "email_assistant", "response_preferences", messages)
