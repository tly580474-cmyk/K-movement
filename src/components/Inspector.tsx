import { ChevronRight, RefreshCw, TrendingUp } from 'lucide-react'
import type { AssetSummary } from '../types/api'
import { Panel } from './Panel'

interface InspectorProps {
  asset: AssetSummary
  bpm: number
  setBpm: (value: number) => void
  musicalKey: string
  setMusicalKey: (value: string) => void
  style: string
  setStyle: (value: string) => void
  onGenerate: () => void
  generating: boolean
}

export function Inspector({ asset, bpm, setBpm, musicalKey, setMusicalKey, style, setStyle, onGenerate, generating }: InspectorProps) {
  const rising = asset.change >= 0
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
          <dt>开盘</dt><dd>191.10</dd><dt>最高</dt><dd>194.02</dd>
          <dt>最低</dt><dd>190.48</dd><dt>成交量</dt><dd>63.25M</dd>
          <dt>成交额</dt><dd>12.19B</dd><dt>数据日</dt><dd>{asset.lastDataDate?.slice(5) ?? '未知'}</dd>
        </dl>
        <div className="trend-state"><span>趋势状态</span><b>Bullish</b><TrendingUp size={18} /></div>
        <dl className="indicator-stats">
          <dt>波动率(20)</dt><dd>23.45%</dd>
          <dt>RSI(14)</dt><dd>62.35</dd>
          <dt>MACD</dt><dd>2.35</dd>
          <dt>均线趋势</dt><dd>多头排列</dd>
        </dl>
      </Panel>

      <Panel title="音乐生成参数" action={<ChevronRight size={16} />} className="generation-panel">
        <label>生成风格
          <select value={style} onChange={(event) => setStyle(event.target.value)}>
            <option value="交响乐">交响乐 (Orchestral)</option>
            <option value="氛围钢琴">氛围钢琴 (Piano)</option>
            <option value="电子合成">电子合成 (Synth)</option>
          </select>
        </label>
        <label>乐器编制
          <select defaultValue="Piano + Strings + Bass">
            <option>Piano + Strings + Bass</option>
            <option>Piano Solo</option>
            <option>Synth + Bass + Drums</option>
          </select>
        </label>
        <label>BPM
          <input type="number" min="60" max="160" value={bpm} onChange={(event) => setBpm(Number(event.target.value))} />
        </label>
        <label>调式
          <select value={musicalKey} onChange={(event) => setMusicalKey(event.target.value)}>
            <option>C Major</option><option>A Minor</option><option>G Major</option><option>D Minor</option>
          </select>
        </label>
        <label>情感色彩
          <select defaultValue="激昂 / 向上"><option>激昂 / 向上</option><option>平静 / 舒缓</option><option>紧张 / 波动</option></select>
        </label>
        <button className="generate-button" onClick={onGenerate} disabled={generating}>
          <RefreshCw size={16} className={generating ? 'spinning' : ''} />
          {generating ? '生成乐章中…' : '重新生成'}
        </button>
      </Panel>

    </aside>
  )
}

export function StructurePanel() {
  return (
    <Panel title="乐章结构" className="structure-panel">
      <div className="structure-content">
        <dl><dt>结构类型</dt><dd>变奏曲式 (Rondo)</dd><dt>总时长</dt><dd>02:45</dd><dt>小节数</dt><dd>64小节</dd><dt>当前片段</dt><dd>动机 #32</dd></dl>
        <div className="structure-ring"><span>♪</span><i /><b /><em /></div>
      </div>
    </Panel>
  )
}
