import { Heart, Pause, Play, RotateCcw, SkipBack, SkipForward, Volume2 } from 'lucide-react'
import type { AssetSummary, CompositionDto, DateRange } from '../types/api'

interface TransportBarProps {
  playing: boolean
  onToggle: () => void
  progress: number
  setProgress: (value: number) => void
  bpm: number
  musicalKey: string
  asset: AssetSummary
  dateRange: DateRange
  composition: CompositionDto | null
  playbackError: string
  volume: number
  onVolumeChange: (value: number) => void
}

export function TransportBar({ playing, onToggle, progress, setProgress, bpm, musicalKey, asset, dateRange, composition, playbackError, volume, onVolumeChange }: TransportBarProps) {
  const totalSeconds = composition?.durationSeconds ?? 0
  const currentSeconds = Math.round((progress / 100) * totalSeconds)
  const formatTime = (seconds: number) => `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`
  const jump = totalSeconds ? Math.max(1, 240 / bpm) / totalSeconds * 100 : 0

  return (
    <section className="transport" aria-label="乐章播放器">
      <div className="track-meta">
        <div className="cover-art"><span>♫</span><i /></div>
        <div><h2>{composition ? '市场乐章' : '尚未生成'} <span>#{composition?.id.slice(0, 8) ?? dateRange.endDate}</span></h2><p>{asset.name} · 日K · {dateRange.startDate}～{dateRange.endDate}</p>{playbackError ? <small className="playback-error" role="alert">{playbackError}</small> : null}</div>
        <button className="icon-button" aria-label="收藏乐章"><Heart size={17} /></button>
      </div>
      <div className="transport__center">
        <div className="transport-buttons">
          <button aria-label="返回开头" onClick={() => setProgress(0)} disabled={!composition}><RotateCcw size={15} /></button>
          <button aria-label="上一小节" onClick={() => setProgress(Math.max(0, progress - jump))} disabled={!composition}><SkipBack size={17} /></button>
          <button className="primary" aria-label={playing ? '暂停' : '播放'} onClick={onToggle} disabled={!composition}>
            {playing ? <Pause size={21} fill="currentColor" /> : <Play size={21} fill="currentColor" />}
          </button>
          <button aria-label="下一小节" onClick={() => setProgress(Math.min(100, progress + jump))} disabled={!composition}><SkipForward size={17} /></button>
        </div>
        <label className="progress-control">
          <span className="sr-only">播放进度</span>
          <input type="range" min="0" max="100" step="0.1" value={progress} disabled={!composition} onChange={(event) => setProgress(Number(event.target.value))} />
        </label>
      </div>
      <div className="playback-data">
        <span className="time-display">{formatTime(currentSeconds)} / {formatTime(Math.round(totalSeconds))}</span>
        <dl><div><dt>BPM</dt><dd>{bpm}</dd></div><div><dt>调式</dt><dd>{musicalKey}</dd></div><div><dt>拍号</dt><dd>4/4</dd></div></dl>
        <Volume2 size={17} />
        <input className="volume-control" aria-label="音量" type="range" min="0" max="100" value={volume} onChange={(event) => onVolumeChange(Number(event.target.value))} />
      </div>
    </section>
  )
}
