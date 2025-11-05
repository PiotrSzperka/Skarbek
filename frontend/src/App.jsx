import React, { useEffect, useState } from 'react'
import Admin from './Admin'
import ParentLogin from './ParentLogin'
import ParentDashboard from './ParentDashboard'
import * as api from './api'

function parseHash() {
  const h = (window.location.hash || '#/').replace(/^#/, '')
  if (h.startsWith('/admin')) return 'admin'
  if (h.startsWith('/parent/login')) return 'parent_login'
  if (h.startsWith('/parent/dashboard')) return 'parent_dashboard'
  return 'home'
}

export default function App() {
  const [campaigns, setCampaigns] = useState([])
  const [route, setRoute] = useState(parseHash)

  useEffect(() => {
    if (route === 'home') {
      api.listCampaigns().then(setCampaigns).catch(() => setCampaigns([]))
    }

    function onHash() {
      setRoute(parseHash())
    }
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [route])

  const navigate = (path) => { window.location.hash = path }

  if (route === 'admin') {
    return <Admin onLogout={() => navigate('/')} />
  }

  if (route === 'parent_login') {
    return <ParentLogin onLogin={() => navigate('/parent/dashboard')} />
  }

  if (route === 'parent_dashboard') {
    return <ParentDashboard onLogout={() => navigate('/parent/login')} />
  }

  return (
    <div className="container">
      <header className="header">
        <h1>Skarbek</h1>
        <p>Wsparcie zbiórek klasowych dla rodziców i skarbników.</p>
      </header>

      <section style={{ marginBottom: 32 }}>
        <h2>Aktywne zbiórki</h2>
        {campaigns.length === 0 ? (
          <p>Brak aktywnych zbiórek.</p>
        ) : (
          <ul className="campaign-list">
            {campaigns.map(c => (
              <li key={c.id}>{c.title} — Kwota: {c.target_amount}</li>
            ))}
          </ul>
        )}
      </section>

      <section className="grid">
        <div className="col card">
          <h3 className="panel-title">Panel rodzica</h3>
          <p>Podgląd zbiórek, zgłaszanie wpłat oraz historia płatności.</p>
          <button className="btn btn-primary" onClick={() => navigate('/parent/login')}>Przejdź do panelu rodzica</button>
        </div>
        <div className="col card">
          <h3 className="panel-title">Panel skarbnika</h3>
          <p>Zarządzanie zbiórkami i kontami rodziców.</p>
          <button className="btn btn-ghost" onClick={() => navigate('/admin')}>Przejdź do panelu skarbnika</button>
        </div>
      </section>
    </div>
  )
}
