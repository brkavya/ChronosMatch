import struct

# Binary format:
#   Q = 64-bit unsigned int (order_id) -> 8 bytes
#   d = 64-bit float (price)           -> 8 bytes
#   I = 32-bit unsigned int (quantity)  -> 4 bytes
#   c = char ('B' for Buy, 'S' for Sell)-> 1 byte
# Total size: 21 bytes (packed tightly with '<' little-endian: 21 bytes)
ORDER_FORMAT = "<QdIc"
ORDER_SIZE = struct.calcsize(ORDER_FORMAT)


def pack_order(order_id: int, price: float, quantity: int, side: str) -> bytes:
    """Packs an order into fixed-width binary bytes."""
    return struct.pack(ORDER_FORMAT, order_id, price, quantity, side.encode("ascii"))


def unpack_order(data: bytes) -> tuple:
    """Unpacks binary bytes into (order_id, price, quantity, side)."""
    order_id, price, quantity, side_bytes = struct.unpack(ORDER_FORMAT, data)
    return order_id, price, quantity, side_bytes.decode("ascii")


if __name__ == "__main__":
    print(f"Order packet size: {ORDER_SIZE} bytes")
    sample = pack_order(1001, 150.25, 50, "B")
    print(f"Packed bytes: {sample}")
    unpacked = unpack_order(sample)
    print(f"Unpacked order: {unpacked}")