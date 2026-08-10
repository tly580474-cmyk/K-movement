import type { CompositionDto, MusicNoteDto } from '../types/api'

const MIN_REST_SECONDS = 0.1

interface RestInterval {
  startSeconds: number
  endSeconds: number
}

export interface ScheduledNote {
  startSeconds: number
  durationSeconds: number
}

export interface PlaybackTimeline {
  durationSeconds: number
  sourceDurationSeconds: number
  rests: ReadonlyArray<RestInterval>
  toPlaybackSeconds: (sourceSeconds: number) => number
  toSourceSeconds: (playbackSeconds: number) => number
  scheduleNote: (note: MusicNoteDto) => ScheduledNote | null
}

function clamp(value: number, minimum: number, maximum: number): number {
  return Math.max(minimum, Math.min(maximum, value))
}

function melodyRests(composition: CompositionDto): RestInterval[] {
  const notes = [...(composition.tracks.find((track) => track.id === 'melody')?.notes ?? [])]
    .sort((left, right) => left.startSeconds - right.startSeconds)
  if (!notes.length) return []

  const rests: RestInterval[] = []
  let soundingUntil = 0
  for (const note of notes) {
    const startSeconds = clamp(note.startSeconds, 0, composition.durationSeconds)
    if (startSeconds - soundingUntil >= MIN_REST_SECONDS) {
      rests.push({ startSeconds: soundingUntil, endSeconds: startSeconds })
    }
    soundingUntil = Math.max(soundingUntil, startSeconds + Math.max(0, note.durationSeconds))
  }
  return rests
}

export function buildPlaybackTimeline(composition: CompositionDto | null, playBreaths: boolean): PlaybackTimeline {
  const sourceDurationSeconds = Math.max(0, composition?.durationSeconds ?? 0)
  const rests = composition && !playBreaths ? melodyRests(composition) : []

  const toPlaybackSeconds = (sourceSeconds: number): number => {
    const clampedSource = clamp(sourceSeconds, 0, sourceDurationSeconds)
    const removed = rests.reduce((total, rest) => (
      total + clamp(clampedSource - rest.startSeconds, 0, rest.endSeconds - rest.startSeconds)
    ), 0)
    return clampedSource - removed
  }

  const durationSeconds = toPlaybackSeconds(sourceDurationSeconds)

  const toSourceSeconds = (playbackSeconds: number): number => {
    const target = clamp(playbackSeconds, 0, durationSeconds)
    let sourceCursor = 0
    let playbackCursor = 0
    for (const rest of rests) {
      const soundingDuration = rest.startSeconds - sourceCursor
      if (target < playbackCursor + soundingDuration) {
        return sourceCursor + target - playbackCursor
      }
      playbackCursor += soundingDuration
      sourceCursor = rest.endSeconds
    }
    return clamp(sourceCursor + target - playbackCursor, 0, sourceDurationSeconds)
  }

  const scheduleNote = (note: MusicNoteDto): ScheduledNote | null => {
    const startSeconds = toPlaybackSeconds(note.startSeconds)
    const endSeconds = toPlaybackSeconds(note.startSeconds + note.durationSeconds)
    const durationSeconds = endSeconds - startSeconds
    return durationSeconds > 0.01 ? { startSeconds, durationSeconds } : null
  }

  return { durationSeconds, sourceDurationSeconds, rests, toPlaybackSeconds, toSourceSeconds, scheduleNote }
}
