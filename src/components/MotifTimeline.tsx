import { ChevronRight, Play, Plus } from 'lucide-react'
import { motifs } from '../data'
import { Panel } from './Panel'

interface MotifTimelineProps {
  activeMotif: number
  onSelect: (index: number) => void
}

function SparkChart({ values }: { values: number[] }) {
  const points = values.map((value, index) => `${index * 12},${80 - value * 0.7}`).join(' ')
  return (
    <svg viewBox="0 0 132 72" preserveAspectRatio="none" aria-hidden="true">
      <polyline points={points} />
    </svg>
  )
}

export function MotifTimeline({ activeMotif, onSelect }: MotifTimelineProps) {
  return (
    <Panel title="市场动机 / 小节列表" className="motif-section">
      <div className="motif-list">
        {motifs.map((motif, index) => (
          <button
            key={motif.id}
            className={`motif-card ${motif.color} ${index === activeMotif ? 'active' : ''}`}
            onClick={() => onSelect(index)}
            aria-pressed={index === activeMotif}
          >
            <div className="motif-card__label"><b>{motif.label}</b><span>/ {motif.bars}</span><ChevronRight size={14} /></div>
            <strong>{motif.title}</strong><small>{motif.description}</small>
            <SparkChart values={motif.values} />
            {index === activeMotif ? <i className="motif-play"><Play size={14} fill="currentColor" /></i> : null}
          </button>
        ))}
        <button className="add-motif"><Plus size={28} /><span>添加动机</span></button>
      </div>
    </Panel>
  )
}
