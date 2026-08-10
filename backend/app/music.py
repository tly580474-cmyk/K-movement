from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from math import ceil
from statistics import median

from .schemas import (
    CandleSeriesResponse,
    Composition,
    CompositionCreateRequest,
    GenerationSettings,
    MarketMotif,
    MusicNote,
    MusicTrack,
)


class CompositionGenerationError(ValueError):
    pass


BEATS_PER_BAR = 4
MIN_BARS = 16
MAX_BARS = 32
SECTION_ROLES = ("A", "A′", "B", "A″")
SCALE_INTERVALS = {
    "major-pentatonic": (0, 2, 4, 7, 9),
    "minor-pentatonic": (0, 3, 5, 7, 10),
    "major": (0, 2, 4, 5, 7, 9, 11),
    "minor": (0, 2, 3, 5, 7, 8, 10),
}
ROOT_PITCH_CLASS = {"C": 0, "D": 2, "G": 7, "A": 9}
PITCH_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
HEPTATONIC_INTERVALS = {
    "major": (0, 2, 4, 5, 7, 9, 11),
    "minor": (0, 2, 3, 5, 7, 8, 10),
}
STYLE_LEGATO_FACTORS = {
    "jazz-lounge": 1.08,
    "cinematic-epic": 1.04,
    "chinese-folk": 1.08,
    "ambient-minimal": 1.32,
    "pop-rock": 0.88,
}
RHYTHM_PATTERNS: dict[str, tuple[tuple[float, float], ...]] = {
    "sparse": ((0.0, 1.25), (2.5, 1.0)),
    "calm": ((0.0, 1.0), (1.5, 0.5), (2.5, 1.0)),
    "steady": ((0.0, 0.75), (1.0, 0.5), (2.0, 0.75), (3.0, 0.75)),
    "syncopated": ((0.0, 0.5), (0.75, 0.75), (2.0, 0.5), (2.75, 0.5), (3.5, 0.5)),
    "active": ((0.0, 0.5), (0.75, 0.5), (1.5, 0.5), (2.0, 0.5), (2.75, 0.5), (3.5, 0.5)),
    "cadence": ((0.0, 0.75), (1.0, 0.5), (2.0, 2.0)),
}


@dataclass(frozen=True)
class BarPlan:
    index: int
    section: int
    role: str
    source_positions: tuple[int, ...]
    degree: int
    activity: float
    rhythm: tuple[tuple[float, float], ...]
    cadence: bool


def _quantile(values: list[float], fraction: float) -> float:
    if not values:
        return 0
    ordered = sorted(values)
    index = round((len(ordered) - 1) * fraction)
    return ordered[index]


def _pitch_name(midi: int) -> str:
    return f"{PITCH_NAMES[midi % 12]}{midi // 12 - 1}"


def _sample_indices(length: int, maximum: int = 128) -> list[int]:
    if length <= maximum:
        return list(range(length))
    step = (length - 1) / (maximum - 1)
    return sorted({round(position * step) for position in range(maximum)})


def _effective_settings(settings: GenerationSettings, trend: str) -> GenerationSettings:
    scale = settings.scale
    if trend == "bullish":
        scale = "major-pentatonic" if "pentatonic" in scale else "major"
    elif trend == "bearish":
        scale = "minor-pentatonic" if "pentatonic" in scale else "minor"
    if settings.style == "chinese-folk":
        scale = "minor-pentatonic" if "minor" in scale else "major-pentatonic"
    return settings.model_copy(update={"scale": scale})


def _scale_notes(settings: GenerationSettings) -> list[int]:
    root = ROOT_PITCH_CLASS[settings.musical_key]
    return [
        midi
        for midi in range(48, 89)
        if (midi - root) % 12 in SCALE_INTERVALS[settings.scale]
    ]


def _composition_id(request: CompositionCreateRequest) -> str:
    canonical = request.model_dump_json(by_alias=True, exclude_none=True)
    return sha256(canonical.encode("utf-8")).hexdigest()[:20]


def _trend_state(series: CandleSeriesResponse, returns: list[float]) -> str:
    if series.analysis and series.analysis.trend_state != "unknown":
        return series.analysis.trend_state
    total = sum(returns)
    if total > 1:
        return "bullish"
    if total < -1:
        return "bearish"
    return "sideways"


def _chord_midis(settings: GenerationSettings, degree: int) -> tuple[int, ...]:
    quality = "minor" if "minor" in settings.scale else "major"
    intervals = HEPTATONIC_INTERVALS[quality]
    tonic = 48 + ROOT_PITCH_CLASS[settings.musical_key]
    if tonic > 55:
        tonic -= 12

    def note_at(offset: int) -> int:
        scale_position = degree + offset
        octave, index = divmod(scale_position, 7)
        return tonic + intervals[index] + octave * 12

    root = note_at(0)
    third = note_at(2)
    fifth = note_at(4)
    if settings.style == "jazz-lounge":
        return root, third, fifth, note_at(6)
    if settings.style == "cinematic-epic":
        return root, third, fifth, root + 12
    if settings.style == "chinese-folk":
        return root, fifth, root + 12
    if settings.style == "ambient-minimal":
        return root, note_at(1), fifth
    if settings.style == "pop-rock":
        return root, fifth, root + 12
    return root, third, fifth


def _section_progression(trend: str, role: str) -> tuple[int, ...]:
    if trend == "bearish":
        progressions = {
            "A": (0, 5, 3, 4),
            "A′": (0, 3, 5, 4),
            "B": (5, 2, 3, 4),
            "A″": (0, 5, 4, 0),
        }
    elif trend == "sideways":
        progressions = {
            "A": (0, 4, 5, 3),
            "A′": (0, 3, 1, 4),
            "B": (5, 3, 1, 4),
            "A″": (0, 3, 4, 0),
        }
    else:
        progressions = {
            "A": (0, 3, 4, 0),
            "A′": (0, 5, 3, 4),
            "B": (5, 3, 1, 4),
            "A″": (0, 3, 4, 0),
        }
    return progressions[role]


def _rhythm_for_bar(style: str, mood: str, activity: float, cadence: bool) -> tuple[tuple[float, float], ...]:
    if cadence:
        return RHYTHM_PATTERNS["cadence"]
    if style == "ambient-minimal":
        return RHYTHM_PATTERNS["sparse"]
    if style == "pop-rock":
        return RHYTHM_PATTERNS["active" if activity >= 0.65 else "steady"]
    if style == "jazz-lounge":
        return RHYTHM_PATTERNS["syncopated" if activity >= 0.48 else "calm"]
    if mood == "tense" or activity >= 0.72:
        return RHYTHM_PATTERNS["active"]
    if mood == "calm" or activity <= 0.32:
        return RHYTHM_PATTERNS["sparse"]
    return RHYTHM_PATTERNS["steady"]


def _bar_count(sample_count: int) -> int:
    requested = max(MIN_BARS, min(MAX_BARS, ceil(sample_count / 4)))
    return min(MAX_BARS, ceil(requested / 4) * 4)


def _partition_sources(source_count: int, total_bars: int, bar_index: int) -> tuple[int, ...]:
    start = bar_index * source_count // total_bars
    end = (bar_index + 1) * source_count // total_bars
    if end <= start:
        position = round(bar_index / max(1, total_bars - 1) * (source_count - 1))
        return (position,)
    return tuple(range(start, end))


def _key_source_positions(series: CandleSeriesResponse, selected_indices: list[int], returns: list[float]) -> set[int]:
    closes = [series.items[index].close for index in selected_indices]
    key_positions = {closes.index(max(closes)), closes.index(min(closes))}
    move_cutoff = _quantile([abs(value) for value in returns], 0.75)
    for position in range(1, len(closes) - 1):
        left = closes[position] - closes[position - 1]
        right = closes[position + 1] - closes[position]
        if left * right <= 0 and abs(returns[position]) >= move_cutoff:
            key_positions.add(position)
        window = closes[max(0, position - 8):position]
        if window and (closes[position] > max(window) or closes[position] < min(window)):
            key_positions.add(position)
    return key_positions


def _theme_contour(returns: list[float], return_limit: float, length: int = 8) -> tuple[int, ...]:
    source = returns[:max(1, ceil(len(returns) / 4))]
    contour: list[int] = []
    for position in range(length):
        source_index = round(position / max(1, length - 1) * (len(source) - 1))
        normalized = max(-1.0, min(1.0, source[source_index] / return_limit))
        contour.append(round(normalized * 3))
    return tuple(contour)


def _nearest_chord_index(scale_notes: list[int], target_index: int, chord: tuple[int, ...]) -> int:
    chord_classes = {midi % 12 for midi in chord}
    candidates = [index for index, midi in enumerate(scale_notes) if midi % 12 in chord_classes]
    return min(candidates, key=lambda index: abs(index - target_index)) if candidates else target_index


def _motif_copy(role: str, returns: list[float]) -> tuple[str, str, str]:
    total = sum(returns)
    spread = max(returns, default=0) - min(returns, default=0)
    if role == "A":
        return "行情主题", "从首段走势提取核心音程轮廓", "mint"
    if role == "A′":
        return "主题变奏", "保留核心轮廓并由当前行情改变重音", "blue"
    if role == "B":
        return "对比发展", "倒影音程与高音区形成行情转折", "gold" if spread >= 4 else "violet"
    if total >= 0:
        return "主题回归", "主题材料回归并以属主终止收束", "blue"
    return "低位回归", "主题在低位回归并完成调性解决", "violet"


def _normalized_values(values: list[float]) -> list[float]:
    if not values:
        return []
    low, high = min(values), max(values)
    if high == low:
        return [50.0 for _ in values]
    return [round(20 + (value - low) / (high - low) * 60, 2) for value in values]


def generate_composition(request: CompositionCreateRequest, series: CandleSeriesResponse) -> Composition:
    if request.start_date > request.end_date:
        raise CompositionGenerationError("开始日期不能晚于结束日期")
    if len(series.items) < 2:
        raise CompositionGenerationError("至少需要 2 个交易日才能生成乐章")
    if not request.settings.instruments:
        raise CompositionGenerationError("至少需要选择一种乐器")

    selected_indices = _sample_indices(len(series.items))
    returns = [
        series.indicators[index].return_pct
        if index < len(series.indicators) and series.indicators[index].return_pct is not None
        else (0.0 if index == 0 or series.items[index - 1].close == 0 else (series.items[index].close / series.items[index - 1].close - 1) * 100)
        for index in selected_indices
    ]
    volumes = [float(series.items[index].volume or 0) for index in selected_indices]
    volume_median = median([value for value in volumes if value > 0]) if any(value > 0 for value in volumes) else 1.0
    volume_ratios = [
        float(series.indicators[index].relative_volume20)
        if index < len(series.indicators) and series.indicators[index].relative_volume20 is not None
        else volume / volume_median
        for index, volume in zip(selected_indices, volumes)
    ]
    atr_ratios = [
        float(series.indicators[index].atr14 or 0) / series.items[index].close
        if index < len(series.indicators) and series.items[index].close else 0
        for index in selected_indices
    ]
    atr_median = median([value for value in atr_ratios if value > 0]) if any(value > 0 for value in atr_ratios) else 1.0
    return_limit = max(_quantile([abs(value) for value in returns], 0.9), 0.25)
    source_activity = [
        min(1.0, abs(ret) / return_limit * 0.45 + min(2.0, volume) / 2 * 0.3 + min(2.0, atr / atr_median) / 2 * 0.25)
        for ret, volume, atr in zip(returns, volume_ratios, atr_ratios)
    ]
    quiet_cutoff = _quantile(source_activity, 0.2)
    key_positions = _key_source_positions(series, selected_indices, returns)
    trend = _trend_state(series, returns)
    settings = _effective_settings(request.settings, trend)
    scale_notes = _scale_notes(settings)
    center = len(scale_notes) // 2
    seconds_per_beat = 60 / settings.bpm
    total_bars = _bar_count(len(selected_indices))
    section_bars = total_bars // 4
    theme = _theme_contour(returns, return_limit)

    bars: list[BarPlan] = []
    for bar_index in range(total_bars):
        section = min(3, bar_index // section_bars)
        role = SECTION_ROLES[section]
        within_section = bar_index - section * section_bars
        positions = _partition_sources(len(selected_indices), total_bars, bar_index)
        activity = sum(source_activity[position] for position in positions) / len(positions)
        progression = _section_progression(trend, role)
        degree = progression[within_section % len(progression)]
        if within_section == section_bars - 2:
            degree = 4
        elif within_section == section_bars - 1:
            degree = 0
        cadence = within_section == section_bars - 1
        rhythm = _rhythm_for_bar(settings.style, settings.mood, activity, cadence)
        bars.append(BarPlan(bar_index, section, role, positions, degree, activity, rhythm, cadence))

    melody_notes: list[MusicNote] = []
    previous_pitch_index = center
    section_dynamics = {"A": -4, "A′": 1, "B": 7, "A″": 3}
    style_velocity = {"jazz-lounge": -4, "cinematic-epic": 10, "chinese-folk": 2, "ambient-minimal": -10, "pop-rock": 9}
    for bar in bars:
        chord = _chord_midis(settings, bar.degree)
        is_quiet_bar = (
            all(source_activity[position] <= quiet_cutoff for position in bar.source_positions)
            and not any(position in key_positions for position in bar.source_positions)
            and not bar.cadence
            and bar.index % section_bars != 0
        )
        if is_quiet_bar:
            continue
        for slot, (beat, notated_duration) in enumerate(bar.rhythm):
            source_position = bar.source_positions[min(len(bar.source_positions) - 1, slot * len(bar.source_positions) // len(bar.rhythm))]
            if source_activity[source_position] <= quiet_cutoff and source_position not in key_positions and not bar.cadence:
                continue
            candle_index = selected_indices[source_position]
            normalized_return = max(-1.0, min(1.0, returns[source_position] / return_limit))
            data_offset = round(normalized_return * settings.mapping_strength * 7)
            theme_index = round((bar.index % section_bars + beat / BEATS_PER_BAR) / section_bars * (len(theme) - 1))
            theme_offset = theme[min(len(theme) - 1, theme_index)]
            if bar.role == "A":
                shaped_offset = round(theme_offset * 0.55 + data_offset * 0.45)
            elif bar.role == "A′":
                shaped_offset = round(theme_offset * 0.7 + data_offset * 0.3) + (1 if slot % 2 else 0)
            elif bar.role == "B":
                shaped_offset = -theme_offset + round(data_offset * 0.35) + 4
            else:
                shaped_offset = round(theme_offset * 0.8 + data_offset * 0.2) + (1 if trend == "bullish" else -1 if trend == "bearish" else 0)
            if settings.mood == "dark":
                shaped_offset -= 2
            target_index = max(0, min(len(scale_notes) - 1, center + shaped_offset))
            if beat in {0.0, 2.0}:
                target_index = _nearest_chord_index(scale_notes, target_index, chord)
            max_step = {"ambient-minimal": 1, "cinematic-epic": 4, "pop-rock": 3}.get(settings.style, 3 if settings.mood == "tense" else 2)
            if bar.role == "B" and bar.index == bar.section * section_bars and slot == 0:
                max_step = 5
            pitch_index = max(0, min(len(scale_notes) - 1, max(previous_pitch_index - max_step, min(previous_pitch_index + max_step, target_index))))
            if bar.cadence and beat == 2.0:
                tonic_class = ROOT_PITCH_CLASS[settings.musical_key]
                tonic_indices = [index for index, midi in enumerate(scale_notes) if midi % 12 == tonic_class]
                pitch_index = min(tonic_indices, key=lambda index: abs(index - center))
            previous_pitch_index = pitch_index
            volume_ratio = volume_ratios[source_position]
            beat_weight = 12 if beat == 0 else 7 if beat == 2 else -4
            phrase_arc = round(5 * (bar.index % section_bars) / max(1, section_bars - 1))
            velocity = round(48 + min(2.0, volume_ratio) / 2 * 45 + beat_weight + phrase_arc + section_dynamics[bar.role] + style_velocity.get(settings.style, 0))
            if source_position in key_positions:
                velocity += 10
            velocity = max(32, min(122, velocity))
            legato = STYLE_LEGATO_FACTORS.get(settings.style, 1.08 if settings.mood == "calm" else 0.96)
            duration_beats = min(BEATS_PER_BAR - beat, notated_duration * legato)
            if bar.cadence and beat == 2.0:
                duration_beats = 2.0
            if source_position in key_positions and not bar.cadence:
                duration_beats = min(BEATS_PER_BAR - beat, max(duration_beats, 1.25))
            melody_notes.append(MusicNote(
                id=f"note-{len(melody_notes) + 1}", track_id="melody", midi=scale_notes[pitch_index], pitch_name=_pitch_name(scale_notes[pitch_index]),
                start_seconds=round((bar.index * BEATS_PER_BAR + beat) * seconds_per_beat, 6),
                duration_seconds=round(max(0.125, duration_beats) * seconds_per_beat, 6), velocity=velocity,
                candle_index=candle_index, motif_id=f"motif-{bar.section + 1}",
            ))

    harmony_notes: list[MusicNote] = []
    bass_notes: list[MusicNote] = []
    for bar in bars:
        chord = _chord_midis(settings, bar.degree)
        start_seconds = bar.index * BEATS_PER_BAR * seconds_per_beat
        duration_seconds = BEATS_PER_BAR * seconds_per_beat
        candle_index = selected_indices[bar.source_positions[0]]
        harmony_velocity = max(36, min(82, round(48 + bar.activity * 22 + section_dynamics[bar.role])))
        for voice, midi in enumerate(chord):
            harmony_notes.append(MusicNote(
                id=f"harmony-{bar.index + 1}-{voice + 1}", track_id="harmony", midi=midi, pitch_name=_pitch_name(midi),
                start_seconds=round(start_seconds, 6), duration_seconds=round(duration_seconds, 6), velocity=harmony_velocity,
                candle_index=candle_index, motif_id=f"motif-{bar.section + 1}",
            ))
        bass_root = max(36, chord[0] - 12)
        for pulse, midi in enumerate((bass_root, min(55, bass_root + 7))):
            bass_notes.append(MusicNote(
                id=f"bass-{bar.index + 1}-{pulse + 1}", track_id="bass", midi=midi, pitch_name=_pitch_name(midi),
                start_seconds=round((bar.index * BEATS_PER_BAR + pulse * 2) * seconds_per_beat, 6),
                duration_seconds=round(1.8 * seconds_per_beat, 6), velocity=max(40, harmony_velocity - 5),
                candle_index=candle_index, motif_id=f"motif-{bar.section + 1}",
            ))

    drum_notes: list[MusicNote] = []
    if settings.style == "pop-rock":
        for bar in bars:
            candle_index = selected_indices[bar.source_positions[0]]
            for half_beat in range(8):
                beat = half_beat / 2
                events = [(42, 62 + (8 if half_beat in {0, 4} else 0))]
                if half_beat % 2 == 0:
                    events.append((36 if half_beat in {0, 4} else 38, 108 if half_beat in {0, 4} else 98))
                for event_index, (midi, velocity) in enumerate(events):
                    drum_notes.append(MusicNote(
                        id=f"drum-{bar.index + 1}-{half_beat + 1}-{event_index + 1}", track_id="drums", midi=midi,
                        pitch_name=_pitch_name(midi), start_seconds=round((bar.index * 4 + beat) * seconds_per_beat, 6),
                        duration_seconds=round(seconds_per_beat * 0.16, 6), velocity=velocity,
                        candle_index=candle_index, motif_id=f"motif-{bar.section + 1}",
                    ))

    motifs: list[MarketMotif] = []
    for section, role in enumerate(SECTION_ROLES):
        section_plan = bars[section * section_bars:(section + 1) * section_bars]
        positions = sorted({position for bar in section_plan for position in bar.source_positions})
        section_returns = [returns[position] for position in positions]
        title, description, color = _motif_copy(role, section_returns)
        motifs.append(MarketMotif(
            id=f"motif-{section + 1}", label=role,
            start_candle_index=selected_indices[positions[0]], end_candle_index=selected_indices[positions[-1]],
            start_seconds=round(section * section_bars * 4 * seconds_per_beat, 6),
            end_seconds=round((section + 1) * section_bars * 4 * seconds_per_beat, 6),
            title=title, description=description, color=color,
            values=_normalized_values([series.items[selected_indices[position]].close for position in positions]),
        ))

    duration_seconds = round(total_bars * BEATS_PER_BAR * seconds_per_beat, 6)
    primary_instrument = settings.instruments[0]
    harmony_instrument = settings.instruments[1] if len(settings.instruments) > 1 else primary_instrument
    bass_instrument = settings.instruments[2] if len(settings.instruments) > 2 else primary_instrument
    tracks = [
        MusicTrack(id="melody", name="市场主旋律", instrument=primary_instrument, notes=melody_notes),
        MusicTrack(id="harmony", name="小节和声", instrument=harmony_instrument, notes=harmony_notes),
        MusicTrack(id="bass", name="和声低音", instrument=bass_instrument, notes=bass_notes),
    ]
    if drum_notes:
        tracks.append(MusicTrack(id="drums", name="摇滚鼓组", instrument="drums", notes=drum_notes))
    return Composition(
        id=_composition_id(request), asset=series.asset, start_date=request.start_date, end_date=request.end_date,
        settings=settings, duration_seconds=duration_seconds, total_bars=total_bars, tracks=tracks, motifs=motifs,
        warnings=series.warnings,
    )
