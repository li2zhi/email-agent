import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

from sql.sqlite_manager import SQLiteDB
from template.prompt import MEMORY_UPDATE_INSTRUCTIONS
from template.protocol import UserPreferences

load_dotenv(override=True)


class MemoryManager:
    def __init__(self):
        self.llm = init_chat_model(
            model='deepseek-chat',
            model_provider='deepseek',
            api_key=os.getenv('DEEPSEEK_API_KEY')
        )
        self.sqliteDB = SQLiteDB("agent-memory.db")
        self.init_flag = False


    def update_memory(self, store, namespace, key, messages):
        user_preferences = store.get(namespace, key)
        memory_updater_llm = self.llm.with_structured_output(UserPreferences)

        result = memory_updater_llm.invoke(
            [
                {"role": "system",
                 "content": MEMORY_UPDATE_INSTRUCTIONS.format(current_profile=user_preferences.value,
                                                              namespace=namespace)},
            ]
            + messages
        )

        if store.get(namespace, key):
            self.update_memory_in_db(store, namespace, key, result.user_preferences)
        else:
            self.save_memory_in_db(store, namespace, key, result.user_preferences)


    def get_memory(self, store, namespace, key, default_content=None):
        """Get memory from the store or initialize with default if it doesn't exist."""

        if not self.init_flag:
            self.init_memory_store(store)
            self.init_flag = True

        user_preferences = store.get(namespace, key)

        if user_preferences:
            return user_preferences.value
        else:
            self.save_memory_in_db(store, namespace, key, default_content)
            return default_content


    def init_memory_store(self, store):
        res = self.sqliteDB.base_select("select * from preference")

        if len(res) < 1:
            return

        for data in res:
            store.put(data['namespace'], data['unique_key'], data['content'])

        print(f"从DB中加载了{len(res)}条记忆")


    def save_memory_in_db(self, store, namespace, key, value):
        store.put(namespace, key, value)
        self.sqliteDB.base_modify("insert into preference(namespace, unique_key, content) values(?,?,?)",
                                  (namespace, key, value))


    def update_memory_in_db(self, store, namespace, key, value):
        store.put(namespace, key, value)
        count = self.sqliteDB.base_modify(
            "update preference set content = ?, updated_time = datetime('now') where namespace = ? and unique_key = ?",
            (value, namespace, key))

        if count == 0:
            print(f"记忆更新失败, namespace: {namespace}, key: {key}, value: {value}")


def display_memory_content(store, namespace=None):
    print("\n======= CURRENT MEMORY CONTENT =======")

    for ns in [
        ("email_assistant", "triage_preferences"),
        ("email_assistant", "response_preferences"),
    ]:
        memory = store.get(ns[0], ns[1])
        print(f"\n--- {ns[1]} ---")
        if memory:
            print(memory.value)
        else:
            print("No memory found")
        print("=======================================\n")
