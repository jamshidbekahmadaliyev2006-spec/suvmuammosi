"""Xabarlarning takroriy kelishidan himoya qilish moduli.

Bir xil Telegram xabari botga qayta kelganda yoki qayta urinish paytida
ikkinchi marotaba backendga yuborilmasligi uchun xotirada eslab qoladi.
"""
import asyncio
from collections import OrderedDict


class MessageDeduplicator:
    def __init__(self, max_size: int = 10000) -> None:
        self.max_size = max_size
        self._seen: OrderedDict[tuple[int, int], bool] = OrderedDict()
        self._lock = asyncio.Lock()

    async def is_duplicate(self, chat_id: int, message_id: int) -> bool:
        """Agar xabar avval ko'rilgan bo'lsa True, aks holda False qaytaradi va bazaga kiritadi."""
        key = (chat_id, message_id)
        async with self._lock:
            if key in self._seen:
                return True
            self._seen[key] = True
            # Agar limitdan oshsa, eng eskisini o'chirish
            if len(self._seen) > self.max_size:
                self._seen.popitem(last=False)
            return False

    async def clear(self) -> None:
        async with self._lock:
            self._seen.clear()

    def count(self) -> int:
        return len(self._seen)
