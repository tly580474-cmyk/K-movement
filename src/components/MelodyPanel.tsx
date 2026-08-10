import { Info, Music2, Sparkles } from 'lucide-react'
import { melodyNotes, pianoKeys } from '../data'
import type { CompositionDto, MusicNoteDto } from '../types/api'
import { Panel } from './Panel'

function StaffMelody() {
  return (
    <div className="staff-melody" aria-label="旋律走向示意">
      <svg viewBox="0 0 620 145" role="img" aria-label="从蓝色到金色的上行旋律">
        <defs>
          <linearGradient id="staffGradient" x1="0" x2="1">
            <stop offset="0" stopColor="#37b8ff" />
            <stop offset="0.52" stopColor="#9a74ff" />
            <stop offset="1" stopColor="#ffc75f" />
          </linearGradient>
          <filter id="noteGlow" x="-100%" y="-100%" width="300%" height="300%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>
        {[48, 61, 74, 87, 100].map((y) => <line key={y} x1="24" y1={y} x2="610" y2={y} className="staff-line" />)}
        <text x="25" y="98" className="clef">𝄞</text>
        <text x="73" y="72" className="signature">4</text>
        <text x="73" y="91" className="signature">4</text>
        <path d="M112 110 C 180 86, 222 64, 282 74 S 386 100, 438 69 S 532 49, 594 55" className="melody-curve" />
        {[
          [130, 104], [168, 91], [205, 77], [246, 67], [289, 79], [334, 91], [378, 83], [422, 70], [468, 65], [514, 51], [560, 60], [594, 48],
        ].map(([x, y], index) => (
          <g key={index} className="staff-note" filter="url(#noteGlow)">
            <ellipse cx={x} cy={y} rx="8" ry="5.5" />
            <line x1={x + 7} y1={y} x2={x + 7} y2={y - 29} />
          </g>
        ))}
      </svg>
    </div>
  )
}

function PianoKeyboard({ activeMidi }: { activeMidi: number | null }) {
  return (
    <div className="piano-keyboard" aria-label="钢琴键盘">
      {pianoKeys.map((label, index) => {
        const isBlack = [1, 3, 6, 8, 10].includes(index % 12)
        const isActive = activeMidi !== null && index === activeMidi - 48
        return (
          <div
            key={`${label}-${index}`}
            className={`piano-key ${isBlack ? 'black' : 'white'} ${isActive ? 'active' : ''}`}
            aria-hidden="true"
          >
            {!isBlack && label ? <span>{label}</span> : null}
          </div>
        )
      })}
    </div>
  )
}

export function MelodyPanel({ progress, currentSeconds, composition }: { progress: number; currentSeconds: number; composition: CompositionDto | null }) {
  const generatedNotes = composition?.tracks[0]?.notes ?? []
  const activeGeneratedNote = generatedNotes.reduce<MusicNoteDto | null>(
    (current, note) => note.startSeconds <= currentSeconds ? note : current,
    generatedNotes[0] ?? null,
  )
  const fallbackActive = melodyNotes.reduce((current, note) => (
    note.start <= progress && note.start + note.duration >= progress ? note : current
  ), melodyNotes[0])
  const duration = Math.max(composition?.durationSeconds ?? 0, 0.001)
  const rollNotes: Array<MusicNoteDto & { tone: 'blue' | 'violet' | 'gold' }> = generatedNotes.map((note, index) => ({
    ...note,
    tone: index / Math.max(1, generatedNotes.length - 1) > 0.68 ? 'gold' : index / Math.max(1, generatedNotes.length - 1) > 0.34 ? 'violet' : 'blue',
  }))
  const currentMotif = composition?.motifs.find((motif) => motif.id === activeGeneratedNote?.motifId)
  const musicalMode = composition ? `${composition.settings.musicalKey} ${composition.settings.scale}` : '待生成'

  return (
    <Panel
      title="旋律可视化"
      className="melody-panel"
      action={<span className="mapping-strength">映射强度 <b>{Math.round((composition?.settings.mappingStrength ?? 0.88) * 100)}%</b><i><em /></i></span>}
    >
      <div className="mode-row">
        <span>当前调式 · <b>{musicalMode}</b></span>
        <span className="motif-chip"><Sparkles size={13} /> {currentMotif?.label ?? '等待生成'}</span>
      </div>
      <StaffMelody />

      <div className="piano-roll">
        <div className="pitch-labels">
          <span>C5</span><span>C4</span><span>C3</span>
        </div>
        <div className="note-grid">
          <div className="beat-grid" />
          {(rollNotes.length ? rollNotes : melodyNotes.map((note) => ({
            id: String(note.id), trackId: 'mock', midi: 56 - note.pitch, pitchName: '',
            startSeconds: note.start, durationSeconds: note.duration, velocity: 80,
            candleIndex: note.id - 1, motifId: 'mock', tone: note.tone,
          }))).map((note) => (
            <i
              key={note.id}
              className={`roll-note ${note.tone} ${String(note.id) === String(activeGeneratedNote?.id ?? fallbackActive.id) ? 'active' : ''}`}
              style={{
                left: `${composition ? note.startSeconds / duration * 100 : note.startSeconds}%`,
                width: `${composition ? Math.max(0.7, note.durationSeconds / duration * 100) : note.durationSeconds}%`,
                top: `${8 + (84 - note.midi) / 36 * 72}%`,
              }}
            />
          ))}
          <div className="playhead" style={{ left: `${progress}%` }}>
            <span />
          </div>
          <div className="roll-times">
            <span>00:34</span><span>00:36</span><span>00:38</span><span>00:40</span><span>00:42</span><span>00:44</span>
          </div>
        </div>
      </div>
      <PianoKeyboard activeMidi={activeGeneratedNote?.midi ?? null} />
      <div className="sync-badge" aria-live="polite"><Music2 size={18} /><span>{composition ? '播放同步中' : '等待生成'}</span><Info size={12} /></div>
    </Panel>
  )
}
