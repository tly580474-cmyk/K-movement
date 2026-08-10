from __future__ import annotations

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


def _quantile(values: list[float], fraction: float) -> float:
    if not values:
        return 0
    ordered = sorted(values)
    index = round((len(ordered) - 1) * fraction)
    return ordered[index]


def _pitch_name(midi: int) -> str:
    return f"{PITCH_NAMES[midi % 12]}{midi // 12 - 1}"


def _scale_notes(settings: GenerationSettings) -> list[int]:
    root = ROOT_PITCH_CLASS[settings.musical_key]
    intervals = SCALE_INTERVALS[settings.scale]
    return [
        midi
        for midi in range(48, 85)
        if (midi - root) % 12 in intervals
    ]


def _sample_indices(length: int, maximum: int = 256) -> list[int]:
    if length <= maximum:
        return list(range(length))
    step = (length - 1) / (maximum - 1)
    return sorted({round(position * step) for position in range(maximum)})


def _motif_copy(index: int, returns: list[float]) -> tuple[str, str, str]:
    total = sum(returns)
    spread = max(returns, default=0) - min(returns, default=0)
    if total >= 3:
        return "突破上行", "收益动能持续增强", "blue"
    if total <= -3:
        return "回落低吟", "价格重心明显下移", "violet"
    if spread >= 4:
        return "剧烈震荡", "高低波动形成紧张乐句", "gold"
    if index == 0:
        return "行情引子", "以初始价格区间建立主题", "mint"
    return "盘整变奏", "窄幅变化形成平稳乐句", "mint"


def _normalized_values(values: list[float]) -> list[float]:
    if not values:
        return []
    low, high = min(values), max(values)
    if high == low:
        return [50.0 for _ in values]
    return [round(20 + (value - low) / (high - low) * 60, 2) for value in values]


def _composition_id(request: CompositionCreateRequest) -> str:
    canonical = request.model_dump_json(by_alias=True, exclude_none=True)
    return sha256(canonical.encode("utf-8")).hexdigest()[:20]


def _chord_midis(settings: GenerationSettings, degree: int) -> tuple[int, int, int]:
    quality = "minor" if "minor" in settings.scale else "major"
    intervals = HEPTATONIC_INTERVALS[quality]
    tonic = 48 + ROOT_PITCH_CLASS[settings.musical_key]
    if tonic > 55:
        tonic -= 12
    notes: list[int] = []
    for offset in (0, 2, 4):
        scale_position = degree + offset
        octave, index = divmod(scale_position, 7)
        notes.append(tonic + intervals[index] + octave * 12)
    return notes[0], notes[1], notes[2]


def _progression_degree(chunk_index: int, chunk_returns: list[float]) -> int:
    total = sum(chunk_returns)
    if total > 1:
        progression = (0, 3, 4, 0)  # I–IV–V–I
    elif total < -1:
        progression = (5, 3, 0, 4)  # vi–IV–I–V
    else:
        progression = (0, 4, 5, 3)  # I–V–vi–IV
    return progression[chunk_index % len(progression)]


def generate_composition(
    request: CompositionCreateRequest,
    series: CandleSeriesResponse,
) -> Composition:
    if request.start_date > request.end_date:
        raise CompositionGenerationError("开始日期不能晚于结束日期")
    if len(series.items) < 2:
        raise CompositionGenerationError("至少需要 2 个交易日才能生成乐章")

    selected_indices = _sample_indices(len(series.items))
    returns = [
        series.indicators[index].return_pct
        if index < len(series.indicators) and series.indicators[index].return_pct is not None
        else (
            0.0
            if index == 0 or series.items[index - 1].close == 0
            else (series.items[index].close / series.items[index - 1].close - 1) * 100
        )
        for index in selected_indices
    ]
    return_limit = max(_quantile([abs(value) for value in returns], 0.9), 0.25)
    volumes = [float(series.items[index].volume or 0) for index in selected_indices]
    volume_median = median([value for value in volumes if value > 0]) if any(value > 0 for value in volumes) else 1.0
    atr_ratios = [
        (
            float(series.indicators[index].atr14 or 0) / series.items[index].close
            if index < len(series.indicators) and series.items[index].close
            else 0
        )
        for index in selected_indices
    ]
    atr_median = median([value for value in atr_ratios if value > 0]) if any(value > 0 for value in atr_ratios) else 0
    scale_notes = _scale_notes(request.settings)
    center = len(scale_notes) // 2
    seconds_per_beat = 60 / request.settings.bpm
    cursor_beats = 0.0
    notes: list[MusicNote] = []
    previous_pitch_index = center

    for sequence, candle_index in enumerate(selected_indices):
        normalized_return = max(-1.0, min(1.0, returns[sequence] / return_limit))
        pitch_offset = round(normalized_return * request.settings.mapping_strength * 7)
        if request.settings.mood == "upward":
            pitch_offset += round(sequence / max(1, len(selected_indices) - 1) * 2)
        elif request.settings.mood == "dark":
            pitch_offset -= 2
        target_pitch_index = max(0, min(len(scale_notes) - 1, center + pitch_offset))
        max_step = 3 if request.settings.mood == "tense" else 2
        pitch_index = max(
            0,
            min(
                len(scale_notes) - 1,
                max(previous_pitch_index - max_step, min(previous_pitch_index + max_step, target_pitch_index)),
            ),
        )
        previous_pitch_index = pitch_index
        midi = scale_notes[pitch_index]

        relative_volume = (
            series.indicators[candle_index].relative_volume20
            if candle_index < len(series.indicators)
            else None
        )
        volume_ratio = float(relative_volume) if relative_volume is not None else volumes[sequence] / volume_median
        velocity = round(45 + max(0, min(2, volume_ratio)) / 2 * 65)

        atr_ratio = atr_ratios[sequence]
        base_step = {"upward": 0.5, "calm": 0.75, "tense": 0.375, "dark": 0.625}[request.settings.mood]
        if atr_median and atr_ratio >= atr_median * 1.35:
            step_beats = max(0.25, base_step - 0.125)
        elif atr_median and atr_ratio <= atr_median * 0.7:
            step_beats = min(1.0, base_step + 0.125)
        else:
            step_beats = base_step
        duration_beats = step_beats * (1.45 if request.settings.mood == "calm" else 1.22)

        motif_number = sequence // 8
        notes.append(
            MusicNote(
                id=f"note-{sequence + 1}",
                track_id="melody",
                midi=midi,
                pitch_name=_pitch_name(midi),
                start_seconds=round(cursor_beats * seconds_per_beat, 6),
                duration_seconds=round(duration_beats * seconds_per_beat, 6),
                velocity=velocity,
                candle_index=candle_index,
                motif_id=f"motif-{motif_number + 1}",
            )
        )
        cursor_beats += step_beats

    harmony_notes: list[MusicNote] = []
    bass_notes: list[MusicNote] = []
    for chunk_index, start in enumerate(range(0, len(notes), 4)):
        chunk = notes[start:start + 4]
        chunk_returns = returns[start:start + len(chunk)]
        degree = _progression_degree(chunk_index, chunk_returns)
        chord = _chord_midis(request.settings, degree)
        chord_start = chunk[0].start_seconds
        if start + len(chunk) < len(notes):
            chord_end = notes[start + len(chunk)].start_seconds
        else:
            chord_end = notes[-1].start_seconds + notes[-1].duration_seconds
        chord_duration = max(seconds_per_beat, chord_end - chord_start + seconds_per_beat * 0.08)
        candle_index = chunk[0].candle_index
        motif_id = chunk[0].motif_id
        harmony_velocity = max(38, min(78, round(sum(note.velocity for note in chunk) / len(chunk) * 0.67)))
        for voice, midi in enumerate(chord):
            harmony_notes.append(
                MusicNote(
                    id=f"harmony-{chunk_index + 1}-{voice + 1}",
                    track_id="harmony",
                    midi=midi,
                    pitch_name=_pitch_name(midi),
                    start_seconds=round(chord_start, 6),
                    duration_seconds=round(chord_duration, 6),
                    velocity=harmony_velocity,
                    candle_index=candle_index,
                    motif_id=motif_id,
                )
            )
        bass_root = max(36, chord[0] - 12)
        bass_step = chord_duration / 2
        for pulse, midi in enumerate((bass_root, min(55, bass_root + 7))):
            bass_notes.append(
                MusicNote(
                    id=f"bass-{chunk_index + 1}-{pulse + 1}",
                    track_id="bass",
                    midi=midi,
                    pitch_name=_pitch_name(midi),
                    start_seconds=round(chord_start + pulse * bass_step, 6),
                    duration_seconds=round(bass_step * 0.94, 6),
                    velocity=max(42, harmony_velocity - 4),
                    candle_index=candle_index,
                    motif_id=motif_id,
                )
            )

    motifs: list[MarketMotif] = []
    for motif_number, start in enumerate(range(0, len(notes), 8)):
        chunk = notes[start:start + 8]
        chunk_returns = returns[start:start + len(chunk)]
        title, description, color = _motif_copy(motif_number, chunk_returns)
        motifs.append(
            MarketMotif(
                id=f"motif-{motif_number + 1}",
                label="引子" if motif_number == 0 else f"动机 #{motif_number + 1}",
                start_candle_index=chunk[0].candle_index,
                end_candle_index=chunk[-1].candle_index,
                start_seconds=chunk[0].start_seconds,
                end_seconds=round(chunk[-1].start_seconds + chunk[-1].duration_seconds, 6),
                title=title,
                description=description,
                color=color,
                values=_normalized_values([
                    series.items[note.candle_index].close for note in chunk
                ]),
            )
        )

    all_notes = notes + harmony_notes + bass_notes
    duration_seconds = round(max(note.start_seconds + note.duration_seconds for note in all_notes), 6)
    primary_instrument = request.settings.instruments[0]
    harmony_instrument = "strings" if "strings" in request.settings.instruments else primary_instrument
    bass_instrument = "bass" if "bass" in request.settings.instruments else primary_instrument
    return Composition(
        id=_composition_id(request),
        asset=series.asset,
        start_date=request.start_date,
        end_date=request.end_date,
        settings=request.settings,
        duration_seconds=duration_seconds,
        total_bars=max(1, ceil(cursor_beats / 4)),
        tracks=[
            MusicTrack(id="melody", name="市场主旋律", instrument=primary_instrument, notes=notes),
            MusicTrack(id="harmony", name="自动和声", instrument=harmony_instrument, notes=harmony_notes),
            MusicTrack(id="bass", name="和声低音", instrument=bass_instrument, notes=bass_notes),
        ],
        motifs=motifs,
        warnings=series.warnings,
    )
