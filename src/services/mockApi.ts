import { candles } from '../data'
import type { AssetSearchResponse, AssetSummary, CandleSeriesResponse, DateRange } from '../types/api'

export const mockAssets: AssetSummary[] = [
  {
    assetId: 'stock:SH:600519',
    sourceId: '29',
    market: 'SH',
    symbol: '600519',
    name: '贵州茅台',
    assetType: 'stock',
    status: 'active',
    lastDataDate: '2026-08-07',
    lastPrice: 1309.22,
    currency: 'CNY',
    change: 0.67,
    changePercent: 0.05,
  },
  {
    assetId: 'index:dataset:932000',
    sourceId: '7de97d1e-3d0c-4102-9fd8-c85126568dec',
    market: 'SH',
    symbol: '932000',
    name: '中证2000',
    assetType: 'index',
    status: 'active',
    lastDataDate: '2026-08-05',
    lastPrice: 3000.29,
    currency: 'POINT',
    change: 79.5,
    changePercent: 2.72,
  },
  {
    assetId: 'index:dataset:000300',
    sourceId: '435e043c-41e7-407e-8a2f-ac97c800cddf',
    market: 'SH',
    symbol: '000300',
    name: '沪深300',
    assetType: 'index',
    status: 'active',
    lastDataDate: '2026-08-07',
    lastPrice: 4278.13,
    currency: 'POINT',
    change: 24.16,
    changePercent: 0.57,
  },
  {
    assetId: 'index:dataset:399006',
    sourceId: '3435cf2e-595a-4042-851e-67a288e458eb',
    market: 'SZ',
    symbol: '399006',
    name: '创业板指',
    assetType: 'index',
    status: 'active',
    lastDataDate: '2026-08-07',
    lastPrice: 2614.92,
    currency: 'POINT',
    change: -18.44,
    changePercent: -0.7,
  },
  {
    assetId: 'stock:SZ:000001',
    sourceId: '67',
    market: 'SZ',
    symbol: '000001',
    name: '平安银行',
    assetType: 'stock',
    status: 'active',
    lastDataDate: '2026-08-07',
    lastPrice: 12.38,
    currency: 'CNY',
    change: 0.16,
    changePercent: 1.31,
  },
  {
    assetId: 'index:dataset:000001',
    sourceId: '7c5031c8-eccd-4f21-bd5a-66a354d46231',
    market: 'SH',
    symbol: '000001',
    name: '上证指数',
    assetType: 'index',
    status: 'active',
    lastDataDate: '2026-08-07',
    lastPrice: 3642.21,
    currency: 'POINT',
    change: 18.33,
    changePercent: 0.51,
  },
]

const wait = (milliseconds: number) => new Promise((resolve) => window.setTimeout(resolve, milliseconds))

export async function searchAssets(query: string): Promise<AssetSearchResponse> {
  await wait(180)
  const keyword = query.trim().toLocaleLowerCase('zh-CN')
  const items = keyword
    ? mockAssets.filter((asset) =>
        [asset.symbol, asset.name, asset.market, asset.assetType]
          .some((field) => field.toLocaleLowerCase('zh-CN').includes(keyword)),
      )
    : mockAssets
  return { items, total: items.length }
}

export async function getMockCandles(asset: AssetSummary, range: DateRange): Promise<CandleSeriesResponse> {
  await wait(220)
  const items = candles.map((candle, index) => ({
    ...candle,
    date: new Date(Date.UTC(2026, 4, 1 + index)).toISOString().slice(0, 10),
    amount: candle.volume * candle.close * 10000,
  }))
  return {
    asset,
    timeframe: '1d',
    requestedStartDate: range.startDate,
    requestedEndDate: range.endDate,
    actualStartDate: items[0]?.date ?? null,
    actualEndDate: items.at(-1)?.date ?? null,
    items,
    indicators: [],
    analysis: {
      trendState: 'bullish',
      volatility20: 23.45,
      latestRsi14: 62.35,
      latestMacd: 2.35,
      latestAtr14: 3.12,
      latestMa20: 186.34,
      latestMa60: 177.98,
    },
    warnings: ['当前使用 Mock 行情数据'],
  }
}
