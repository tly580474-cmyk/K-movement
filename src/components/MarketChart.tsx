import { Maximize2, SlidersHorizontal } from 'lucide-react'
import { candles } from '../data'
import type { AssetSummary, DateRange } from '../types/api'
import { AssetSelector } from './AssetSelector'
import { DateRangeControl } from './DateRangeControl'
import { Panel } from './Panel'

const WIDTH = 680
const HEIGHT = 278
const PADDING = { top: 18, right: 46, bottom: 24, left: 8 }
const minPrice = Math.min(...candles.map((item) => item.low)) - 2
const maxPrice = Math.max(...candles.map((item) => item.high)) + 2
const chartWidth = WIDTH - PADDING.left - PADDING.right
const chartHeight = HEIGHT - PADDING.top - PADDING.bottom

const yFor = (value: number) =>
  PADDING.top + ((maxPrice - value) / (maxPrice - minPrice)) * chartHeight

const xFor = (index: number) => PADDING.left + (index / candles.length) * chartWidth + 5

function averageAt(index: number, window: number) {
  const start = Math.max(0, index - window + 1)
  const values = candles.slice(start, index + 1)
  return values.reduce((total, candle) => total + candle.close, 0) / values.length
}

function linePath(window: number) {
  return candles
    .map((_, index) => `${index === 0 ? 'M' : 'L'} ${xFor(index)} ${yFor(averageAt(index, window))}`)
    .join(' ')
}

function MiniIndicators() {
  const rsiPath = Array.from({ length: 42 }, (_, index) => {
    const x = 8 + index * 7.5
    const y = 38 + Math.sin(index * 0.58) * 13 + Math.cos(index * 0.19) * 6
    return `${index === 0 ? 'M' : 'L'} ${x} ${y}`
  }).join(' ')

  const macdPath = Array.from({ length: 42 }, (_, index) => {
    const x = 8 + index * 7.5
    const y = 45 - Math.sin(index * 0.28 - 1) * 17
    return `${index === 0 ? 'M' : 'L'} ${x} ${y}`
  }).join(' ')

  return (
    <div className="indicator-row">
      <div className="mini-indicator">
        <div className="mini-indicator__label">RSI(14) <b>62.35</b></div>
        <svg viewBox="0 0 330 78" role="img" aria-label="RSI 指标示意图">
          <line x1="0" y1="22" x2="330" y2="22" />
          <line x1="0" y1="58" x2="330" y2="58" />
          <path d={rsiPath} className="rsi-line" />
        </svg>
      </div>
      <div className="mini-indicator">
        <div className="mini-indicator__label">MACD(12,26,9) <b className="gold">DIF 2.35</b></div>
        <svg viewBox="0 0 330 78" role="img" aria-label="MACD 指标示意图">
          <line x1="0" y1="42" x2="330" y2="42" />
          {Array.from({ length: 30 }, (_, index) => {
            const value = Math.sin(index * 0.33 - 1.8) * 16
            return (
              <rect
                key={index}
                x={index * 11 + 3}
                y={value > 0 ? 42 - value : 42}
                width="6"
                height={Math.abs(value)}
                className={value > 0 ? 'macd-up' : 'macd-down'}
              />
            )
          })}
          <path d={macdPath} className="macd-line" />
        </svg>
      </div>
    </div>
  )
}

interface MarketChartProps {
  activeIndex: number
  asset: AssetSummary
  onAssetChange: (asset: AssetSummary) => void
  dateRange: DateRange
  onDateRangeChange: (range: DateRange) => void
}

export function MarketChart({ activeIndex, asset, onAssetChange, dateRange, onDateRangeChange }: MarketChartProps) {
  const candleWidth = Math.max(4, chartWidth / candles.length - 4)
  const active = Math.min(candles.length - 1, activeIndex)

  return (
    <Panel
      title="K线图表"
      className="market-panel"
      action={
        <button className="icon-button compact" aria-label="放大 K 线图">
          <Maximize2 size={15} />
        </button>
      }
    >
      <div className="chart-toolbar">
        <AssetSelector value={asset} onChange={onAssetChange} />
        <div className="timeframes" aria-label="K线周期">
          {['1分', '5分', '15分', '1小时', '日K', '周K', '月K'].map((item) => (
            <button key={item} className={item === '日K' ? 'active' : ''}>{item}</button>
          ))}
        </div>
        <DateRangeControl value={dateRange} onChange={onDateRangeChange} />
        <button className="icon-button compact" aria-label="图表设置"><SlidersHorizontal size={15} /></button>
      </div>

      <div className="ma-legend" aria-label="移动平均线图例">
        <span className="pink">MA5: 192.35</span>
        <span className="gold">MA10: 189.21</span>
        <span className="violet">MA20: 186.34</span>
        <span className="blue">MA60: 177.98</span>
      </div>

      <div className="candle-chart">
        <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label={`${asset.name}日 K 线 Mock 图表`}>
          <defs>
            <filter id="activeGlow" x="-100%" y="-100%" width="300%" height="300%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
          </defs>
          {[0, 1, 2, 3, 4].map((line) => {
            const y = PADDING.top + (line / 4) * chartHeight
            const price = maxPrice - (line / 4) * (maxPrice - minPrice)
            return (
              <g key={line}>
                <line x1="0" y1={y} x2={WIDTH - 40} y2={y} className="grid-line" />
                <text x={WIDTH - 34} y={y + 4} className="axis-text">{price.toFixed(0)}.00</text>
              </g>
            )
          })}
          {candles.map((candle, index) => {
            const x = xFor(index)
            const rising = candle.close >= candle.open
            const top = yFor(Math.max(candle.open, candle.close))
            const bottom = yFor(Math.min(candle.open, candle.close))
            const isActive = index === active
            return (
              <g key={candle.date} className={rising ? 'candle rising' : 'candle falling'}>
                {isActive ? <rect x={x - 7} y="4" width={candleWidth + 14} height={HEIGHT - 32} className="active-candle-band" /> : null}
                <line x1={x + candleWidth / 2} y1={yFor(candle.high)} x2={x + candleWidth / 2} y2={yFor(candle.low)} />
                <rect
                  x={x}
                  y={top}
                  width={candleWidth}
                  height={Math.max(2, bottom - top)}
                  filter={isActive ? 'url(#activeGlow)' : undefined}
                />
              </g>
            )
          })}
          <path d={linePath(5)} className="ma-line ma-five" />
          <path d={linePath(10)} className="ma-line ma-ten" />
          <path d={linePath(20)} className="ma-line ma-twenty" />
          <line x1="0" y1={yFor(193.42)} x2={WIDTH - 42} y2={yFor(193.42)} className="price-line" />
          <rect x={WIDTH - 46} y={yFor(193.42) - 11} width="45" height="21" rx="5" className="price-tag" />
          <text x={WIDTH - 42} y={yFor(193.42) + 4} className="price-tag-text">193.42</text>
        </svg>
      </div>

      <div className="volume-chart">
        <div className="volume-label">成交量(Vol) <b>63.25M</b></div>
        {candles.map((candle) => (
          <i
            key={candle.date}
            className={candle.close >= candle.open ? 'up' : 'down'}
            style={{ height: `${Math.max(14, candle.volume)}%` }}
          />
        ))}
      </div>
      <MiniIndicators />
    </Panel>
  )
}
