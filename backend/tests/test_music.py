from datetime import date, timedelta

import pytest

from app.midi import composition_to_midi
from app.music import generate_composition
from app.schemas import (
    AssetSummary,
    Candle,
    CandleSeriesResponse,
    CompositionCreateRequest,
    GenerationSettings,
    IndicatorPoint,
    MarketAnalysis,
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
    melody = first.tracks[0].notes
    linked_candles = {note.candle_index for note in melody}
    assert linked_candles < set(range(16))
    assert 0.7 <= len(linked_candles) / 16 <= 0.9
    assert all(48 <= note.midi <= 88 for note in melody)
    assert all(note.midi % 12 in {0, 2, 4, 7, 9} for note in first.tracks[0].notes)
    assert all(32 <= note.velocity <= 122 for note in melody)
    assert all(abs(left.midi - right.midi) <= 12 for left, right in zip(melody, melody[1:]))
    assert [track.id for track in first.tracks] == ["melody", "harmony", "bass"]
    assert first.total_bars == 16
    assert len(first.tracks[1].notes) == first.total_bars * 3
    assert len(first.tracks[2].notes) == first.total_bars * 2
    assert first.tracks[1].notes[0].start_seconds == first.tracks[1].notes[1].start_seconds
    assert any(right.start_seconds > left.start_seconds + left.duration_seconds for left, right in zip(melody, melody[1:]))
    assert first.motifs[0].start_seconds == 0
    assert [motif.label for motif in first.motifs] == ["A", "A′", "B", "A″"]
    assert first.duration_seconds > 0


def test_harmony_is_bar_aligned_and_each_section_has_a_dominant_tonic_cadence() -> None:
    composition = generate_composition(_request(), _series())
    harmony = composition.tracks[1].notes
    seconds_per_bar = 4 * 60 / composition.settings.bpm
    starts = sorted({note.start_seconds for note in harmony})
    roots = [next(note.midi for note in harmony if note.start_seconds == start) for start in starts]

    assert starts == pytest.approx([bar * seconds_per_bar for bar in range(composition.total_bars)])
    assert all(note.duration_seconds == pytest.approx(seconds_per_bar) for note in harmony)
    section_bars = composition.total_bars // 4
    for section in range(4):
        assert roots[(section + 1) * section_bars - 2] % 12 == 7
        assert roots[(section + 1) * section_bars - 1] % 12 == 0


def test_form_uses_contrasting_b_section_and_long_phrase_endings() -> None:
    composition = generate_composition(_request(), _series())
    melody = composition.tracks[0].notes
    section_seconds = composition.duration_seconds / 4
    a_pitches = [note.midi for note in melody if note.start_seconds < section_seconds]
    b_pitches = [note.midi for note in melody if section_seconds * 2 <= note.start_seconds < section_seconds * 3]
    cadence_notes = [
        note for note in melody
        if any(abs(note.start_seconds - (section * section_seconds - 2 * 60 / composition.settings.bpm)) < 1e-6 for section in range(1, 5))
    ]

    assert sum(b_pitches) / len(b_pitches) > sum(a_pitches) / len(a_pitches) + 4
    assert len(cadence_notes) == 4
    assert all(note.duration_seconds >= 2 * 60 / composition.settings.bpm for note in cadence_notes)


def test_market_trend_selects_scale_quality() -> None:
    bearish_series = _series().model_copy(update={"analysis": MarketAnalysis(trend_state="bearish")})
    bullish_series = _series().model_copy(update={"analysis": MarketAnalysis(trend_state="bullish")})
    request = _request()

    assert generate_composition(request, bearish_series).settings.scale == "minor-pentatonic"
    assert generate_composition(request, bullish_series).settings.scale == "major-pentatonic"


def test_midi_is_a_valid_multitrack_file() -> None:
    payload = composition_to_midi(generate_composition(_request(), _series()))
    assert payload[:4] == b"MThd"
    assert payload[8:10] == b"\x00\x01"
    assert payload[10:12] == b"\x00\x04"
    assert payload.count(b"MTrk") == 4
    assert payload.endswith(b"\xff\x2f\x00")


@pytest.mark.parametrize(
    "style",
    ["jazz-lounge", "cinematic-epic", "chinese-folk", "ambient-minimal", "pop-rock"],
)
def test_extended_styles_generate_valid_arrangements(style: str) -> None:
    request = _request().model_copy(
        update={"settings": _request().settings.model_copy(update={"style": style})}
    )
    composition = generate_composition(request, _series())
    assert composition.settings.style == style
    assert len(composition.tracks) >= 3
    assert composition.duration_seconds > 0


def test_extended_styles_have_distinct_musical_behavior() -> None:
    base = _request()
    jazz = generate_composition(
        base.model_copy(update={"settings": base.settings.model_copy(update={"style": "jazz-lounge"})}),
        _series(),
    )
    ambient = generate_composition(
        base.model_copy(update={"settings": base.settings.model_copy(update={"style": "ambient-minimal"})}),
        _series(),
    )
    rock = generate_composition(
        base.model_copy(update={"settings": base.settings.model_copy(update={"style": "pop-rock"})}),
        _series(),
    )
    chinese = generate_composition(
        base.model_copy(update={"settings": base.settings.model_copy(update={"style": "chinese-folk"})}),
        _series(),
    )

    assert len(jazz.tracks[1].notes) > len(ambient.tracks[1].notes)
    assert len(ambient.tracks[0].notes) < len(rock.tracks[0].notes)
    assert rock.tracks[-1].id == "drums"
    assert len(rock.tracks[-1].notes) > 0
    first_chinese_chord = chinese.tracks[1].notes[:3]
    assert [note.midi - first_chinese_chord[0].midi for note in first_chinese_chord] == [0, 7, 12]
    rock_midi = composition_to_midi(rock)
    assert int.from_bytes(rock_midi[10:12], "big") == 5
    assert b"\x99" in rock_midi
