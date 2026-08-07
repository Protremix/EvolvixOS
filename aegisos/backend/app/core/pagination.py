"""
Pagination Utility — Phase 50 Security Fix

Standardized pagination for all list endpoints.
Prevents large response payloads from impacting performance.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PaginationParams:
    page: int = 1
    page_size: int = 50
    max_page_size: int = 500

    def __post_init__(self):
        if self.page < 1:
            self.page = 1
        if self.page_size < 1:
            self.page_size = 1
        if self.page_size > self.max_page_size:
            self.page_size = self.max_page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


@dataclass
class PaginatedResponse:
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int
    has_more: bool

    def to_dict(self) -> dict:
        return {
            "items": self.items,
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages,
            "has_more": self.has_more,
        }


def paginate(items: list, page: int = 1, page_size: int = 50,
             max_page_size: int = 500) -> PaginatedResponse:
    """Paginate a list of items."""
    params = PaginationParams(page=page, page_size=page_size, max_page_size=max_page_size)
    total = len(items)
    total_pages = (total + params.page_size - 1) // params.page_size
    paginated = items[params.offset:params.offset + params.page_size]
    has_more = params.offset + params.page_size < total

    return PaginatedResponse(
        items=paginated, total=total, page=params.page,
        page_size=params.page_size, total_pages=total_pages,
        has_more=has_more,
    )
