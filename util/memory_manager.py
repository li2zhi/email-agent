import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

from template.prompt import MEMORY_UPDATE_INSTRUCTIONS
from template.protocol import UserPreferences

load_dotenv(override=True)

llm = init_chat_model(
    model='deepseek-chat',
    model_provider='deepseek',
    api_key=os.getenv('DEEPSEEK_API_KEY')
)


def get_memory(store, namespace, default_content=None):
    """Get memory from the store or initialize with default if it doesn't exist."""

    user_preferences = store.get(namespace, "user_preferences")

    if user_preferences:
        return user_preferences.value
    else:
        store.put(namespace, "user_preferences", default_content)
        return default_content


def update_memory(store, namespace, messages):
    user_preferences = store.get(namespace, "user_preferences")
    memory_updater_llm = llm.with_structured_output(UserPreferences)

    result = memory_updater_llm.invoke(
        [
            {"role": "system",
             "content": MEMORY_UPDATE_INSTRUCTIONS.format(current_profile=user_preferences.value, namespace=namespace)},
        ]
        + messages
    )

    store.put(namespace, "user_preferences", result.user_preferences)


def display_memory_content(store, namespace=None):
    print("\n======= CURRENT MEMORY CONTENT =======")

    if namespace:
        memory = store.get(namespace, "user_preferences")
        print(f"\n--- {namespace[1]} ---")
        if memory:
            print(memory.value)
        else:
            print("No memory found")

    else:
        for ns in [
            ("email_assistant", "triage_preferences"),
            ("email_assistant", "response_preferences"),
            # ("email_assistant", "cal_preferences"),
            # ("email_assistant", "background")
        ]:
            memory = store.get(ns, "user_preferences")
            print(f"\n--- {ns[1]} ---")
            if memory:
                print(memory.value)
            else:
                print("No memory found")
            print("=======================================\n")
