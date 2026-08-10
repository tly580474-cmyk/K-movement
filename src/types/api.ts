export type AssetType = 'stock' | 'index' | 'etf'
export type MarketCode = 'SH' | 'SZ' | 'BJ' | 'GLOBAL'

export interface AssetSummary {
  assetId: string
  sourceId: string
  market: MarketCode
  symbol: string
  name: string
  assetType: AssetType
  status: 'active' | 'delisted'
  lastDataDate: string | null
  lastPrice: number
  currency: 'CNY' | 'POINT'
  change: number
  changePercent: number
}

export interface AssetSearchResponse {
  items: AssetSummary[]
  total: number
}

export interface DateRange {
  startDate: string
  endDate: string
}

export interface CandleDto {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number | null
  amount: number | null
}

export interface IndicatorPoint {
  date: string
  returnPct: number | null
  ma5: number | null
  ma10: number | null
  ma20: number | null
  ma60: number | null
  rsi14: number | null
  macd: number | null
  macdSignal: number | null
  macdHistogram: number | null
  atr14: number | null
  relativeVolume20: number | null
}

export interface MarketAnalysis {
  trendState: 'bullish' | 'bearish' | 'sideways' | 'unknown'
  volatility20: number | null
  latestRsi14: number | null
  latestMacd: number | null
  latestAtr14: number | null
  latestMa20: number | null
  latestMa60: number | null
}

export interface CandleSeriesResponse {
  asset: AssetSummary
  timeframe: '1d'
  requestedStartDate: string
  requestedEndDate: string
  actualStartDate: string | null
  actualEndDate: string | null
  items: CandleDto[]
  indicators: IndicatorPoint[]
  analysis: MarketAnalysis | null
  warnings: string[]
}

export interface ApiError {
  code: string
  message: string
  requestId?: string
}

export type MusicStyle =
  | 'orchestral'
  | 'piano'
  | 'synth'
  | 'lofi'
  | 'jazz-lounge'
  | 'cinematic-epic'
  | 'chinese-folk'
  | 'ambient-minimal'
  | 'pop-rock'
export type MusicScale = 'major-pentatonic' | 'minor-pentatonic' | 'major' | 'minor'
export type MusicMood = 'upward' | 'calm' | 'tense' | 'dark'

export interface GenerationSettings {
  style: MusicStyle
  instruments: string[]
  bpm: number
  musicalKey: 'C' | 'A' | 'G' | 'D'
  scale: MusicScale
  mood: MusicMood
  mappingStrength: number
}

export interface CompositionCreateRequest {
  assetId: string
  startDate: string
  endDate: string
  settings: GenerationSettings
}

export interface MusicNoteDto {
  id: string
  trackId: string
  midi: number
  pitchName: string
  startSeconds: number
  durationSeconds: number
  velocity: number
  candleIndex: number
  motifId: string
}

export interface MusicTrackDto {
  id: string
  name: string
  instrument: string
  notes: MusicNoteDto[]
}

export interface MarketMotifDto {
  id: string
  label: string
  startCandleIndex: number
  endCandleIndex: number
  startSeconds: number
  endSeconds: number
  title: string
  description: string
  color: 'mint' | 'blue' | 'violet' | 'gold'
  values: number[]
}

export interface CompositionDto {
  id: string
  asset: AssetSummary
  startDate: string
  endDate: string
  settings: GenerationSettings
  timeSignature: '4/4'
  durationSeconds: number
  totalBars: number
  tracks: MusicTrackDto[]
  motifs: MarketMotifDto[]
  warnings: string[]
}
