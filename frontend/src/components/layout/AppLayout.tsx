import { Outlet, useLocation } from 'react-router-dom'
import { Header } from './Header'
import { Sidebar } from './Sidebar'

export function AppLayout() {
  const location = useLocation()

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <div className="flex-1 flex">
        <Sidebar />
        <main className="flex-1 overflow-auto p-6">
          {/*
            key={location.pathname} forces React to remount the Outlet
            on every route change, which re-triggers the CSS animation.
          */}
          <div
            key={location.pathname}
            className="rg-anim-fade-in"
          >
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}