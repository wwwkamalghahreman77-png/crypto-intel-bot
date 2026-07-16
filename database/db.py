import sqlite3
import os
from datetime import datetime
from config.settings import settings


SQLITE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data.db"
)


CREATE_TABLES_SQL = {

    "dex_discoveries": """
        CREATE TABLE IF NOT EXISTS dex_discoveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT,
            network TEXT,
            date_found TEXT,
            security_score REAL,
            dex_score REAL,
            price_found REAL,
            liquidity REAL,
            volume REAL,
            status TEXT
        )
    """,

    "crypto_reports": """
        CREATE TABLE IF NOT EXISTS crypto_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT,
            date_found TEXT,
            total_score REAL,
            security REAL,
            fundamental REAL,
            news REAL,
            technical REAL,
            community REAL,
            status TEXT
        )
    """,

    "signal_history": """
        CREATE TABLE IF NOT EXISTS signal_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT,
            signal_type TEXT,
            price REAL,
            score REAL,
            date_found TEXT
        )
    """,

    "performance_tracking": """
        CREATE TABLE IF NOT EXISTS performance_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT,
            initial_price REAL,
            price_7d REAL,
            price_30d REAL,
            result TEXT
        )
    """,

    "active_signals": """
        CREATE TABLE IF NOT EXISTS active_signals (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            symbol TEXT,
            signal_type TEXT,

            entry_price REAL,

            tp1 REAL,
            tp2 REAL,
            tp3 REAL,
            tp4 REAL,

            stop_loss REAL,

            telegram_chat_id TEXT,
            telegram_message_id INTEGER,

            status TEXT,

            hit_tp1 INTEGER DEFAULT 0,
            hit_tp2 INTEGER DEFAULT 0,
            hit_tp3 INTEGER DEFAULT 0,
            hit_tp4 INTEGER DEFAULT 0,
            hit_stop INTEGER DEFAULT 0,

            date_found TEXT
        )
    """,

}



class Database:


    def __init__(self):

        self.use_supabase = settings.use_supabase

        if self.use_supabase:

            self._init_supabase()

        else:

            self._init_sqlite()



    def _init_sqlite(self):

        self.conn = sqlite3.connect(
            SQLITE_PATH
        )

        self.conn.row_factory = sqlite3.Row


        cur = self.conn.cursor()


        for sql in CREATE_TABLES_SQL.values():

            cur.execute(sql)


        self.conn.commit()




    def _init_supabase(self):

        from supabase import create_client

        self.client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )




    def insert(
        self,
        table: str,
        data: dict
    ):


        data = dict(data)


        if self.use_supabase:

            return (
                self.client
                .table(table)
                .insert(data)
                .execute()
            )


        else:

            columns = ", ".join(
                data.keys()
            )


            placeholders = ", ".join(
                ["?"] * len(data)
            )


            values = list(
                data.values()
            )


            cur = self.conn.cursor()


            cur.execute(
                f"""
                INSERT INTO {table}
                ({columns})
                VALUES ({placeholders})
                """,
                values
            )


            self.conn.commit()


            return cur.lastrowid





    def fetch_all(
        self,
        table: str,
        limit: int = 50
    ):


        if self.use_supabase:


            res = (
                self.client
                .table(table)
                .select("*")
                .order(
                    "id",
                    desc=True
                )
                .limit(limit)
                .execute()
            )


            return res.data



        else:


            cur = self.conn.cursor()


            cur.execute(
                f"""
                SELECT *
                FROM {table}
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,)
            )


            rows = cur.fetchall()


            return [
                dict(row)
                for row in rows
            ]





    def fetch_by_token(
        self,
        table: str,
        token: str
    ):


        if self.use_supabase:


            res = (
                self.client
                .table(table)
                .select("*")
                .eq(
                    "token",
                    token
                )
                .execute()
            )


            return res.data



        else:


            cur = self.conn.cursor()


            cur.execute(
                f"""
                SELECT *
                FROM {table}
                WHERE token = ?
                """,
                (token,)
            )


            rows = cur.fetchall()


            return [
                dict(row)
                for row in rows
            ]


    def fetch_active(
        self,
        table: str,
        status: str = "active",
        limit: int = 500
    ):

        if self.use_supabase:

            res = (
                self.client
                .table(table)
                .select("*")
                .eq("status", status)
                .execute()
            )

            return res.data

        cur = self.conn.cursor()

        cur.execute(
            f"SELECT * FROM {table} WHERE status = ? ORDER BY id DESC LIMIT ?",
            (status, limit)
        )

        return [dict(row) for row in cur.fetchall()]


    def update(
        self,
        table: str,
        row_id,
        data: dict
    ):

        data = dict(data)

        if self.use_supabase:

            return (
                self.client
                .table(table)
                .update(data)
                .eq("id", row_id)
                .execute()
            )

        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        values = list(data.values()) + [row_id]

        cur = self.conn.cursor()

        cur.execute(
            f"UPDATE {table} SET {set_clause} WHERE id = ?",
            values
        )

        self.conn.commit()

        return cur.rowcount





    def token_exists(
        self,
        table: str,
        token: str
    ) -> bool:


        return len(
            self.fetch_by_token(
                table,
                token
            )
        ) > 0





db = Database()



def now_str() -> str:

    return datetime.utcnow().strftime(
        "%Y-%m-%d %H:%M:%S"
    )
