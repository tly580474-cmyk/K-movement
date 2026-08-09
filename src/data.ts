export interface Candle {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface MelodyNote {
  id: number
  start: number
  duration: number
  pitch: number
  tone: 'blue' | 'violet' | 'gold'
}

export interface Motif {
  id: number
  label: string
  bars: string
  title: string
  description: string
  color: 'mint' | 'blue' | 'violet' | 'gold'
  values: number[]
}

const closes = [
  184, 181, 183, 178, 176, 179, 174, 169, 172, 168, 166, 171, 174, 176, 173,
  175, 178, 181, 184, 180, 178, 176, 179, 183, 185, 181, 178, 180, 177, 176,
  174, 178, 182, 185, 181, 184, 187, 190, 188, 191, 194, 198, 195, 191, 188,
  192, 190, 194, 191, 193.42,
]

export const candles: Candle[] = closes.map((close, index) => {
  const previous = index === 0 ? close - 1.6 : closes[index - 1]
  const open = previous + Math.sin(index * 1.7) * 1.9
  const spread = 1.6 + Math.abs(Math.sin(index * 0.83)) * 2.2
  return {
    date: `07-${String(index + 1).padStart(2, '0')}`,
    open,
    close,
    high: Math.max(open, close) + spread,
    low: Math.min(open, close) - spread * 0.82,
    volume: 28 + Math.abs(Math.cos(index * 0.71)) * 44 + (index % 9 === 0 ? 22 : 0),
  }
})

export const melodyNotes: MelodyNote[] = [
  { id: 1, start: 2, duration: 4, pitch: 6, tone: 'blue' },
  { id: 2, start: 7, duration: 3, pitch: 5, tone: 'blue' },
  { id: 3, start: 11, duration: 4, pitch: 4, tone: 'blue' },
  { id: 4, start: 16, duration: 3, pitch: 5, tone: 'blue' },
  { id: 5, start: 20, duration: 4, pitch: 3, tone: 'blue' },
  { id: 6, start: 25, duration: 4, pitch: 4, tone: 'blue' },
  { id: 7, start: 30, duration: 3, pitch: 2, tone: 'violet' },
  { id: 8, start: 34, duration: 5, pitch: 3, tone: 'violet' },
  { id: 9, start: 40, duration: 3, pitch: 5, tone: 'violet' },
  { id: 10, start: 44, duration: 4, pitch: 4, tone: 'violet' },
  { id: 11, start: 49, duration: 6, pitch: 3, tone: 'violet' },
  { id: 12, start: 56, duration: 4, pitch: 4, tone: 'blue' },
  { id: 13, start: 61, duration: 6, pitch: 4, tone: 'blue' },
  { id: 14, start: 68, duration: 4, pitch: 7, tone: 'gold' },
  { id: 15, start: 73, duration: 4, pitch: 6, tone: 'gold' },
  { id: 16, start: 78, duration: 5, pitch: 5, tone: 'gold' },
  { id: 17, start: 84, duration: 4, pitch: 4, tone: 'blue' },
  { id: 18, start: 89, duration: 5, pitch: 3, tone: 'blue' },
]

export const motifs: Motif[] = [
  {
    id: 0,
    label: '引子',
    bars: '0–8 小节',
    title: '平稳起步',
    description: '平稳上升',
    color: 'mint',
    values: [20, 26, 25, 34, 39, 36, 47, 53, 51, 61, 66, 74],
  },
  {
    id: 1,
    label: '动机 #32',
    bars: '8–16 小节',
    title: '突破上行',
    description: '强势突破',
    color: 'blue',
    values: [22, 24, 30, 28, 39, 43, 47, 56, 54, 67, 71, 79],
  },
  {
    id: 2,
    label: '动机 #33',
    bars: '16–24 小节',
    title: '震荡整理',
    description: '缓盘蓄势',
    color: 'violet',
    values: [44, 39, 45, 41, 49, 46, 51, 45, 54, 52, 57, 61],
  },
  {
    id: 3,
    label: '动机 #34',
    bars: '24–32 小节',
    title: 'V 型反转',
    description: '蓄力反转',
    color: 'gold',
    values: [58, 51, 42, 34, 27, 33, 39, 48, 55, 62, 70, 77],
  },
  {
    id: 4,
    label: '动机 #35',
    bars: '32–40 小节',
    title: '加速上攻',
    description: '动能增强',
    color: 'gold',
    values: [21, 24, 31, 29, 39, 44, 48, 55, 62, 68, 73, 82],
  },
]

export const pianoKeys = ['C3', '', 'D3', '', 'E3', 'F3', '', 'G3', '', 'A3', '', 'B3', 'C4', '', 'D4', '', 'E4', 'F4', '', 'G4', '', 'A4', '', 'B4', 'C5']
