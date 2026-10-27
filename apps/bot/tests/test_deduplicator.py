import pytest

from services.deduplicator import MessageDeduplicator


@pytest.mark.asyncio
async def test_deduplicator_detects_duplicates():
    dedup = MessageDeduplicator(max_size=100)
    # Birinchi marta: duplicate emas
    assert await dedup.is_duplicate(1001, 55) is False
    # Ikkinchi marta: aynan shu xabar duplicate
    assert await dedup.is_duplicate(1001, 55) is True

    # Boshqa xabar: duplicate emas
    assert await dedup.is_duplicate(1001, 56) is False
    # Boshqa chat: duplicate emas
    assert await dedup.is_duplicate(1002, 55) is False


@pytest.mark.asyncio
async def test_deduplicator_eviction():
    dedup = MessageDeduplicator(max_size=3)
    await dedup.is_duplicate(1, 101)
    await dedup.is_duplicate(1, 102)
    await dedup.is_duplicate(1, 103)
    assert dedup.count() == 3

    # To'rtinchi qo'shilganda eng eskisi (1, 101) chiqib ketadi
    await dedup.is_duplicate(1, 104)
    assert dedup.count() == 3

    # 101 yana yangi hisoblanadi (chunki keshdan o'chgan)
    assert await dedup.is_duplicate(1, 101) is False
