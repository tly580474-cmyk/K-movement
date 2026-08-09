import { useEffect, useMemo, useState } from 'react'
import { AppHeader } from './components/AppHeader'
import { Inspector, StructurePanel } from './components/Inspector'
import { MarketChart } from './components/MarketChart'
import { MelodyPanel } from './components/MelodyPanel'
import { MotifTimeline } from './components/MotifTimeline'
import { Sidebar } from './components/Sidebar'
import { TransportBar } from './components/TransportBar'
import { candles } from './data'
import { mockAssets } from './services/mockApi'
import type { DateRange } from './types/api'

function App() {
  const [playing, setPlaying] = useState(false)
  const [progress, setProgress] = useState(42)
  const [bpm, setBpm] = useState(96)
  const [musicalKey, setMusicalKey] = useState('C Major')
  const [style, setStyle] = useState('交响乐')
  const [generating, setGenerating] = useState(false)
  const [asset, setAsset] = useState(mockAssets[0])
  const [dateRange, setDateRange] = useState<DateRange>({ startDate: '2026-04-01', endDate: '2026-08-07' })

  useEffect(() => {
    if (!playing) return
    const timer = window.setInterval(() => {
      setProgress((current) => {
        if (current >= 100) {
          setPlaying(false)
          return 100
        }
        return current + 0.22
      })
    }, 250)
    return () => window.clearInterval(timer)
  }, [playing])

  const activeCandle = useMemo(
    () => Math.min(candles.length - 1, Math.floor((progress / 100) * candles.length)),
    [progress],
  )
  const activeMotif = Math.min(4, Math.floor(progress / 20))

  const handleGenerate = () => {
    setGenerating(true)
    setPlaying(false)
    window.setTimeout(() => {
      setProgress(0)
      setGenerating(false)
    }, 1100)
  }

  const handleMotifSelect = (index: number) => setProgress(index * 20 + 2)
  const handleAssetChange = (nextAsset: typeof asset) => {
    setAsset(nextAsset)
    setProgress(0)
    setPlaying(false)
    if (nextAsset.lastDataDate && dateRange.endDate > nextAsset.lastDataDate) {
      setDateRange((current) => ({ ...current, endDate: nextAsset.lastDataDate! }))
    }
  }

  return (
    <div className="app-shell">
      <div className="ambient ambient--one" />
      <div className="ambient ambient--two" />
      <Sidebar />
      <AppHeader />
      <main className="dashboard">
        <div className="workspace-grid">
          <MarketChart activeIndex={activeCandle} asset={asset} onAssetChange={handleAssetChange} dateRange={dateRange} onDateRangeChange={setDateRange} />
          <MelodyPanel progress={progress} />
          <Inspector
            asset={asset}
            bpm={bpm}
            setBpm={setBpm}
            musicalKey={musicalKey}
            setMusicalKey={setMusicalKey}
            style={style}
            setStyle={setStyle}
            onGenerate={handleGenerate}
            generating={generating}
          />
        </div>
        <TransportBar playing={playing} onToggle={() => setPlaying((value) => !value)} progress={progress} setProgress={setProgress} bpm={bpm} musicalKey={musicalKey} asset={asset} dateRange={dateRange} />
        <div className="bottom-grid">
          <MotifTimeline activeMotif={activeMotif} onSelect={handleMotifSelect} />
          <StructurePanel />
        </div>
        <p className="disclaimer">金融数据听觉化实验 · 展示数据为 Mock 示例 · 不构成投资建议</p>
      </main>
    </div>
  )
}

export default App
