import asyncio
import os
import time
from src.market_simulator import AsyncMarketSimulator
from src.order_book import OrderBook
from src.ring_buffer import MmapRingBuffer
from src.trade_db import TradeDatabase


class ChronosEngine:

    def __init__(
        self, buffer_file: str = "chronos_mmap.bin", capacity: int = 1000
    ):
        self.buffer_file = buffer_file
        self.ring = MmapRingBuffer(buffer_file, capacity=capacity)
        self.book = OrderBook()
        self.db = TradeDatabase("chronos_trades.db")
        self.simulator = AsyncMarketSimulator(self.ring, rate_per_second=200)
        self.total_matched = 0

    async def consumer_matching_loop(self, max_orders: int = 60):
        processed = 0
        batch_trades = []

        print("[Engine] Matching loop initialized. Polling ring buffer...")

        while processed < max_orders:
            order = self.ring.read_order()
            if order is None:
                await asyncio.sleep(0.0005)
                continue

            order_id, price, qty, side = order
            processed += 1

            t0 = time.perf_counter_ns()
            trades = self.book.add_order(order_id, price, qty, side)
            latency = time.perf_counter_ns() - t0

            if trades:
                self.total_matched += len(trades)
                batch_trades.extend(trades)
                for maker_id, taker_id, match_px, match_sz in trades:
                    print(
                        f"  [MATCH] Maker #{maker_id} vs Taker #{taker_id} |"
                        f" {match_sz} @ {match_px:.2f} ({latency} ns)"
                    )

            if len(batch_trades) >= 5:
                self.db.record_trades_batch(batch_trades)
                batch_trades.clear()

        if batch_trades:
            self.db.record_trades_batch(batch_trades)

        print(
            f"[Engine] Complete. Processed: {processed} orders | Total matches:"
            f" {self.total_matched}"
        )

    async def start(self, order_count: int = 60):
        print("=== ChronosMatch Real-Time Engine Launching ===")
        await asyncio.gather(
            self.simulator.run(max_orders=order_count),
            self.consumer_matching_loop(max_orders=order_count),
        )
        self.ring.close()
        if os.path.exists(self.buffer_file):
            try:
                os.remove(self.buffer_file)
            except OSError:
                pass


if __name__ == "__main__":
    engine = ChronosEngine()
    asyncio.run(engine.start(order_count=60))