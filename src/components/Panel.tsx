import type { ReactNode } from 'react'

interface PanelProps {
  title?: string
  action?: ReactNode
  className?: string
  children: ReactNode
}

export function Panel({ title, action, className = '', children }: PanelProps) {
  return (
    <section className={`panel ${className}`}>
      {title ? (
        <header className="panel__header">
          <h2>{title}</h2>
          {action}
        </header>
      ) : null}
      {children}
    </section>
  )
}
