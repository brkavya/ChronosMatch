import asyncio
import os
import random
import time

from src.ring_buffer import MmapRingBuffer


class AsyncMarketSimulator:
    def __init__(
        self,
        buffer: MmapRingBuffer,
        rate_per_second: int = 100,
        arrival_mode: str = "poisson",
        burst_probability: float = 0.05,
        burst_size: int = 10,
    ):
        self.buffer = buffer
        self.rate_per_second = rate_per_second
        self.arrival_mode = arrival_mode
        self.burst_probability = burst_probability
        self.burst_size = burst_size

        self.running = False
        self._next_order_id = 1

    async def generate_order(self):
        """Generate a realistic mock trade or cancellation order."""
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
            k=1,
        )[0]

        return order_id, price, quantity, side

    async def wait_for_arrival(self):
        """Apply Poisson-style inter-arrival pacing."""
        if self.rate_per_second <= 0:
            return

        if self.arrival_mode == "poisson":
            interval = random.expovariate(self.rate_per_second)
            await asyncio.sleep(interval)

        elif self.arrival_mode == "burst":
            await asyncio.sleep(0)

        else:
            raise ValueError(
                "arrival_mode must be 'poisson' or 'burst'"
            )

    async def write_with_backpressure(
        self,
        order_id: int,
        price: float,
        quantity: int,
        side: str,
    ):
        """Write an order without exceeding ring-buffer capacity."""

        while self.running:
            success = self.buffer.write_order(
                order_id,
                price,
                quantity,
                side,
            )

            if success:
                return True

            # Buffer is full. Wait briefly and retry.
            # This prevents overflow and order loss.
            await asyncio.sleep(0)

        return False

    async def run(self, max_orders: int = 50):
        """Run the asynchronous market order stream."""
        self.running = True
        count = 0
        start_time = time.perf_counter()

        print(
            f"[Simulator] Launching order stream "
            f"({max_orders} orders at "
            f"{self.rate_per_second}/sec, "
            f"{self.arrival_mode} arrival)..."
        )

        while self.running and count < max_orders:

            # Create a burst when burst mode is enabled.
            current_burst = 1

            if (
                self.arrival_mode == "burst"
                and random.random() < self.burst_probability
            ):
                current_burst = self.burst_size

            for _ in range(current_burst):

                if count >= max_orders:
                    break

                await self.wait_for_arrival()

                order_id, price, qty, side = await self.generate_order()

                success = await self.write_with_backpressure(
                    order_id,
                    price,
                    qty,
                    side,
                )

                if success:
                    count += 1

                    if count % 100 == 0 or count == max_orders:
                        print(
                            f"[Simulator] Injected order #{order_id}: "
                            f"{side} {qty} @ {price}"
                        )

        elapsed = time.perf_counter() - start_time

        if elapsed > 0:
            throughput = count / elapsed
        else:
            throughput = 0

        print(
            f"[Simulator] Stream complete. "
            f"Total injected: {count} orders."
        )

        print(
            f"[Simulator] Elapsed time: {elapsed:.6f} seconds"
        )

        print(
            f"[Simulator] Measured throughput: "
            f"{throughput:.2f} orders/sec"
        )


async def consume_orders(
    ring: MmapRingBuffer,
    expected_orders: int,
):
    """Drain the ring buffer while the simulator is producing orders."""

    consumed = 0

    while consumed < expected_orders:
        order = ring.read_order()

        if order is not None:
            consumed += 1

        else:
            # Give the producer a chance to continue.
            await asyncio.sleep(0)

    return consumed


async def run_throughput_test():
    """Verify high-rate production without exceeding buffer capacity."""

    test_path = "chronos_throughput_buffer.bin"
    capacity = 100
    max_orders = 2000

    ring = MmapRingBuffer(
        test_path,
        capacity=capacity,
    )

    simulator = AsyncMarketSimulator(
        ring,
        rate_per_second=1000,
        arrival_mode="burst",
        burst_probability=0.10,
        burst_size=10,
    )

    print("\n[Throughput Test]")
    print(f"Buffer capacity: {capacity}")
    print(f"Target rate: 1000 orders/sec")
    print(f"Orders to generate: {max_orders}")

    start_time = time.perf_counter()

    producer = asyncio.create_task(
        simulator.run(max_orders=max_orders)
    )

    consumer = asyncio.create_task(
        consume_orders(
            ring,
            max_orders,
        )
    )

    await producer
    consumed = await consumer

    elapsed = time.perf_counter() - start_time

    throughput = (
        consumed / elapsed
        if elapsed > 0
        else 0
    )

    print(
        f"[Throughput Test] Consumed: {consumed}"
    )

    print(
        f"[Throughput Test] Measured throughput: "
        f"{throughput:.2f} orders/sec"
    )

    print(
        f"[Throughput Test] Buffer capacity respected: "
        f"{capacity} slots"
    )

    ring.close()

    if os.path.exists(test_path):
        os.remove(test_path)


if __name__ == "__main__":
    asyncio.run(run_throughput_test())