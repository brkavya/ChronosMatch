import time
from src.order_book import OrderBook


def benchmark_order_book(num_orders=5000):
    book = OrderBook()

    # Pre-populate book with resting sell orders
    for i in range(1, num_orders + 1):
        book.add_order(order_id=i, price=2450.0 + (i * 0.05), quantity=10, side="S")

    # Time incoming taker buy orders
    start_ns = time.perf_counter_ns()
    for i in range(num_orders + 1, num_orders + 501):
        book.add_order(order_id=i, price=2500.0, quantity=5, side="B")
    end_ns = time.perf_counter_ns()

    total_time_ns = end_ns - start_ns
    avg_latency_ns = total_time_ns / 500
    avg_latency_us = avg_latency_ns / 1000

    print("=== Order Matching Engine Performance ===")
    print(f"Total Matches Processed: 500 aggressive orders")
    print(f"Total Execution Time:    {total_time_ns / 1_000_000:.3f} ms")
    print(f"Average Order Latency:   {avg_latency_ns:.0f} ns ({avg_latency_us:.2f} µs)")
    print(f"Book Depth Post-Test:    {book.get_market_depth()}")


if __name__ == "__main__":
    benchmark_order_book()