import { getMockCandles, searchAssets as searchMockAssets } from './mockApi'
import type { AssetSearchResponse, AssetSummary, CandleSeriesResponse, CompositionCreateRequest, CompositionDto, DateRange } from '../types/api'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
export const useMockApi = import.meta.env.VITE_USE_MOCK_API === 'true'

export class MarketApiError extends Error {
  constructor(
    message: string,
    readonly status: number | null = null,
    readonly code = 'NETWORK_ERROR',
  ) {
    super(message)
    this.name = 'MarketApiError'
  }
}

async function request<T>(path: string, signal?: AbortSignal, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      signal,
      headers: { Accept: 'application/json', ...init?.headers },
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    throw new MarketApiError('无法连接行情服务，请确认 FastAPI 已启动')
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => null) as { error?: { code?: string; message?: string } } | null
    throw new MarketApiError(
      payload?.error?.message || `行情服务返回 ${response.status}`,
      response.status,
      payload?.error?.code,
    )
  }
  return response.json() as Promise<T>
}

export async function createComposition(payload: CompositionCreateRequest): Promise<CompositionDto> {
  return request<CompositionDto>('/api/compositions', undefined, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function downloadCompositionMidi(composition: CompositionDto): Promise<void> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}/api/compositions/${composition.id}/midi`)
  } catch {
    throw new MarketApiError('无法连接音乐导出服务')
  }
  if (!response.ok) throw new MarketApiError('MIDI 导出失败', response.status, 'MIDI_EXPORT_FAILED')
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `kline-melody-${composition.asset.symbol}-${composition.id}.mid`
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}

export async function searchAssets(query: string, signal?: AbortSignal): Promise<AssetSearchResponse> {
  if (useMockApi) return searchMockAssets(query)
  const params = new URLSearchParams({ query, limit: '20' })
  return request<AssetSearchResponse>(`/api/assets?${params}`, signal)
}

export async function getCandles(
  asset: AssetSummary,
  range: DateRange,
  signal?: AbortSignal,
): Promise<CandleSeriesResponse> {
  if (useMockApi) return getMockCandles(asset, range)
  const params = new URLSearchParams({ start: range.startDate, end: range.endDate, timeframe: '1d' })
  return request<CandleSeriesResponse>(
    `/api/assets/${encodeURIComponent(asset.assetId)}/candles?${params}`,
    signal,
  )
}
