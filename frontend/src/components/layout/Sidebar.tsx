import { NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Home, FolderOpen, Settings } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAbout } from '@/hooks/useAbout'

const items = [
  { to: '/', icon: Home, key: 'nav.home', end: true },
  { to: '/projects', icon: FolderOpen, key: 'nav.projects', end: false },
  { to: '/settings', icon: Settings, key: 'nav.settings', end: false },
]

export function Sidebar() {
  const { t } = useTranslation()
  const { data: about } = useAbout()

  return (
    <aside
      className="w-56 border-e flex flex-col p-3"
      style={{
        backgroundColor: 'rgb(var(--color-surface))',
        borderColor: 'rgb(var(--color-border))',
      }}
    >
      {/* Navigation items */}
      <nav className="flex flex-col gap-1">
        {items.map(({ to, icon: Icon, key, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                isActive
                  ? 'text-white'
                  : 'hover:bg-[rgb(var(--color-surface-alt))]'
              )
            }
            style={({ isActive }) =>
              isActive
                ? { backgroundColor: 'rgb(var(--color-primary))' }
                : { color: 'rgb(var(--color-text))' }
            }
          >
            <Icon className="h-4 w-4" />
            <span>{t(key)}</span>
          </NavLink>
        ))}
      </nav>

      {/* Version badge — pinned to bottom */}
      <div
        className="mt-auto pt-3 border-t text-center text-xs"
        style={{
          borderColor: 'rgb(var(--color-border))',
          color: 'rgb(var(--color-text-muted))',
        }}
        title={t('about.version_tooltip')}
      >
        v{about?.version ?? '0.0.0'}
      </div>
    </aside>
  )
}