import asyncio
import os
import time

import pytest

from src.market_simulator import AsyncMarketSimulator, consume_orders
from src.ring_buffer import MmapRingBuffer


@pytest.mark.asyncio
async def test_high_throughput_with_ring_buffer():
    test_path = "test_throughput_buffer.bin"
    capacity = 100
    total_orders = 2000

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

    start_time = time.perf_counter()

    producer = asyncio.create_task(
        simulator.run(max_orders=total_orders)
    )

    consumer = asyncio.create_task(
        consume_orders(
            ring,
            total_orders,
        )
    )

    await producer
    consumed = await consumer

    elapsed = time.perf_counter() - start_time

    throughput = consumed / elapsed

    assert consumed == total_orders
    assert throughput >= 1000

    ring.close()

    if os.path.exists(test_path):
        os.remove(test_path)