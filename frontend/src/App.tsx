import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, Route, Routes } from 'react-router-dom'
import { getHealth } from './api'

const upcoming = ['My Projects', 'New Architecture', 'Agent Runs', 'Settings']

function StatusCard({ kind, title }: { kind: 'live' | 'ready'; title: string }) {
  const health = useQuery({ queryKey: ['health', kind], queryFn: () => getHealth(kind) })
  const state = health.isPending ? 'Checking' : health.isError ? 'Unavailable' : 'Operational'

  return (
    <section className="status-card" aria-label={title}>
      <div className="card-topline">
        <span className={`status-dot ${health.isSuccess ? 'online' : health.isError ? 'offline' : ''}`} />
        <span>{state}</span>
      </div>
      <h3>{title}</h3>
      <p>
        {health.isPending
          ? 'Checking service status…'
          : health.isError
            ? health.error.message
            : kind === 'live'
              ? 'The API process is responding.'
              : 'PostgreSQL is accepting queries.'}
      </p>
      <button type="button" className="text-button" onClick={() => void health.refetch()}>
        Check again <span aria-hidden="true">↗</span>
      </button>
    </section>
  )
}

function Dashboard() {
  return (
    <>
      <div className="eyebrow">Workspace / Overview</div>
      <div className="hero">
        <div>
          <div className="phase-pill"><span className="pulse" /> Phase 1 · Foundation</div>
          <h1>Architect with clarity.</h1>
          <p className="hero-copy">
            A structured workspace for turning project ideas into explainable software designs.
            The foundation is in place; project generation is the next milestone.
          </p>
        </div>
        <div className="hero-mark" aria-hidden="true"><span>◇</span></div>
      </div>

      <div className="section-heading">
        <div>
          <div className="eyebrow">System status</div>
          <h2>Foundation checks</h2>
        </div>
        <span className="section-note">Live service signals</span>
      </div>
      <div className="status-grid">
        <StatusCard kind="live" title="API service" />
        <StatusCard kind="ready" title="Database connection" />
      </div>

      <div className="section-heading roadmap-heading">
        <div>
          <div className="eyebrow">Build path</div>
          <h2>Next milestone</h2>
        </div>
      </div>
      <div className="milestone-card">
        <span className="milestone-number">02</span>
        <div>
          <h3>Functional MVP</h3>
          <p>Project creation, requirements review, a deterministic mock workflow, and a saved architecture graph.</p>
        </div>
        <span className="milestone-tag">Planned</span>
      </div>
    </>
  )
}

function App() {
  const [dark, setDark] = useState(() => localStorage.getItem('theme') !== 'light')

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }, [dark])

  return (
    <div className="app-shell min-h-screen">
      <aside className="sidebar">
        <div className="brand"><div className="brand-symbol">◇</div><div>AI PROJECT<br /><strong>ARCHITECT</strong></div></div>
        <div className="nav-label">WORKSPACE</div>
        <nav aria-label="Main navigation">
          <Link to="/" className="nav-item selected"><span className="nav-icon">▦</span>Dashboard</Link>
          {upcoming.map((item) => (
            <span className="nav-item disabled" aria-disabled="true" key={item}>
              <span className="nav-icon">◇</span>{item}<small>Soon</small>
            </span>
          ))}
        </nav>
        <div className="sidebar-bottom"><span className="small-square">01</span><div>Foundation phase<br /><small>Local workspace</small></div></div>
      </aside>

      <div className="content-shell">
        <header className="topbar">
          <span>AI Project Architect <span className="topbar-divider">/</span> Dashboard</span>
          <button type="button" className="theme-button" onClick={() => setDark(!dark)} aria-label={`Use ${dark ? 'light' : 'dark'} theme`}>
            {dark ? '☼' : '☾'} <span>Theme</span>
          </button>
        </header>
        <main><Routes><Route path="*" element={<Dashboard />} /></Routes></main>
        <footer>Phase 1 foundation · No projects or AI results are generated yet.</footer>
      </div>
    </div>
  )
}

export default App
