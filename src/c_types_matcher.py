import ctypes
import time


class OrderStruct(ctypes.Structure):
    _fields_ = [
        ("order_id", ctypes.c_uint64),
        ("price", ctypes.c_double),
        ("quantity", ctypes.c_uint32),
        ("side", ctypes.c_char),
    ]


def run_c_memory_benchmark(iterations=100000):
    start = time.perf_counter_ns()
    arr = (OrderStruct * iterations)()
    for i in range(iterations):
        arr[i].order_id = i + 1
        arr[i].price = 2450.50
        arr[i].quantity = 100
        arr[i].side = b"B"
    end = time.perf_counter_ns()

    elapsed_ms = (end - start) / 1_000_000
    ns_per_op = (end - start) / iterations
    print("=== C-Types Memory Allocation Performance ===")
    print(f"Allocated & Initialized: {iterations:,} C structs")
    print(f"Total time:              {elapsed_ms:.2f} ms")
    print(f"Latency per struct:      {ns_per_op:.1f} ns")


if __name__ == "__main__":
    run_c_memory_benchmark()