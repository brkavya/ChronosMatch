import pytest

from src.market_simulator import AsyncMarketSimulator
from src.ring_buffer import MmapRingBuffer


def create_buffer():
    return MmapRingBuffer(
        "test_simulator_buffer.bin",
        capacity=10,
    )


@pytest.mark.asyncio
async def test_generate_order_contains_valid_values():
    ring = create_buffer()

    simulator = AsyncMarketSimulator(ring)

    order = await simulator.generate_order()

    order_id, price, quantity, side = order

    assert order_id == 1
    assert price > 0
    assert quantity in [5, 10, 25, 50, 100]
    assert side in ["B", "S", "C"]

    ring.close()


@pytest.mark.asyncio
async def test_order_ids_are_sequential():
    ring = create_buffer()

    simulator = AsyncMarketSimulator(ring)

    order1 = await simulator.generate_order()
    order2 = await simulator.generate_order()
    order3 = await simulator.generate_order()

    assert order1[0] == 1
    assert order2[0] == 2
    assert order3[0] == 3

    ring.close()


@pytest.mark.asyncio
async def test_invalid_arrival_mode():
    ring = create_buffer()

    simulator = AsyncMarketSimulator(
        ring,
        arrival_mode="invalid",
    )

    with pytest.raises(ValueError):
        await simulator.wait_for_arrival()

    ring.close()


@pytest.mark.asyncio
async def test_burst_mode_configuration():
    ring = create_buffer()

    simulator = AsyncMarketSimulator(
        ring,
        rate_per_second=1000,
        arrival_mode="burst",
        burst_probability=1.0,
        burst_size=5,
    )

    assert simulator.rate_per_second == 1000
    assert simulator.arrival_mode == "burst"
    assert simulator.burst_probability == 1.0
    assert simulator.burst_size == 5

    await simulator.wait_for_arrival()

    ring.close()


@pytest.mark.asyncio
async def test_order_can_be_written_to_ring_buffer():
    ring = create_buffer()

    simulator = AsyncMarketSimulator(ring)

    order = await simulator.generate_order()

    success = ring.write_order(*order)

    assert success is True

    stored_order = ring.read_order()

    assert stored_order == order

    ring.close()