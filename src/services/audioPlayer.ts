import type { CompositionDto, MusicNoteDto, MusicStyle } from '../types/api'

const PIANO_SAMPLE_BASE = 'https://tonejs.github.io/audio/salamander/'
const sampledStyles = new Set<MusicStyle>(['orchestral', 'piano', 'lofi', 'jazz-lounge', 'cinematic-epic', 'ambient-minimal'])

export class CompositionAudioPlayer {
  private tone: typeof import('tone') | null = null
  private melody: import('tone').Sampler | import('tone').PolySynth | null = null
  private harmony: import('tone').PolySynth | null = null
  private bass: import('tone').MonoSynth | null = null
  private kick: import('tone').MembraneSynth | null = null
  private snare: import('tone').NoiseSynth | null = null
  private hiHat: import('tone').NoiseSynth | null = null
  private crash: import('tone').MetalSynth | null = null
  private tom: import('tone').MembraneSynth | null = null
  private space: import('tone').Reverb | null = null
  private master: import('tone').Gain | null = null
  private compositionId = ''
  private endEventId: number | null = null
  private onEnded: (() => void) | null = null

  async load(composition: CompositionDto, onEnded: () => void): Promise<{ sampledPiano: boolean; sampleFallback: boolean }> {
    this.tone ??= await import('tone')
    const Tone = this.tone
    this.releaseAndDispose()
    const transport = Tone.getTransport()
    transport.stop()
    transport.cancel(0)
    transport.seconds = 0
    transport.bpm.value = composition.settings.bpm
    this.master = new Tone.Gain(0.72).toDestination()
    this.space = new Tone.Reverb({
      decay: composition.settings.style === 'ambient-minimal' ? 5.5 : composition.settings.style === 'cinematic-epic' ? 4.2 : 2.8,
      preDelay: 0.025,
      wet: composition.settings.style === 'ambient-minimal' ? 0.42 : composition.settings.style === 'pop-rock' ? 0.16 : 0.27,
    }).connect(this.master)
    await this.space.ready

    const wantsSamples = sampledStyles.has(composition.settings.style)
    let sampledPiano = false
    let sampleFallback = false
    if (wantsSamples) {
      const sampler = new Tone.Sampler({
        urls: { C4: 'C4.mp3', 'D#4': 'Ds4.mp3', 'F#4': 'Fs4.mp3', A4: 'A4.mp3' },
        baseUrl: PIANO_SAMPLE_BASE,
        attack: 0,
        release: composition.settings.style === 'ambient-minimal' ? 2.4 : 1.25,
        volume: -5,
      }).connect(this.space)
      try {
        await Promise.race([
          Tone.loaded(),
          new Promise<never>((_, reject) => window.setTimeout(() => reject(new Error('sample timeout')), 8000)),
        ])
        if (!sampler.loaded) throw new Error('sample unavailable')
        this.melody = sampler
        sampledPiano = true
      } catch {
        sampler.dispose()
        sampleFallback = true
      }
    }
    if (!this.melody) this.melody = this.createStyleMelody(composition.settings.style)

    this.harmony = this.createStyleHarmony(composition.settings.style)
    this.bass = new Tone.MonoSynth({
      volume: composition.settings.style === 'cinematic-epic' ? -9 : -13,
      oscillator: { type: composition.settings.style === 'pop-rock' ? 'square8' : 'triangle8' },
      filter: { type: 'lowpass', frequency: 650, Q: 1.2 },
      envelope: { attack: 0.015, decay: 0.25, sustain: 0.42, release: 0.45 },
      filterEnvelope: { attack: 0.02, decay: 0.18, sustain: 0.25, release: 0.35, baseFrequency: 90, octaves: 2.3 },
    }).connect(this.master)

    const drumTrack = composition.tracks.find((track) => track.id === 'drums')
    if (drumTrack) {
      this.kick = new Tone.MembraneSynth({ volume: -7, pitchDecay: 0.04, octaves: 5 }).connect(this.master)
      this.snare = new Tone.NoiseSynth({ volume: -13, noise: { type: 'pink' }, envelope: { attack: 0.001, decay: 0.16, sustain: 0, release: 0.08 } }).connect(this.master)
      this.hiHat = new Tone.NoiseSynth({ volume: -20, noise: { type: 'white' }, envelope: { attack: 0.001, decay: 0.035, sustain: 0, release: 0.025 } }).connect(this.master)
      this.crash = new Tone.MetalSynth({ volume: -17, harmonicity: 5.1, modulationIndex: 24, resonance: 3200, octaves: 1.5, envelope: { attack: 0.001, decay: 0.7, release: 0.35 } }).connect(this.master)
      this.crash.frequency.value = 220
      this.tom = new Tone.MembraneSynth({ volume: -11, pitchDecay: 0.07, octaves: 3.5 }).connect(this.master)
    }

    this.compositionId = composition.id
    this.onEnded = onEnded
    const melodyTrack = composition.tracks.find((track) => track.id === 'melody')
    const harmonyTrack = composition.tracks.find((track) => track.id === 'harmony')
    const bassTrack = composition.tracks.find((track) => track.id === 'bass')
    this.scheduleTrack(melodyTrack?.notes ?? [], 'melody')
    this.scheduleTrack(harmonyTrack?.notes ?? [], harmonyTrack?.instrument === 'piano' ? 'melody' : 'harmony')
    this.scheduleTrack(bassTrack?.notes ?? [], bassTrack?.instrument === 'piano' ? 'melody' : 'bass')
    this.scheduleTrack(drumTrack?.notes ?? [], 'drums')
    this.endEventId = transport.scheduleOnce(() => {
      Tone.getDraw().schedule(() => this.onEnded?.(), Tone.now())
    }, composition.durationSeconds)
    return { sampledPiano, sampleFallback }
  }

  private createStyleMelody(style: MusicStyle): import('tone').PolySynth {
    const Tone = this.tone!
    if (style === 'chinese-folk') {
      return new Tone.PolySynth(Tone.Synth, {
        volume: -8,
        oscillator: { type: 'triangle8' },
        envelope: { attack: 0.002, decay: 0.5, sustain: 0.06, release: 0.9 },
      }).connect(this.space!)
    }
    if (style === 'pop-rock') {
      return new Tone.PolySynth(Tone.Synth, {
        volume: -11,
        oscillator: { type: 'fatsawtooth', count: 2, spread: 12 },
        envelope: { attack: 0.006, decay: 0.18, sustain: 0.34, release: 0.28 },
      }).connect(this.space!)
    }
    return new Tone.PolySynth(Tone.Synth, {
      volume: -10,
      oscillator: { type: style === 'synth' ? 'square8' : 'triangle8' },
      envelope: { attack: 0.004, decay: 0.72, sustain: 0.2, release: style === 'piano' ? 1.8 : 1.15 },
    }).connect(this.space!)
  }

  private createStyleHarmony(style: MusicStyle): import('tone').PolySynth {
    const Tone = this.tone!
    if (style === 'jazz-lounge') {
      return new Tone.PolySynth(Tone.Synth, { volume: -15, oscillator: { type: 'sine4' }, envelope: { attack: 0.04, decay: 0.35, sustain: 0.3, release: 1.1 } }).connect(this.space!)
    }
    if (style === 'ambient-minimal') {
      return new Tone.PolySynth(Tone.Synth, { volume: -20, oscillator: { type: 'sine' }, envelope: { attack: 0.9, decay: 0.8, sustain: 0.62, release: 3.2 } }).connect(this.space!)
    }
    if (style === 'chinese-folk') {
      return new Tone.PolySynth(Tone.Synth, { volume: -17, oscillator: { type: 'triangle4' }, envelope: { attack: 0.08, decay: 0.5, sustain: 0.25, release: 1.2 } }).connect(this.space!)
    }
    return new Tone.PolySynth(Tone.Synth, {
      volume: style === 'cinematic-epic' ? -12 : -17,
      oscillator: { type: style === 'pop-rock' ? 'sawtooth' : 'fatsawtooth', count: 3, spread: 18 },
      envelope: { attack: style === 'cinematic-epic' ? 0.12 : 0.28, decay: 0.4, sustain: 0.52, release: 1.4 },
    }).connect(this.space!)
  }

  private scheduleTrack(notes: MusicNoteDto[], track: 'melody' | 'harmony' | 'bass' | 'drums'): void {
    if (!this.tone) return
    const transport = this.tone.getTransport()
    for (const note of notes) {
      transport.schedule((time) => {
        const velocity = note.velocity / 127
        if (track === 'melody') this.melody?.triggerAttackRelease(note.pitchName, note.durationSeconds, time, velocity)
        if (track === 'harmony') this.harmony?.triggerAttackRelease(note.pitchName, note.durationSeconds, time, velocity)
        if (track === 'bass') this.bass?.triggerAttackRelease(note.pitchName, note.durationSeconds, time, velocity)
        if (track === 'drums' && note.midi === 36) this.kick?.triggerAttackRelease('C1', note.durationSeconds, time, velocity)
        if (track === 'drums' && note.midi === 38) this.snare?.triggerAttackRelease(note.durationSeconds, time, velocity)
        if (track === 'drums' && note.midi === 42) this.hiHat?.triggerAttackRelease(note.durationSeconds, time, velocity)
        if (track === 'drums' && note.midi === 49) this.crash?.triggerAttackRelease(note.durationSeconds, time, velocity)
        if (track === 'drums' && note.midi === 45) this.tom?.triggerAttackRelease('G1', note.durationSeconds, time, velocity)
        if (track === 'drums' && note.midi === 47) this.tom?.triggerAttackRelease('C2', note.durationSeconds, time, velocity)
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
    this.melody?.releaseAll()
    this.harmony?.releaseAll()
    this.bass?.triggerRelease()
    this.kick?.triggerRelease()
  }

  private releaseAndDispose(): void {
    this.releaseAll()
    this.melody?.dispose()
    this.harmony?.dispose()
    this.bass?.dispose()
    this.kick?.dispose()
    this.snare?.dispose()
    this.hiHat?.dispose()
    this.crash?.dispose()
    this.tom?.dispose()
    this.space?.dispose()
    this.master?.dispose()
    this.melody = null
    this.harmony = null
    this.bass = null
    this.kick = null
    this.snare = null
    this.hiHat = null
    this.crash = null
    this.tom = null
    this.space = null
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
