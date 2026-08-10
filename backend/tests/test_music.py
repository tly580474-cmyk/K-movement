from datetime import date, timedelta

from app.midi import composition_to_midi
from app.music import generate_composition
from app.schemas import (
    AssetSummary,
    Candle,
    CandleSeriesResponse,
    CompositionCreateRequest,
    GenerationSettings,
    IndicatorPoint,
)


def _series() -> CandleSeriesResponse:
    first = date(2026, 1, 1)
    closes = [100, 101, 99, 103, 106, 104, 108, 110, 107, 112, 115, 114, 118, 120, 119, 123]
    candles = [
        Candle(
            date=first + timedelta(days=index),
            open=close - 0.5,
            high=close + 1,
            low=close - 1,
            close=close,
            volume=1_000_000 + index * 80_000,
        )
        for index, close in enumerate(closes)
    ]
    indicators = [
        IndicatorPoint(
            date=candle.date,
            return_pct=0 if index == 0 else (candle.close / candles[index - 1].close - 1) * 100,
            atr14=1.5 + index * 0.08,
            relative_volume20=0.8 + index * 0.05,
        )
        for index, candle in enumerate(candles)
    ]
    asset = AssetSummary(
        asset_id="stock:SH:600519",
        source_id="29",
        market="SH",
        symbol="600519",
        name="贵州茅台",
        asset_type="stock",
        status="active",
        last_data_date=candles[-1].date,
        last_price=closes[-1],
        currency="CNY",
    )
    return CandleSeriesResponse(
        asset=asset,
        requested_start_date=first,
        requested_end_date=candles[-1].date,
        actual_start_date=first,
        actual_end_date=candles[-1].date,
        items=candles,
        indicators=indicators,
    )


def _request() -> CompositionCreateRequest:
    series = _series()
    return CompositionCreateRequest(
        asset_id=series.asset.asset_id,
        start_date=series.requested_start_date,
        end_date=series.requested_end_date,
        settings=GenerationSettings(
            style="orchestral",
            instruments=["piano", "strings", "bass"],
            bpm=96,
            musical_key="C",
            scale="major-pentatonic",
            mood="upward",
            mapping_strength=0.88,
        ),
    )


def test_mapping_is_deterministic_and_preserves_candle_links() -> None:
    request = _request()
    first = generate_composition(request, _series())
    second = generate_composition(request, _series())

    assert first == second
    assert [note.candle_index for note in first.tracks[0].notes] == list(range(16))
    assert all(48 <= note.midi <= 84 for note in first.tracks[0].notes)
    assert all(note.midi % 12 in {0, 2, 4, 7, 9} for note in first.tracks[0].notes)
    assert all(45 <= note.velocity <= 110 for note in first.tracks[0].notes)
    assert all(abs(left.midi - right.midi) <= 5 for left, right in zip(first.tracks[0].notes, first.tracks[0].notes[1:]))
    assert [track.id for track in first.tracks] == ["melody", "harmony", "bass"]
    assert len(first.tracks[1].notes) == 12
    assert len(first.tracks[2].notes) == 8
    assert first.tracks[1].notes[0].start_seconds == first.tracks[1].notes[1].start_seconds
    assert first.tracks[0].notes[1].start_seconds < 60 / request.settings.bpm
    assert first.tracks[0].notes[0].duration_seconds > first.tracks[0].notes[1].start_seconds
    assert first.motifs[0].start_seconds == 0
    assert first.duration_seconds > 0


def test_midi_is_a_valid_multitrack_file() -> None:
    payload = composition_to_midi(generate_composition(_request(), _series()))
    assert payload[:4] == b"MThd"
    assert payload[8:10] == b"\x00\x01"
    assert payload[10:12] == b"\x00\x04"
    assert payload.count(b"MTrk") == 4
    assert payload.endswith(b"\xff\x2f\x00")
