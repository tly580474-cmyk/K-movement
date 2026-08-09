import { CalendarDays, ChevronDown } from 'lucide-react'
import { useRef, useState } from 'react'
import type { DateRange } from '../types/api'

interface DateRangeControlProps {
  value: DateRange
  onChange: (value: DateRange) => void
}

const shortDate = (value: string) => value.slice(5).replace('-', '/')

export function DateRangeControl({ value, onChange }: DateRangeControlProps) {
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState(value)
  const rootRef = useRef<HTMLDivElement>(null)
  const startInputRef = useRef<HTMLInputElement>(null)
  const endInputRef = useRef<HTMLInputElement>(null)

  const apply = () => {
    const nextRange = {
      startDate: startInputRef.current?.value ?? draft.startDate,
      endDate: endInputRef.current?.value ?? draft.endDate,
    }
    if (nextRange.startDate <= nextRange.endDate) {
      onChange(nextRange)
      setOpen(false)
    }
  }

  return (
    <div className="date-range" ref={rootRef} onKeyDown={(event) => event.key === 'Escape' && setOpen(false)}>
      <button className="date-range__trigger" aria-haspopup="dialog" aria-expanded={open} onClick={() => { setDraft(value); setOpen((current) => !current) }}>
        <CalendarDays size={14} /><span>{shortDate(value.startDate)}–{shortDate(value.endDate)}</span><ChevronDown size={12} />
      </button>
      {open ? (
        <div className="date-popover" role="dialog" aria-label="选择行情日期范围">
          <label>开始日期<input ref={startInputRef} type="date" value={draft.startDate} max={draft.endDate} onChange={(event) => setDraft((current) => ({ ...current, startDate: event.target.value }))} /></label>
          <label>结束日期<input ref={endInputRef} type="date" value={draft.endDate} min={draft.startDate} onChange={(event) => setDraft((current) => ({ ...current, endDate: event.target.value }))} /></label>
          <div className="date-popover__actions"><button onClick={() => setOpen(false)}>取消</button><button className="apply" onClick={apply}>应用范围</button></div>
        </div>
      ) : null}
    </div>
  )
}
