import os
from datetime import date

import pytest

from app.repository import get_market_repository
from app.midi import composition_to_midi
from app.music import generate_composition
from app.schemas import CompositionCreateRequest, GenerationSettings


pytestmark = pytest.mark.integration


def _require_database() -> None:
    if not os.getenv("MYSQL_PASSWORD"):
        pytest.skip("未提供 MYSQL_PASSWORD，跳过真实数据库集成测试")


def test_real_database_catalog_and_ranges() -> None:
    _require_database()
    repository = get_market_repository()

    assert repository.ping().startswith("9.")

    collision = repository.search_assets(query="000001", limit=10)
    collision_ids = {asset.asset_id for asset in collision.items}
    assert "stock:SZ:000001" in collision_ids
    assert "index:dataset:7c5031c8-eccd-4f21-bd5a-66a354d46231" in collision_ids

    indices = repository.search_assets(query="中证2000", asset_type="index", limit=5)
    assert indices.items[0].symbol == "932000"

    stock = repository.get_candles(
        "stock:SH:600519",
        date(2026, 8, 1),
        date(2026, 8, 7),
    )
    assert len(stock.items) == 5
    assert len(stock.indicators) == len(stock.items)
    assert stock.analysis is not None
    assert stock.analysis.trend_state in {"bullish", "bearish", "sideways"}
    assert stock.analysis.latest_rsi14 is not None
    assert stock.items[-1].close == pytest.approx(1309.22)

    composition = generate_composition(
        CompositionCreateRequest(
            asset_id="stock:SH:600519",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 7),
            settings=GenerationSettings(),
        ),
        stock,
    )
    assert composition.total_bars == 16
    assert [motif.label for motif in composition.motifs] == ["A", "A′", "B", "A″"]
    assert {note.candle_index for note in composition.tracks[0].notes} <= set(range(len(stock.items)))
    seconds_per_bar = 4 * 60 / composition.settings.bpm
    harmony_bars = {int(note.start_seconds // seconds_per_bar) for note in composition.tracks[1].notes}
    assert 0 < len(harmony_bars) <= composition.total_bars
    assert composition_to_midi(composition).startswith(b"MThd")

    index = repository.get_candles(
        "index:dataset:7de97d1e-3d0c-4102-9fd8-c85126568dec",
        date(2026, 7, 20),
        date(2026, 8, 7),
    )
    assert index.actual_end_date == date(2026, 8, 5)
    assert index.warnings == ["行情数据仅更新至 2026-08-05"]
