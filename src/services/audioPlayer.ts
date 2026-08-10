import type { CompositionDto, MusicNoteDto } from '../types/api'

const PIANO_SAMPLE_BASE = 'https://tonejs.github.io/audio/salamander/'

export class CompositionAudioPlayer {
  private tone: typeof import('tone') | null = null
  private piano: import('tone').Sampler | import('tone').PolySynth | null = null
  private harmony: import('tone').PolySynth | null = null
  private bass: import('tone').MonoSynth | null = null
  private master: import('tone').Gain | null = null
  private compositionId = ''
  private endEventId: number | null = null
  private onEnded: (() => void) | null = null

  async load(composition: CompositionDto, onEnded: () => void): Promise<{ sampledPiano: boolean }> {
    this.tone ??= await import('tone')
    const Tone = this.tone
    this.releaseAndDispose()
    const transport = Tone.getTransport()
    transport.stop()
    transport.cancel(0)
    transport.seconds = 0
    transport.bpm.value = composition.settings.bpm

    this.master = new Tone.Gain(0.72).toDestination()
    let sampledPiano = true
    const sampler = new Tone.Sampler({
      urls: { C4: 'C4.mp3', 'D#4': 'Ds4.mp3', 'F#4': 'Fs4.mp3', A4: 'A4.mp3' },
      baseUrl: PIANO_SAMPLE_BASE,
      attack: 0,
      release: 1.25,
      volume: -5,
    }).connect(this.master)
    try {
      await Promise.race([
        Tone.loaded(),
        new Promise<never>((_, reject) => window.setTimeout(() => reject(new Error('sample timeout')), 8000)),
      ])
      if (!sampler.loaded) throw new Error('sample unavailable')
      this.piano = sampler
    } catch {
      sampler.dispose()
      sampledPiano = false
      this.piano = new Tone.PolySynth(Tone.Synth, {
        volume: -10,
        oscillator: { type: 'triangle8' },
        envelope: { attack: 0.005, decay: 0.45, sustain: 0.08, release: 0.8 },
      }).connect(this.master)
    }

    this.harmony = new Tone.PolySynth(Tone.Synth, {
      volume: -17,
      oscillator: { type: 'fatsawtooth', count: 3, spread: 18 },
      envelope: { attack: 0.28, decay: 0.4, sustain: 0.52, release: 1.4 },
    }).connect(this.master)
    this.bass = new Tone.MonoSynth({
      volume: -13,
      oscillator: { type: 'triangle8' },
      filter: { type: 'lowpass', frequency: 650, Q: 1.2 },
      envelope: { attack: 0.015, decay: 0.25, sustain: 0.42, release: 0.45 },
      filterEnvelope: { attack: 0.02, decay: 0.18, sustain: 0.25, release: 0.35, baseFrequency: 90, octaves: 2.3 },
    }).connect(this.master)

    this.compositionId = composition.id
    this.onEnded = onEnded
    const melodyTrack = composition.tracks.find((track) => track.id === 'melody')
    const harmonyTrack = composition.tracks.find((track) => track.id === 'harmony')
    const bassTrack = composition.tracks.find((track) => track.id === 'bass')
    this.scheduleTrack(melodyTrack?.notes ?? [], 'melody')
    this.scheduleTrack(harmonyTrack?.notes ?? [], harmonyTrack?.instrument === 'piano' ? 'melody' : 'harmony')
    this.scheduleTrack(bassTrack?.notes ?? [], bassTrack?.instrument === 'piano' ? 'melody' : 'bass')
    this.endEventId = transport.scheduleOnce(() => {
      Tone.getDraw().schedule(() => this.onEnded?.(), Tone.now())
    }, composition.durationSeconds)
    return { sampledPiano }
  }

  private scheduleTrack(notes: MusicNoteDto[], track: 'melody' | 'harmony' | 'bass'): void {
    if (!this.tone) return
    const transport = this.tone.getTransport()
    for (const note of notes) {
      transport.schedule((time) => {
        if (track === 'melody') this.piano?.triggerAttackRelease(note.pitchName, note.durationSeconds, time, note.velocity / 127)
        if (track === 'harmony') this.harmony?.triggerAttackRelease(note.pitchName, note.durationSeconds, time, note.velocity / 127)
        if (track === 'bass') this.bass?.triggerAttackRelease(note.pitchName, note.durationSeconds, time, note.velocity / 127)
      }, note.startSeconds)
    }
  }

  async play(): Promise<void> {
    if (!this.tone || !this.compositionId) throw new Error('请先生成乐章')
    await this.tone.start()
    const transport = this.tone.getTransport()
    if (transport.state !== 'started') transport.start()
  }

  pause(): void {
    this.tone?.getTransport().pause()
    this.releaseAll()
  }

  seek(seconds: number): void {
    if (!this.tone) return
    this.releaseAll()
    this.tone.getTransport().seconds = Math.max(0, seconds)
  }

  setVolume(percent: number): void {
    if (this.master) this.master.gain.value = Math.max(0, Math.min(100, percent)) / 100
  }

  get currentSeconds(): number {
    return this.tone?.getTransport().seconds ?? 0
  }

  private releaseAll(): void {
    this.piano?.releaseAll()
    this.harmony?.releaseAll()
    this.bass?.triggerRelease()
  }

  private releaseAndDispose(): void {
    this.releaseAll()
    this.piano?.dispose()
    this.harmony?.dispose()
    this.bass?.dispose()
    this.master?.dispose()
    this.piano = null
    this.harmony = null
    this.bass = null
    this.master = null
  }

  dispose(): void {
    if (this.tone) {
      const transport = this.tone.getTransport()
      transport.stop()
      transport.cancel(0)
      if (this.endEventId !== null) transport.clear(this.endEventId)
    }
    this.releaseAndDispose()
    this.compositionId = ''
  }
}
