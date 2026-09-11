import os
import sqlite3
import time
from typing import List, Tuple


class TradeDatabase:

    def __init__(self, db_path: str = "chronos_trades.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    maker_order_id INTEGER NOT NULL,
                    taker_order_id INTEGER NOT NULL,
                    price REAL NOT NULL,
                    quantity INTEGER NOT NULL,
                    timestamp_ns INTEGER NOT NULL
                )
            """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp_ns)"
            )
            conn.commit()
        finally:
            conn.close()

    def record_trades_batch(
        self, trades: List[Tuple[int, int, float, int]]
    ) -> int:
        """Persists executed trades as a batch using a single transaction."""
        if not trades:
            return 0

        ts_ns = time.perf_counter_ns()
        records = [
            (maker_id, taker_id, price, qty, ts_ns)
            for (maker_id, taker_id, price, qty) in trades
        ]

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.executemany(
                """
                INSERT INTO trades (maker_order_id, taker_order_id, price, quantity, timestamp_ns)
                VALUES (?, ?, ?, ?, ?)
            """,
                records,
            )
            conn.commit()
        finally:
            conn.close()

        return len(records)

    def fetch_latest_trades(self, limit: int = 10) -> list:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT trade_id, maker_order_id, taker_order_id, price, quantity, timestamp_ns
                FROM trades
                ORDER BY trade_id DESC
                LIMIT ?
            """,
                (limit,),
            )
            return cursor.fetchall()
        finally:
            conn.close()


if __name__ == "__main__":
    test_db = "test_chronos.db"
    db = TradeDatabase(test_db)

    sample_trades = [
        (101, 201, 2450.50, 15),
        (102, 201, 2450.50, 10),
        (105, 202, 2451.00, 50),
    ]

    inserted = db.record_trades_batch(sample_trades)
    print(f"Persisted {inserted} trades.")

    rows = db.fetch_latest_trades(5)
    print("Latest trades retrieved from DB:")
    for row in rows:
        print(
            f"  Trade #{row[0]}: Maker {row[1]} <-> Taker {row[2]} | {row[4]} @ {row[3]}"
        )

    if os.path.exists(test_db):
        try:
            os.remove(test_db)
        except PermissionError:
            time.sleep(0.1)
            os.remove(test_db)