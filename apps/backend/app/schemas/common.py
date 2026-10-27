from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, StringConstraints, computed_field

T = TypeVar("T")

Str120 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Str200 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int

    @computed_field  # type: ignore[misc]
    @property
    def total_pages(self) -> int:
        return max(1, (self.total + self.page_size - 1) // self.page_size) if self.page_size > 0 else 1
