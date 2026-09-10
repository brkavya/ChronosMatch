from collections import deque
import bisect


class OrderBook:
    def __init__(self):
        # bids: descending price order (highest buy price first)
        # asks: ascending price order (lowest sell price first)
        self.bids = {}  # price -> deque of [order_id, quantity]
        self.asks = {}  # price -> deque of [order_id, quantity]
        self.bid_prices = []  # sorted descending
        self.ask_prices = []  # sorted ascending

    def add_order(self, order_id: int, price: float, quantity: int, side: str) -> list:
        """
        Processes an incoming order against the opposite book.
        Executes matches via Price-Time Priority and rests any unfilled remainder.
        Returns a list of executed trades: [(maker_id, taker_id, match_price, match_qty)]
        """
        trades = []
        remaining_qty = quantity

        if side == "B":
            # Match against existing Asks (sellers offering <= buy price)
            while remaining_qty > 0 and self.ask_prices and self.ask_prices[0] <= price:
                best_ask_price = self.ask_prices[0]
                queue = self.asks[best_ask_price]

                while remaining_qty > 0 and queue:
                    maker_order = queue[0]
                    maker_id, maker_qty = maker_order[0], maker_order[1]
                    matched_qty = min(remaining_qty, maker_qty)

                    trades.append((maker_id, order_id, best_ask_price, matched_qty))
                    remaining_qty -= matched_qty
                    maker_order[1] -= matched_qty

                    if maker_order[1] == 0:
                        queue.popleft()

                if not queue:
                    del self.asks[best_ask_price]
                    self.ask_prices.pop(0)

            # If order is not completely filled, rest the remaining quantity on Bid book
            if remaining_qty > 0:
                if price not in self.bids:
                    self.bids[price] = deque()
                    # Keep bid_prices sorted descending
                    idx = bisect.bisect_left([-p for p in self.bid_prices], -price)
                    self.bid_prices.insert(idx, price)
                self.bids[price].append([order_id, remaining_qty])

        elif side == "S":
            # Match against existing Bids (buyers offering >= sell price)
            while remaining_qty > 0 and self.bid_prices and self.bid_prices[0] >= price:
                best_bid_price = self.bid_prices[0]
                queue = self.bids[best_bid_price]

                while remaining_qty > 0 and queue:
                    maker_order = queue[0]
                    maker_id, maker_qty = maker_order[0], maker_order[1]
                    matched_qty = min(remaining_qty, maker_qty)

                    trades.append((maker_id, order_id, best_bid_price, matched_qty))
                    remaining_qty -= matched_qty
                    maker_order[1] -= matched_qty

                    if maker_order[1] == 0:
                        queue.popleft()

                if not queue:
                    del self.bids[best_bid_price]
                    self.bid_prices.pop(0)

            # Rest remaining quantity on Ask book
            if remaining_qty > 0:
                if price not in self.asks:
                    self.asks[price] = deque()
                    # Keep ask_prices sorted ascending
                    idx = bisect.bisect_left(self.ask_prices, price)
                    self.ask_prices.insert(idx, price)
                self.asks[price].append([order_id, remaining_qty])

        return trades

    def get_market_depth(self) -> dict:
        """Returns best bid, best ask, and spread for the dashboard."""
        best_bid = self.bid_prices[0] if self.bid_prices else None
        best_ask = self.ask_prices[0] if self.ask_prices else None
        spread = round(best_ask - best_bid, 2) if (best_bid and best_ask) else None
        return {
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": spread,
            "total_bid_levels": len(self.bid_prices),
            "total_ask_levels": len(self.ask_prices),
        }


if __name__ == "__main__":
    book = OrderBook()

    print("--- Placing resting Sell orders (Asks) ---")
    book.add_order(order_id=1, price=102.0, quantity=10, side="S")
    book.add_order(order_id=2, price=101.0, quantity=15, side="S")
    book.add_order(order_id=3, price=101.0, quantity=20, side="S")

    depth = book.get_market_depth()
    print(f"Market Depth after Asks: {depth}")

    print("\n--- Placing aggressive Buy order (Taker) ---")
    # Buy 25 shares up to 101.50 -> Should match completely against orders #2 and #3 at 101.0
    trades = book.add_order(order_id=4, price=101.50, quantity=25, side="B")

    for trade in trades:
        maker_id, taker_id, match_price, match_qty = trade
        print(f"Trade Executed: Maker #{maker_id} matched with Taker #{taker_id} -> {match_qty} shares @ ${match_price}")

    print(f"\nMarket Depth after Matching: {book.get_market_depth()}")