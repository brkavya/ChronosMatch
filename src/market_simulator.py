import asyncio
import random
from src.ring_buffer import MmapRingBuffer


class AsyncMarketSimulator:
    def __init__(self, buffer: MmapRingBuffer, rate_per_second: int = 100):
        self.buffer = buffer
        self.interval = 1.0 / rate_per_second
        self.running = False
        self._next_order_id = 1

    async def generate_order(self):
        """Generates a realistic mock trade or cancellation order."""
        order_id = self._next_order_id
        self._next_order_id += 1

        base_price = 2450.00
        spread_offset = random.uniform(-2.5, 2.5)
        price = round(base_price + spread_offset, 2)

        quantity = random.choice([5, 10, 25, 50, 100])

        # B = Buy, S = Sell, C = Cancel
        side = random.choices(
            ["B", "S", "C"],
            weights=[45, 45, 10],
            k=1
        )[0]

        return order_id, price, quantity, side

    async def run(self, max_orders: int = 50):
        """Simulates asynchronous high-frequency order dispatch."""
        self.running = True
        count = 0

        print(f"[Simulator] Launching order stream ({max_orders} orders)...")

        while self.running and count < max_orders:
            order_id, price, qty, side = await self.generate_order()

            success = self.buffer.write_order(
                order_id,
                price,
                qty,
                side
            )

            if success:
                count += 1

                if count % 10 == 0 or count == max_orders:
                    print(
                        f"[Simulator] Injected order #{order_id}: "
                        f"{side} {qty} @ {price}"
                    )
            else:
                await asyncio.sleep(0.001)

            await asyncio.sleep(self.interval)

        print(
            f"[Simulator] Stream complete. "
            f"Total injected: {count} orders."
        )


if __name__ == "__main__":
    import os

    test_path = "chronos_sim_buffer.bin"

    ring = MmapRingBuffer(
        test_path,
        capacity=100
    )

    sim = AsyncMarketSimulator(
        ring,
        rate_per_second=500
    )

    # Run the event loop
    asyncio.run(
        sim.run(max_orders=30)
    )

    # Read back generated orders
    print("\n[Engine Verification] Polling orders from buffer:")

    consumed = 0

    while True:
        order = ring.read_order()

        if order is None:
            break

        consumed += 1

        if consumed <= 5 or consumed >= 28:
            print(
                f"  Verified order #{order[0]}: "
                f"{order[3]} {order[2]} @ {order[1]}"
            )

    print(
        f"Total verified in ring buffer: {consumed}"
    )

    ring.close()

    if os.path.exists(test_path):
        os.remove(test_path)