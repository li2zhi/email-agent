import uuid

from IPython.display import Image, display
from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import END, START
from langgraph.graph import StateGraph
from langgraph.store.memory import InMemoryStore
from langgraph.types import Command

from template.nodes import email_triage, triage_interrupt_handler, route_triage_decision, route_next_step, llm_call, \
    tool_execute
from template.protocol import State, StateInput, INTERRUPT_TAGS
from template.data_generate import TestDataManager
from util.memory_manager import display_memory_content

overall_workflow = (
    StateGraph(State, input=StateInput)
    .add_node("triage_router", email_triage)
    .add_node("triage_interrupt_handler", triage_interrupt_handler)
    .add_node("llm_call", llm_call)
    .add_node("tool_execute", tool_execute)
    .add_edge(START, "triage_router")
    .add_edge("triage_router", "triage_interrupt_handler")
    .add_conditional_edges(
        "triage_interrupt_handler",
        route_triage_decision,
        {
            "llm_call": "llm_call",
            "end": END
        }
    )
    .add_conditional_edges(
        "llm_call",
        route_next_step,
        {
            "tool_execute": "tool_execute",
            END: END
        }
    )
    .add_conditional_edges(
        "tool_execute",
        route_next_step,
        {
            "llm_call": "llm_call",
            END: END
        }
    )
)

checkpointer = MemorySaver()
store = InMemoryStore()
graph = overall_workflow.compile(checkpointer=checkpointer, store=store)

# display(Image(graph.get_graph().draw_mermaid_png()))
png_data = graph.get_graph().draw_mermaid_png()
with open('graph.png', 'wb') as f:
    f.write(png_data)

manager = TestDataManager("examples/test_emails.json")
data_list = manager.load_test_data()

for data in data_list:
    thread_config = {"configurable": {"thread_id": uuid.uuid4()}}
    next_input = {"email_input": data}

    while True:
        saw_any_interrupt = False

        for event in graph.stream(next_input, thread_config):
            if "__interrupt__" in event:
                Interrupt_Object = event["__interrupt__"][0]
                feedback = INTERRUPT_TAGS[Interrupt_Object.value["tag"]](Interrupt_Object.value)

                next_input = Command(resume=feedback)
                saw_any_interrupt = True
                break

        if not saw_any_interrupt:
            break

    display_memory_content(store)
