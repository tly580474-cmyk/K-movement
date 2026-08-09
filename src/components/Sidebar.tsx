import {
  BarChart3,
  BookOpen,
  Home,
  Library,
  Music2,
  Settings,
  Sparkles,
  Users,
} from 'lucide-react'

const navItems = [
  { label: '首页', icon: Home, active: true },
  { label: '市场', icon: BarChart3 },
  { label: '乐谱库', icon: Library },
  { label: '创作', icon: Music2 },
  { label: '社区', icon: Users },
  { label: '设置', icon: Settings },
]

export function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`brand ${compact ? 'compact' : ''}`}>
      <div className="brand__mark"><span>K</span><i /><b /></div>
      {!compact ? <><strong>K线乐章</strong><em>专业版</em></> : null}
    </div>
  )
}

export function Sidebar() {
  return (
    <aside className="sidebar">
      <Brand />
      <nav aria-label="主导航">
        {navItems.map(({ label, icon: Icon, active }) => (
          <button key={label} className={active ? 'active' : ''} aria-current={active ? 'page' : undefined}>
            <Icon size={19} strokeWidth={1.8} />
            <span>{label}</span>
            {!active && ['乐谱库', '社区'].includes(label) ? <i title="即将开放" /> : null}
          </button>
        ))}
      </nav>
      <div className="master-mode">
        <BookOpen size={17} />
        <span>大师模式</span>
        <button aria-label="切换大师模式" role="switch" aria-checked="true"><i /></button>
      </div>
      <div className="sidebar__ambient"><Sparkles size={14} /> Market Orchestra</div>
    </aside>
  )
}
