from sql.sqlite_manager import SQLiteDB

sqliteDB = SQLiteDB("agent-memory.db")

res = sqliteDB.base_select("select * from preference")
print(res)
