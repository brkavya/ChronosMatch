# ChronosMatch 
# ChronosMatch

A zero-copy, low-latency financial order matching engine built with Python, asynchronous I/O, shared memory (mmap), and SQLite persistence.

---

## Key Architectural Components

* **Zero-Copy IPC (`src/ring_buffer.py`)**: Circular ring buffer mapped via `mmap` for cross-process memory transmission with minimal copy overhead.
* **Compact Binary Serialization (`src/order_types.py`)**: Pack/unpack binary order structs into fixed-width binary packets using Python's `struct`.
* **High-Rate Asynchronous Simulator (`src/market_simulator.py`)**: Poisson and burst order arrival simulation running on `asyncio`.
* **Price-Time Priority Limit Order Book (`src/order_book.py`)**: FIFO matching engine implementing resting order books and aggressive taker order matching.
* **Trade Persistence (`src/trade_db.py`)**: Batch trade logging directly into SQLite with single-transaction commits and indexed lookups.
* **Integrated Pipeline Orchestrator (`src/engine.py`)**: End-to-end event-driven loop tying ingestion, matching, and database storage together.

---

## Verified Benchmarks

* **C-Types Struct Allocation:** ~475.6 ns per struct
* **Order Matching Latency:** ~5,606 ns (5.61 µs) average execution latency per order
* **Asynchronous Ingestion Throughput:** 60+ orders/sec sustained throughput across tests

---

## Running the Engine

```powershell
# Run unit & throughput tests
py -m pytest tests/ -v

# Run the end-to-end matching pipeline
py -m src.engine