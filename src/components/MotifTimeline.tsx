import { ChevronRight, Music2, Play } from 'lucide-react'
import type { MarketMotifDto } from '../types/api'
import { Panel } from './Panel'

interface MotifTimelineProps {
  activeMotif: number
  onSelect: (index: number) => void
  motifs: MarketMotifDto[]
}

function SparkChart({ values }: { values: number[] }) {
  const points = values.map((value, index) => `${index * 12},${80 - value * 0.7}`).join(' ')
  return (
    <svg viewBox="0 0 132 72" preserveAspectRatio="none" aria-hidden="true">
      <polyline points={points} />
    </svg>
  )
}

export function MotifTimeline({ activeMotif, onSelect, motifs }: MotifTimelineProps) {
  return (
    <Panel title="市场动机 / 小节列表" className="motif-section">
      <div className="motif-list">
        {motifs.length ? motifs.map((motif, index) => (
          <button
            key={motif.id}
            className={`motif-card ${motif.color} ${index === activeMotif ? 'active' : ''}`}
            onClick={() => onSelect(index)}
            aria-pressed={index === activeMotif}
          >
            <div className="motif-card__label"><b>{motif.label}</b><span>/ K{motif.startCandleIndex + 1}–K{motif.endCandleIndex + 1}</span><ChevronRight size={14} /></div>
            <strong>{motif.title}</strong><small>{motif.description}</small>
            <SparkChart values={motif.values} />
            {index === activeMotif ? <i className="motif-play"><Play size={14} fill="currentColor" /></i> : null}
          </button>
        )) : <div className="motif-empty"><Music2 size={24} /><span>生成乐章后展示市场动机</span></div>}
      </div>
    </Panel>
  )
}
