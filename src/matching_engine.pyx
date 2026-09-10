# cython: language_level=3
# distutils: language = c

def match_order_c(
    unsigned long long order_id,
    double price,
    unsigned int quantity,
    char side,
    list resting_prices,
    dict resting_book
):
    """
    Cython-accelerated order matching routine using C-level data types.
    """
    cdef unsigned int remaining_qty = quantity
    cdef unsigned int matched_qty = 0
    cdef double best_price
    cdef list trades = []
    cdef list queue
    cdef list maker_order

    if side == b'B'[0]:
        while remaining_qty > 0 and len(resting_prices) > 0 and resting_prices[0] <= price:
            best_price = resting_prices[0]
            queue = resting_book[best_price]

            while remaining_qty > 0 and len(queue) > 0:
                maker_order = queue[0]
                matched_qty = remaining_qty if remaining_qty < maker_order[1] else maker_order[1]

                trades.append((maker_order[0], order_id, best_price, matched_qty))
                remaining_qty -= matched_qty
                maker_order[1] -= matched_qty

                if maker_order[1] == 0:
                    queue.pop(0)

            if len(queue) == 0:
                del resting_book[best_price]
                resting_prices.pop(0)

    elif side == b'S'[0]:
        while remaining_qty > 0 and len(resting_prices) > 0 and resting_prices[0] >= price:
            best_price = resting_prices[0]
            queue = resting_book[best_price]

            while remaining_qty > 0 and len(queue) > 0:
                maker_order = queue[0]
                matched_qty = remaining_qty if remaining_qty < maker_order[1] else maker_order[1]

                trades.append((maker_order[0], order_id, best_price, matched_qty))
                remaining_qty -= matched_qty
                maker_order[1] -= matched_qty

                if maker_order[1] == 0:
                    queue.pop(0)

            if len(queue) == 0:
                del resting_book[best_price]
                resting_prices.pop(0)

    return trades, remaining_qty