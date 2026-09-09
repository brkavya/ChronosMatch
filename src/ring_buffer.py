import mmap
import os
import struct
from src.order_types import ORDER_SIZE, pack_order, unpack_order

# Ring Buffer Header:
#   I = write_index (4 bytes)
#   I = read_index  (4 bytes)
HEADER_FORMAT = "<II"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


class MmapRingBuffer:
    def __init__(self, filepath: str, capacity: int = 1000):
        self.filepath = filepath
        self.capacity = capacity
        # Total byte size = 8 bytes header + (capacity * 21 bytes per order)
        self.total_size = HEADER_SIZE + (self.capacity * ORDER_SIZE)

        # Pre-allocate binary backing file if not present
        if not os.path.exists(self.filepath) or os.path.getsize(self.filepath) != self.total_size:
            with open(self.filepath, "wb") as f:
                f.write(b"\x00" * self.total_size)

        self.file = open(self.filepath, "r+b")
        self.mm = mmap.mmap(self.file.fileno(), self.total_size)

    def _get_indices(self) -> tuple[int, int]:
        return struct.unpack_from(HEADER_FORMAT, self.mm, 0)

    def _set_indices(self, write_idx: int, read_idx: int) -> None:
        struct.pack_into(HEADER_FORMAT, self.mm, 0, write_idx, read_idx)

    def write_order(self, order_id: int, price: float, quantity: int, side: str) -> bool:
        write_idx, read_idx = self._get_indices()
        # Full condition: buffer is saturated
        if (write_idx - read_idx) >= self.capacity:
            return False

        slot = write_idx % self.capacity
        offset = HEADER_SIZE + (slot * ORDER_SIZE)
        packed_bytes = pack_order(order_id, price, quantity, side)

        self.mm[offset : offset + ORDER_SIZE] = packed_bytes
        self._set_indices(write_idx + 1, read_idx)
        return True

    def read_order(self) -> tuple | None:
        write_idx, read_idx = self._get_indices()
        # Empty condition: read pointer caught up with write pointer
        if read_idx >= write_idx:
            return None

        slot = read_idx % self.capacity
        offset = HEADER_SIZE + (slot * ORDER_SIZE)
        packed_bytes = self.mm[offset : offset + ORDER_SIZE]

        self._set_indices(write_idx, read_idx + 1)
        return unpack_order(packed_bytes)

    def close(self):
        self.mm.close()
        self.file.close()


if __name__ == "__main__":
    test_buffer_path = "chronos_test_buffer.bin"
    rb = MmapRingBuffer(test_buffer_path, capacity=10)

    # Test writing orders into the shared memory buffer
    print("Writing 3 sample orders to mmap ring buffer...")
    rb.write_order(101, 2450.50, 10, "B")
    rb.write_order(102, 2451.00, 25, "S")
    rb.write_order(103, 2449.75, 100, "B")

    # Test reading back directly
    print("\nReading orders out of buffer:")
    while True:
        order = rb.read_order()
        if order is None:
            break
        print(f"Consumed order: {order}")

    rb.close()
    if os.path.exists(test_buffer_path):
        os.remove(test_buffer_path)
    print("\nRing buffer zero-copy test completed cleanly.")