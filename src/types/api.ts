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

export interface ApiError {
  code: string
  message: string
  requestId?: string
}
