from datetime import date, timedelta

import pytest

from app.midi import composition_to_midi
from app.music import _swing_beat, generate_composition
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
    assert all(note.midi % 12 in {0, 2, 4, 7, 9} for note in melody if note.motif_id != "motif-3")
    assert all(note.midi % 12 in {0, 3, 5, 7, 10} for note in melody if note.motif_id == "motif-3")
    assert all(32 <= note.velocity <= 122 for note in melody)
    assert all(abs(left.midi - right.midi) <= 12 for left, right in zip(melody, melody[1:]))
    assert all(abs(left.velocity - right.velocity) <= 12 for left, right in zip(melody, melody[1:]))
    assert [track.id for track in first.tracks] == ["melody", "harmony", "bass"]
    assert first.total_bars == 16
    assert len(first.tracks[1].notes) > first.total_bars * 3
    assert len(first.tracks[2].notes) >= first.total_bars
    assert first.tracks[1].notes[0].start_seconds == first.tracks[1].notes[1].start_seconds
    assert any(left.start_seconds + left.duration_seconds >= right.start_seconds for left, right in zip(melody, melody[1:]))
    assert first.motifs[0].start_seconds == 0
    assert [motif.label for motif in first.motifs] == ["A", "A′", "B", "A″"]
    assert first.duration_seconds > 0


def test_harmony_uses_voice_leading_rhythm_and_hierarchical_cadences() -> None:
    composition = generate_composition(_request(), _series())
    harmony = composition.tracks[1].notes
    seconds_per_beat = 60 / composition.settings.bpm
    seconds_per_bar = 4 * seconds_per_beat
    assert {round((note.start_seconds / seconds_per_beat) % 4, 6) for note in harmony} <= {0.0, 1.0, 2.0, 3.0}
    assert all(
        note.duration_seconds < seconds_per_bar or note.start_seconds == pytest.approx(composition.duration_seconds - seconds_per_bar)
        for note in harmony
    )
    voicings = []
    for bar in range(composition.total_bars):
        voicing = sorted(note.midi for note in harmony if abs(note.start_seconds - bar * seconds_per_bar) < 1e-6)
        if voicing:
            voicings.append(voicing)
    assert all(sum(abs(left - right) for left, right in zip(first, second)) <= 6 for first, second in zip(voicings, voicings[1:]))

    section_bars = composition.total_bars // 4
    cadence_pitch_classes = []
    for section in range(4):
        bar_start = ((section + 1) * section_bars - 1) * seconds_per_bar
        cadence_pitch_classes.append({note.midi % 12 for note in harmony if abs(note.start_seconds - bar_start) < 1e-6})
    assert cadence_pitch_classes == [{2, 7, 11}, {2, 7, 11}, {0, 3, 8}, {0, 4, 7}]
    b_dominant_start = (section_bars * 3 - 2) * seconds_per_bar
    assert {note.midi % 12 for note in harmony if abs(note.start_seconds - b_dominant_start) < 1e-6} == {2, 7, 11}


def test_form_uses_contrasting_b_section_and_long_phrase_endings() -> None:
    composition = generate_composition(_request(), _series())
    melody = composition.tracks[0].notes
    section_seconds = composition.duration_seconds / 4
    a_pitches = [note.midi for note in melody if note.start_seconds < section_seconds]
    b_pitches = [note.midi for note in melody if section_seconds * 2 <= note.start_seconds < section_seconds * 3]
    cadence_starts = [section_seconds - 2 * 60 / composition.settings.bpm, section_seconds * 2 - 2 * 60 / composition.settings.bpm, section_seconds * 3 - 2 * 60 / composition.settings.bpm, composition.duration_seconds - 4 * 60 / composition.settings.bpm]
    cadence_notes = [next(note for note in melody if abs(note.start_seconds - start) < 1e-6) for start in cadence_starts]

    assert sum(b_pitches) / len(b_pitches) > sum(a_pitches) / len(a_pitches) + 4
    harmony = composition.tracks[1].notes
    a_harmony_onsets = {note.start_seconds for note in harmony if note.motif_id == "motif-1"}
    b_harmony_onsets = {note.start_seconds for note in harmony if note.motif_id == "motif-3"}
    assert len(b_harmony_onsets) > len(a_harmony_onsets)
    seconds_per_beat = 60 / composition.settings.bpm
    assert [note.duration_seconds for note in cadence_notes] == pytest.approx([1.25 * seconds_per_beat, 1.25 * seconds_per_beat, 1.5 * seconds_per_beat, 4 * seconds_per_beat])

    a_theme = [note.midi for note in melody if note.motif_id == "motif-1"][:8]
    return_start = composition.motifs[3].start_seconds
    returned_theme = [note.midi for note in melody if note.motif_id == "motif-4" and note.start_seconds >= return_start][:8]
    assert returned_theme[:len(a_theme)] == a_theme
    assert any(note.motif_id == "motif-2" and note.start_seconds < composition.motifs[1].start_seconds for note in melody)
    assert any(note.motif_id == "motif-4" and note.start_seconds < composition.motifs[3].start_seconds for note in melody)


def test_quiet_bars_silence_melody_harmony_and_bass_together() -> None:
    composition = generate_composition(_request(), _series())
    melody, harmony, bass = (track.notes for track in composition.tracks[:3])
    seconds_per_bar = 4 * 60 / composition.settings.bpm
    silent_harmony_bars = [
        bar for bar in range(composition.total_bars)
        if not any(bar * seconds_per_bar <= note.start_seconds < (bar + 1) * seconds_per_bar for note in harmony)
    ]
    assert silent_harmony_bars
    for bar in silent_harmony_bars:
        assert not any(bar * seconds_per_bar <= note.start_seconds < (bar + 1) * seconds_per_bar for note in melody)
        assert not any(bar * seconds_per_bar <= note.start_seconds < (bar + 1) * seconds_per_bar for note in bass)
    for bar in set(range(composition.total_bars)) - set(silent_harmony_bars):
        assert any(bar * seconds_per_bar <= note.start_seconds < (bar + 1) * seconds_per_bar for note in melody)


def test_jazz_swing_and_style_specific_bass_patterns() -> None:
    base = _request()
    jazz = generate_composition(base.model_copy(update={"settings": base.settings.model_copy(update={"style": "jazz-lounge"})}), _series())
    ambient = generate_composition(base.model_copy(update={"settings": base.settings.model_copy(update={"style": "ambient-minimal"})}), _series())
    rock = generate_composition(base.model_copy(update={"settings": base.settings.model_copy(update={"style": "pop-rock"})}), _series())
    seconds_per_beat = 60 / jazz.settings.bpm
    jazz_beats = [round(note.start_seconds / seconds_per_beat, 2) for note in jazz.tracks[1].notes]

    assert any(abs(beat % 1 - 0.64) < 1e-6 for beat in jazz_beats)
    assert _swing_beat(0.25, "jazz-lounge") == pytest.approx(0.32)
    assert _swing_beat(0.75, "jazz-lounge") == pytest.approx(0.82)
    assert len(jazz.tracks[2].notes) > len(ambient.tracks[2].notes)
    assert len(rock.tracks[2].notes) == len(jazz.tracks[2].notes)
    assert len({note.midi for note in jazz.tracks[2].notes}) >= 4
    jazz_voicings = []
    seconds_per_bar = 4 * seconds_per_beat
    for bar in range(jazz.total_bars):
        bar_notes = [note for note in jazz.tracks[1].notes if bar * seconds_per_bar <= note.start_seconds < (bar + 1) * seconds_per_bar]
        if bar_notes:
            first_start = min(note.start_seconds for note in bar_notes)
            jazz_voicings.append(sorted(note.midi for note in bar_notes if note.start_seconds == first_start))
    assert all(sum(abs(left - right) for left, right in zip(first, second)) <= 8 for first, second in zip(jazz_voicings, jazz_voicings[1:]))


def test_rock_drums_mark_sections_with_crashes_and_fills() -> None:
    base = _request()
    rock = generate_composition(base.model_copy(update={"settings": base.settings.model_copy(update={"style": "pop-rock"})}), _series())
    drums = rock.tracks[-1].notes

    assert sum(note.midi == 49 for note in drums) == 4
    assert sum(note.midi in {45, 47} for note in drums) == 12


def test_cinematic_crashes_chinese_arpeggios_and_final_sustain() -> None:
    base = _request()
    cinematic = generate_composition(base.model_copy(update={"settings": base.settings.model_copy(update={"style": "cinematic-epic"})}), _series())
    chinese = generate_composition(base.model_copy(update={"settings": base.settings.model_copy(update={"style": "chinese-folk"})}), _series())
    cinematic_drums = cinematic.tracks[-1]
    seconds_per_beat = 60 / chinese.settings.bpm
    chinese_harmony_starts = {
        round(note.start_seconds / seconds_per_beat, 2)
        for note in chinese.tracks[1].notes
        if note.start_seconds < 4 * seconds_per_beat
    }

    assert cinematic_drums.id == "drums"
    assert sum(note.midi == 49 for note in cinematic_drums.notes) == 4
    assert chinese_harmony_starts == {0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5}
    assert chinese.tracks[0].notes[-1].duration_seconds == pytest.approx(4 * seconds_per_beat)
    assert chinese.tracks[2].notes[-1].duration_seconds == pytest.approx(3.9 * seconds_per_beat)


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
