import { useEffect, useMemo, useRef, useState } from 'react'
import { AppHeader } from './components/AppHeader'
import { Inspector, StructurePanel } from './components/Inspector'
import { MarketChart } from './components/MarketChart'
import { MelodyPanel } from './components/MelodyPanel'
import { MotifTimeline } from './components/MotifTimeline'
import { Sidebar } from './components/Sidebar'
import { TransportBar } from './components/TransportBar'
import { candles as mockCandles } from './data'
import { CompositionAudioPlayer } from './services/audioPlayer'
import { mockAssets } from './services/mockApi'
import { createComposition, downloadCompositionMidi, getCandles } from './services/marketApi'
import type { CandleDto, CandleSeriesResponse, CompositionDto, DateRange, GenerationSettings } from './types/api'

const defaultSettings: GenerationSettings = {
  style: 'orchestral',
  instruments: ['piano', 'strings', 'bass'],
  bpm: 96,
  musicalKey: 'C',
  scale: 'major-pentatonic',
  mood: 'upward',
  mappingStrength: 0.88,
}

function App() {
  const player = useRef(new CompositionAudioPlayer())
  const [playing, setPlaying] = useState(false)
  const [progress, setProgress] = useState(0)
  const [currentSeconds, setCurrentSeconds] = useState(0)
  const [volume, setVolume] = useState(72)
  const [settings, setSettings] = useState<GenerationSettings>(defaultSettings)
  const [generating, setGenerating] = useState(false)
  const [generationError, setGenerationError] = useState('')
  const [playbackError, setPlaybackError] = useState('')
  const [exporting, setExporting] = useState(false)
  const [composition, setComposition] = useState<CompositionDto | null>(null)
  const [asset, setAsset] = useState(mockAssets[0])
  const [dateRange, setDateRange] = useState<DateRange>({ startDate: '2026-04-01', endDate: '2026-08-07' })
  const [series, setSeries] = useState<CandleSeriesResponse | null>(null)
  const [marketLoading, setMarketLoading] = useState(true)
  const [marketError, setMarketError] = useState('')

  useEffect(() => {
    const controller = new AbortController()
    setMarketLoading(true)
    setMarketError('')
    getCandles(asset, dateRange, controller.signal)
      .then((response) => {
        setSeries(response)
        setAsset((current) => current.assetId === response.asset.assetId ? response.asset : current)
      })
      .catch((reason: unknown) => {
        if (!(reason instanceof DOMException && reason.name === 'AbortError')) {
          setMarketError(reason instanceof Error ? reason.message : '行情加载失败')
          setSeries(null)
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setMarketLoading(false)
      })
    return () => controller.abort()
  }, [asset.assetId, dateRange.startDate, dateRange.endDate])

  useEffect(() => {
    if (!playing || !composition) return
    let frame = 0
    const update = () => {
      const seconds = Math.min(player.current.currentSeconds, composition.durationSeconds)
      setCurrentSeconds(seconds)
      setProgress(composition.durationSeconds ? seconds / composition.durationSeconds * 100 : 0)
      frame = window.requestAnimationFrame(update)
    }
    frame = window.requestAnimationFrame(update)
    return () => window.cancelAnimationFrame(frame)
  }, [playing, composition])

  useEffect(() => () => player.current.dispose(), [])

  const fallbackCandles = useMemo<CandleDto[]>(() => mockCandles.map((candle) => ({ ...candle, volume: candle.volume, amount: null })), [])
  const chartCandles = series?.items.length ? series.items : fallbackCandles
  const notes = composition?.tracks[0]?.notes ?? []
  const activeNote = notes.reduce<(typeof notes)[number] | null>(
    (current, note) => note.startSeconds <= currentSeconds ? note : current,
    null,
  )
  const activeCandle = activeNote?.candleIndex ?? Math.min(chartCandles.length - 1, Math.floor((progress / 100) * chartCandles.length))
  const activeMotif = composition?.motifs.reduce(
    (current, motif, index) => motif.startSeconds <= currentSeconds ? index : current,
    0,
  ) ?? 0

  const stopPlayback = () => {
    player.current.pause()
    setPlaying(false)
  }

  const handleGenerate = async () => {
    if (!series?.items.length || marketLoading || marketError) return
    stopPlayback()
    setGenerating(true)
    setGenerationError('')
    setPlaybackError('')
    try {
      const generated = await createComposition({
        assetId: asset.assetId,
        startDate: dateRange.startDate,
        endDate: dateRange.endDate,
        settings,
      })
      const audioResult = await player.current.load(generated, () => {
        player.current.pause()
        setPlaying(false)
        setCurrentSeconds(generated.durationSeconds)
        setProgress(100)
      })
      player.current.setVolume(volume)
      if (!audioResult.sampledPiano) setPlaybackError('钢琴采样加载失败，已切换为本地柔和音色')
      setComposition(generated)
      setCurrentSeconds(0)
      setProgress(0)
    } catch (reason) {
      setGenerationError(reason instanceof Error ? reason.message : '乐章生成失败')
    } finally {
      setGenerating(false)
    }
  }

  const handleTogglePlayback = async () => {
    if (!composition) return
    setPlaybackError('')
    if (playing) {
      stopPlayback()
      return
    }
    try {
      if (progress >= 99.9) {
        player.current.seek(0)
        setCurrentSeconds(0)
        setProgress(0)
      }
      await player.current.play()
      setPlaying(true)
    } catch (reason) {
      setPlaybackError(reason instanceof Error ? reason.message : '音频初始化失败')
    }
  }

  const handleSeek = (nextProgress: number) => {
    const clamped = Math.max(0, Math.min(100, nextProgress))
    const seconds = composition ? composition.durationSeconds * clamped / 100 : 0
    player.current.seek(seconds)
    setCurrentSeconds(seconds)
    setProgress(clamped)
  }

  const handleMotifSelect = (index: number) => {
    const motif = composition?.motifs[index]
    if (!motif || !composition) return
    handleSeek(motif.startSeconds / composition.durationSeconds * 100)
  }

  const handleAssetChange = (nextAsset: typeof asset) => {
    stopPlayback()
    player.current.dispose()
    setComposition(null)
    setAsset(nextAsset)
    setProgress(0)
    setCurrentSeconds(0)
    if (nextAsset.lastDataDate && dateRange.endDate > nextAsset.lastDataDate) {
      setDateRange((current) => ({ ...current, endDate: nextAsset.lastDataDate! }))
    }
  }

  const handleDateRangeChange = (range: DateRange) => {
    stopPlayback()
    player.current.dispose()
    setComposition(null)
    setProgress(0)
    setCurrentSeconds(0)
    setDateRange(range)
  }

  const handleExport = async () => {
    if (!composition) return
    setExporting(true)
    setPlaybackError('')
    try {
      await downloadCompositionMidi(composition)
    } catch (reason) {
      setPlaybackError(reason instanceof Error ? reason.message : 'MIDI 导出失败')
    } finally {
      setExporting(false)
    }
  }

  const handleVolumeChange = (value: number) => {
    setVolume(value)
    player.current.setVolume(value)
  }

  return (
    <div className="app-shell">
      <div className="ambient ambient--one" />
      <div className="ambient ambient--two" />
      <Sidebar />
      <AppHeader onExport={handleExport} exportDisabled={!composition || exporting} exporting={exporting} />
      <main className="dashboard">
        <div className="workspace-grid">
          <MarketChart
            activeIndex={activeCandle}
            asset={asset}
            onAssetChange={handleAssetChange}
            dateRange={dateRange}
            onDateRangeChange={handleDateRangeChange}
            candles={chartCandles}
            indicators={series?.indicators ?? []}
            loading={marketLoading}
            error={marketError}
            warnings={series?.warnings ?? []}
          />
          <MelodyPanel progress={progress} currentSeconds={currentSeconds} composition={composition} />
          <Inspector
            asset={asset}
            analysis={series?.analysis ?? null}
            latestCandle={series?.items.at(-1) ?? null}
            warnings={series?.warnings ?? []}
            settings={settings}
            onSettingsChange={(patch) => setSettings((current) => ({ ...current, ...patch }))}
            onGenerate={handleGenerate}
            generating={generating}
            generationError={generationError}
            canGenerate={Boolean(series?.items.length && !marketLoading && !marketError)}
          />
        </div>
        <TransportBar
          playing={playing}
          onToggle={handleTogglePlayback}
          progress={progress}
          setProgress={handleSeek}
          bpm={composition?.settings.bpm ?? settings.bpm}
          musicalKey={composition ? `${composition.settings.musicalKey} ${composition.settings.scale}` : `${settings.musicalKey} ${settings.scale}`}
          asset={asset}
          dateRange={dateRange}
          composition={composition}
          playbackError={playbackError}
          volume={volume}
          onVolumeChange={handleVolumeChange}
        />
        <div className="bottom-grid">
          <MotifTimeline activeMotif={activeMotif} onSelect={handleMotifSelect} motifs={composition?.motifs ?? []} />
          <StructurePanel composition={composition} activeMotif={activeMotif} />
        </div>
        <p className="disclaimer">金融数据听觉化实验 · 音乐映射结果不构成投资建议</p>
      </main>
    </div>
  )
}

export default App
