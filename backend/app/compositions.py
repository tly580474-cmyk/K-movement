from __future__ import annotations

from threading import RLock

from .music import generate_composition
from .repository import MarketRepository
from .schemas import Composition, CompositionCreateRequest


class CompositionNotFoundError(LookupError):
    pass


class CompositionStore:
    def __init__(self) -> None:
        self._items: dict[str, Composition] = {}
        self._lock = RLock()

    def create(self, request: CompositionCreateRequest, repository: MarketRepository) -> Composition:
        series = repository.get_candles(request.asset_id, request.start_date, request.end_date)
        composition = generate_composition(request, series)
        with self._lock:
            self._items[composition.id] = composition
        return composition

    def get(self, composition_id: str) -> Composition:
        with self._lock:
            composition = self._items.get(composition_id)
        if composition is None:
            raise CompositionNotFoundError(f"未找到乐章：{composition_id}")
        return composition


composition_store = CompositionStore()
