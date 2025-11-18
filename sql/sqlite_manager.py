import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class SQLiteDB:
    def __init__(self, db_name):
        self.db_path = os.path.join(BASE_DIR, db_name)

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn


    def base_select(self, statement: str, params = None, num = None):
        conn = self._connect()
        cursor = conn.cursor()

        try:
            cursor.execute(statement, params or [])
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            cursor.close()
            conn.close()


    def base_modify(self, statement: str, params=None):
        """
        Common Insert、Update、Delete
        """
        conn = self._connect()
        cursor = conn.cursor()

        try:
            cursor.execute(statement, params or [])
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()