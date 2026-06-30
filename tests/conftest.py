from __future__ import annotations

from collections.abc import Iterable

import pytest


def make_serials(prefix: str, count: int, start: int = 1, width: int = 8) -> list[str]:
    return [f"{prefix}{value:0{width}d}" for value in range(start, start + count)]


@pytest.fixture
def line_pages():
    def factory(lines: Iterable[str], page: int = 1) -> list[int]:
        return [page for _ in lines]

    return factory
