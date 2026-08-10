from __future__ import annotations

from .schemas import Composition, MusicTrack


TICKS_PER_BEAT = 480
PROGRAMS = {"piano": 0, "strings": 48, "bass": 32, "synth": 80}


def _variable_length(value: int) -> bytes:
    output = bytearray([value & 0x7F])
    while value >> 7:
        value >>= 7
        output.insert(0, (value & 0x7F) | 0x80)
    return bytes(output)


def _event(delta: int, payload: bytes) -> bytes:
    return _variable_length(delta) + payload


def _track_chunk(track_data: bytes | bytearray) -> bytes:
    return b"MTrk" + len(track_data).to_bytes(4, "big") + bytes(track_data)


def _conductor_track(composition: Composition) -> bytes:
    data = bytearray()
    name = f"Kline Melody - {composition.asset.symbol}".encode("utf-8")
    tempo = round(60_000_000 / composition.settings.bpm)
    data.extend(_event(0, b"\xff\x03" + _variable_length(len(name)) + name))
    data.extend(_event(0, b"\xff\x51\x03" + tempo.to_bytes(3, "big")))
    data.extend(_event(0, b"\xff\x58\x04\x04\x02\x18\x08"))
    data.extend(_event(0, b"\xff\x2f\x00"))
    return _track_chunk(data)


def _music_track(track: MusicTrack, channel: int, bpm: int) -> bytes:
    data = bytearray()
    name = track.name.encode("utf-8")
    data.extend(_event(0, b"\xff\x03" + _variable_length(len(name)) + name))
    instrument = track.instrument.lower()
    program = next((number for key, number in PROGRAMS.items() if key in instrument), 0)
    data.extend(_event(0, bytes((0xC0 | channel, program))))

    seconds_to_ticks = bpm * TICKS_PER_BEAT / 60
    events: list[tuple[int, int, bytes]] = []
    for note in track.notes:
        start_tick = round(note.start_seconds * seconds_to_ticks)
        end_tick = round((note.start_seconds + note.duration_seconds) * seconds_to_ticks)
        events.append((start_tick, 1, bytes((0x90 | channel, note.midi, note.velocity))))
        events.append((end_tick, 0, bytes((0x80 | channel, note.midi, 0))))
    events.sort(key=lambda item: (item[0], item[1]))

    previous_tick = 0
    for tick, _, payload in events:
        data.extend(_event(tick - previous_tick, payload))
        previous_tick = tick
    data.extend(_event(0, b"\xff\x2f\x00"))
    return _track_chunk(data)


def composition_to_midi(composition: Composition) -> bytes:
    channels = (0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15)
    music_chunks = [
        _music_track(track, channels[index], composition.settings.bpm)
        for index, track in enumerate(composition.tracks[: len(channels)])
    ]
    track_count = 1 + len(music_chunks)
    header = (
        b"MThd"
        + (6).to_bytes(4, "big")
        + (1).to_bytes(2, "big")
        + track_count.to_bytes(2, "big")
        + TICKS_PER_BEAT.to_bytes(2, "big")
    )
    return header + _conductor_track(composition) + b"".join(music_chunks)
