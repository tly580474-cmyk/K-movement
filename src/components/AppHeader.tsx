import { CircleHelp, Download, Settings, Share2, User } from 'lucide-react'

export function AppHeader() {
  return (
    <header className="app-header">
      <div className="musical-wave left"><i /><i /><i /></div>
      <div className="title-lockup"><span>♪</span><div><h1>K 线 乐 章</h1><p>让 市 场 奏 响 旋 律</p></div><span>♫</span></div>
      <div className="musical-wave right"><i /><i /><i /></div>
      <div className="header-actions">
        <button><Download size={16} /> 导出音乐</button>
        <button><Share2 size={16} /> 分享</button>
        <button className="icon-button" aria-label="设置"><Settings size={18} /></button>
        <button className="icon-button" aria-label="帮助"><CircleHelp size={18} /></button>
        <button className="avatar" aria-label="用户账户"><User size={18} /></button>
      </div>
    </header>
  )
}
