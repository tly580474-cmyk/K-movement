import { ChevronRight, RefreshCw, TrendingUp } from 'lucide-react'
import type { AssetSummary, CandleDto, CompositionDto, GenerationSettings, MarketAnalysis } from '../types/api'
import { Panel } from './Panel'

const styleInstrumentPresets: Record<GenerationSettings['style'], string[]> = {
  orchestral: ['piano', 'strings', 'bass'],
  piano: ['piano'],
  synth: ['synth', 'pad', 'bass'],
  lofi: ['electric-piano', 'pad', 'bass'],
  'jazz-lounge': ['electric-piano', 'brass', 'upright-bass'],
  'cinematic-epic': ['piano', 'strings', 'bass'],
  'chinese-folk': ['guzheng', 'erhu', 'bass'],
  'ambient-minimal': ['piano', 'pad', 'bass'],
  'pop-rock': ['electric-guitar', 'power-chord', 'bass'],
}

interface InspectorProps {
  asset: AssetSummary
  analysis: MarketAnalysis | null
  latestCandle: CandleDto | null
  warnings: string[]
  settings: GenerationSettings
  onSettingsChange: (patch: Partial<GenerationSettings>) => void
  onGenerate: () => void
  generating: boolean
  generationError: string
  canGenerate: boolean
}

export function Inspector({ asset, analysis, latestCandle, warnings, settings, onSettingsChange, onGenerate, generating, generationError, canGenerate }: InspectorProps) {
  const rising = asset.change >= 0
  const trendLabel = {
    bullish: 'Bullish',
    bearish: 'Bearish',
    sideways: 'Sideways',
    unknown: 'Unknown',
  }[analysis?.trendState ?? 'unknown']
  return (
    <aside className="inspector">
      <Panel title="市场信息" action={<ChevronRight size={16} />} className="market-summary">
        <div className="quote-title"><b>{asset.symbol}</b><span>{asset.name}</span></div>
        <div className={`quote-price ${rising ? '' : 'negative'}`}>{asset.lastPrice.toFixed(2)} <small>{asset.currency === 'POINT' ? '点' : asset.currency}</small></div>
        <div className={`quote-change ${rising ? '' : 'negative'}`}>{rising ? '+' : ''}{asset.change.toFixed(2)}&nbsp;&nbsp;{rising ? '+' : ''}{asset.changePercent.toFixed(2)}% <span>{asset.assetType === 'stock' ? '交易中' : '指数'}</span></div>
        <svg className="sparkline" viewBox="0 0 190 64" role="img" aria-label="当日价格上涨趋势">
          <defs><linearGradient id="sparkFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#20d9a3" stopOpacity=".3" /><stop offset="1" stopColor="#20d9a3" stopOpacity="0" /></linearGradient></defs>
          <path d="M2 56 L18 54 L29 47 L41 50 L52 40 L65 44 L77 35 L89 39 L101 28 L112 31 L124 18 L137 24 L149 13 L162 17 L176 8 L188 11 L188 64 L2 64 Z" fill="url(#sparkFill)" />
          <path d="M2 56 L18 54 L29 47 L41 50 L52 40 L65 44 L77 35 L89 39 L101 28 L112 31 L124 18 L137 24 L149 13 L162 17 L176 8 L188 11" />
        </svg>
        <dl className="stats-grid">
          <dt>开盘</dt><dd>{latestCandle?.open.toFixed(2) ?? '—'}</dd><dt>最高</dt><dd>{latestCandle?.high.toFixed(2) ?? '—'}</dd>
          <dt>最低</dt><dd>{latestCandle?.low.toFixed(2) ?? '—'}</dd><dt>成交量</dt><dd>{latestCandle?.volume == null ? '—' : `${(latestCandle.volume / 1_000_000).toFixed(2)}M`}</dd>
          <dt>成交额</dt><dd>{latestCandle?.amount == null ? '—' : `${(latestCandle.amount / 1_000_000_000).toFixed(2)}B`}</dd><dt>数据日</dt><dd>{asset.lastDataDate?.slice(5) ?? '未知'}</dd>
        </dl>
        <div className={`trend-state ${analysis?.trendState ?? 'unknown'}`}><span>趋势状态</span><b>{trendLabel}</b><TrendingUp size={18} /></div>
        <dl className="indicator-stats">
          <dt>波动率(20)</dt><dd>{analysis?.volatility20?.toFixed(2) ?? '—'}%</dd>
          <dt>RSI(14)</dt><dd>{analysis?.latestRsi14?.toFixed(2) ?? '—'}</dd>
          <dt>MACD</dt><dd>{analysis?.latestMacd?.toFixed(2) ?? '—'}</dd>
          <dt>ATR(14)</dt><dd>{analysis?.latestAtr14?.toFixed(2) ?? '—'}</dd>
        </dl>
        {warnings.length ? <div className="data-warning" title={warnings.join('；')}>{warnings[0]}</div> : null}
      </Panel>

      <Panel title="音乐生成参数" action={<ChevronRight size={16} />} className="generation-panel">
        <label>生成风格
          <select value={settings.style} onChange={(event) => {
            const style = event.target.value as GenerationSettings['style']
            onSettingsChange({ style, instruments: styleInstrumentPresets[style] })
          }}>
            <option value="orchestral">交响乐 (Orchestral)</option>
            <option value="piano">氛围钢琴 (Piano)</option>
            <option value="synth">电子合成 (Synth)</option>
            <option value="lofi">低保真 (Lo-fi)</option>
            <option value="jazz-lounge">轻爵士 (Jazz Lounge)</option>
            <option value="cinematic-epic">史诗影视风 (Cinematic Epic)</option>
            <option value="chinese-folk">国风新民乐 (Chinese Folk)</option>
            <option value="ambient-minimal">极简氛围 (Ambient Minimal)</option>
            <option value="pop-rock">摇滚律动 (Pop Rock)</option>
          </select>
        </label>
        <label>乐器编制
          <select value={settings.instruments.join(',')} onChange={(event) => onSettingsChange({ instruments: event.target.value.split(',') })}>
            <option value="piano,strings,bass">Piano + Strings + Bass</option>
            <option value="piano">Piano Solo</option>
            <option value="synth,bass,drums">Synth + Bass + Drums</option>
            <option value="synth,pad,bass">Synth + Pad + Bass</option>
            <option value="electric-piano,pad,bass">Electric Piano + Pad + Bass</option>
            <option value="electric-piano,brass,upright-bass">Electric Piano + Brass + Upright Bass</option>
            <option value="guzheng,erhu,bass">Guzheng + Erhu + Bass</option>
            <option value="electric-guitar,power-chord,bass">Electric Guitar + Power Chord + Bass</option>
          </select>
        </label>
        <label>BPM
          <input type="number" min="60" max="160" value={settings.bpm} onChange={(event) => onSettingsChange({ bpm: Number(event.target.value) })} />
        </label>
        <label>调式
          <select value={`${settings.musicalKey}:${settings.scale}`} onChange={(event) => {
            const [musicalKey, scale] = event.target.value.split(':') as [GenerationSettings['musicalKey'], GenerationSettings['scale']]
            onSettingsChange({ musicalKey, scale })
          }}>
            <option value="C:major-pentatonic">C Major Pentatonic</option><option value="A:minor-pentatonic">A Minor Pentatonic</option><option value="G:major">G Major</option><option value="D:minor">D Minor</option>
          </select>
        </label>
        <label>情感色彩
          <select value={settings.mood} onChange={(event) => onSettingsChange({ mood: event.target.value as GenerationSettings['mood'] })}><option value="upward">激昂 / 向上</option><option value="calm">平静 / 舒缓</option><option value="tense">紧张 / 波动</option><option value="dark">低沉 / 回落</option></select>
        </label>
        {generationError ? <div className="generation-error" role="alert" title={generationError}>{generationError}</div> : null}
        <button className="generate-button" onClick={onGenerate} disabled={generating || !canGenerate} aria-busy={generating}>
          <RefreshCw size={16} className={generating ? 'spinning' : ''} />
          {generating ? '生成乐章中…' : canGenerate ? '生成市场乐章' : '等待真实行情'}
        </button>
      </Panel>

    </aside>
  )
}

export function StructurePanel({ composition, activeMotif }: { composition: CompositionDto | null; activeMotif: number }) {
  const motif = composition?.motifs[activeMotif]
  const duration = composition?.durationSeconds ?? 0
  const formatTime = (seconds: number) => `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(Math.round(seconds % 60)).padStart(2, '0')}`
  return (
    <Panel title="乐章结构" className="structure-panel">
      <div className="structure-content">
        <dl><dt>编曲结构</dt><dd>{composition ? `${composition.tracks.length} 轨自动和声` : '尚未生成'}</dd><dt>总时长</dt><dd>{formatTime(duration)}</dd><dt>小节数</dt><dd>{composition?.totalBars ?? 0} 小节</dd><dt>当前片段</dt><dd>{motif?.label ?? '尚未生成'}</dd></dl>
        <div className="structure-ring"><span>♪</span><i /><b /><em /></div>
      </div>
    </Panel>
  )
}
