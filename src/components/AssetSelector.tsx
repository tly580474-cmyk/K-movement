import { ChevronDown, LoaderCircle, Search, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { searchAssets } from '../services/marketApi'
import type { AssetSummary } from '../types/api'

interface AssetSelectorProps {
  value: AssetSummary
  onChange: (asset: AssetSummary) => void
}

const typeLabels = { stock: '股票', index: '指数', etf: 'ETF' }

export function AssetSelector({ value, onChange }: AssetSelectorProps) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [items, setItems] = useState<AssetSummary[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const rootRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!open) return
    let cancelled = false
    const controller = new AbortController()
    setLoading(true)
    setError('')
    searchAssets(query, controller.signal)
      .then((response) => {
        if (!cancelled) setItems(response.items)
      })
      .catch((reason: unknown) => {
        if (!cancelled && !(reason instanceof DOMException && reason.name === 'AbortError')) {
          setItems([])
          setError(reason instanceof Error ? reason.message : '标的搜索失败')
        }
      })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true; controller.abort() }
  }, [open, query])

  useEffect(() => {
    if (open) window.setTimeout(() => inputRef.current?.focus(), 0)
  }, [open])

  useEffect(() => {
    const closeOnOutsideClick = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', closeOnOutsideClick)
    return () => document.removeEventListener('mousedown', closeOnOutsideClick)
  }, [])

  const selectAsset = (asset: AssetSummary) => {
    onChange(asset)
    setOpen(false)
    setQuery('')
  }

  return (
    <div className="asset-selector" ref={rootRef} onKeyDown={(event) => event.key === 'Escape' && setOpen(false)}>
      <button className="asset-select" aria-haspopup="listbox" aria-expanded={open} onClick={() => setOpen((current) => !current)}>
        <span><b>{value.symbol}</b> · {value.name}</span>
        <ChevronDown size={14} />
      </button>
      {open ? (
        <div className="asset-popover">
          <label className="asset-search">
            <Search size={15} />
            <span className="sr-only">搜索股票或指数</span>
            <input ref={inputRef} value={query} onChange={(event) => setQuery(event.target.value)} placeholder="代码或名称" />
            {query ? <button type="button" onClick={() => setQuery('')} aria-label="清除搜索"><X size={14} /></button> : null}
          </label>
          <div className="asset-results" role="listbox" aria-label="标的搜索结果">
            {loading ? <div className="asset-state"><LoaderCircle size={16} className="spinning" /> 搜索中…</div> : null}
            {!loading && error ? <div className="asset-state error">{error}</div> : null}
            {!loading && !error && items.length === 0 ? <div className="asset-state">没有匹配的股票或指数</div> : null}
            {!loading && items.map((asset) => (
              <button key={asset.assetId} role="option" aria-selected={asset.assetId === value.assetId} onClick={() => selectAsset(asset)}>
                <span className="asset-result__main"><b>{asset.symbol}</b><em>{asset.name}</em></span>
                <span className="asset-result__meta">{asset.market} · {typeLabels[asset.assetType]}</span>
              </button>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  )
}
