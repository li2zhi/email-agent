from langchain_core.tools import tool
from langgraph.types import interrupt

from template.protocol import SendEmailParam, AskUserParam, INTERRUPT_ASK_USER, INTERRUPT_ACK_EMAIL


@tool(description="发送邮件", args_schema=SendEmailParam)
def send_email(to, subject, content):
    return "邮件发送成功"


@tool(description="询问用户意见", args_schema=AskUserParam)
def ask_user(content):
    response = interrupt({
        "action": f"{content}",
        "tag": INTERRUPT_ASK_USER
    })
    return response


@tool(description="确认即将发送的邮件内容")
def ack_email_content(content):
    response = interrupt({
        "action": f"{content}",
        "tag": INTERRUPT_ACK_EMAIL
    })
    return response

agent_tools = [send_email, ask_user, ack_email_content]


tools_by_name = {
    "send_email": send_email,
    "ask_user": ask_user,
    "ack_email_content": ack_email_content,
}