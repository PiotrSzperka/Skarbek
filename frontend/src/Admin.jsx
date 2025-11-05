import React, { useEffect, useState } from 'react'
import * as api from './api'
import AdminCreateParentView from './AdminCreateParentView'
import AdminCreateCampaignView from './AdminCreateCampaignView'
import AdminParentsView from './AdminParentsView'
import AdminCampaignDetail from './AdminCampaignDetail'
import { setAdminToken, clearTokens } from './auth'

export default function Admin({ onLogout }) {
  const [token, setToken] = useState(null)
  const [user, setUser] = useState(null)
  const [campaigns, setCampaigns] = useState([])
  const [loginForm, setLoginForm] = useState({ username: '', password: '' })
  const [status, setStatus] = useState(null)

  useEffect(() => {
    api.listCampaigns().then(setCampaigns).catch(() => setCampaigns([]))
  }, [token])

  const [contribsByCampaign, setContribsByCampaign] = useState([])
  const [showPaidCampaigns, setShowPaidCampaigns] = useState(false)
  const [parents, setParents] = useState([])
  const [view, setView] = useState('list') // list | create-parent | create-campaign
  const [expandedCampaignIds, setExpandedCampaignIds] = useState(new Set())

  useEffect(() => {
    if (!token) return
    let mounted = true
    api.adminListContributions(token).then(data => {
      if (!mounted) return
      setContribsByCampaign(data)
    }).catch(() => setContribsByCampaign([]))
    // also load parents to calculate fallback unpaid counts
    api.adminListParents(token).then(p => { if (mounted) setParents(p) }).catch(() => setParents([]))
    return () => { mounted = false }
  }, [token])

  // initialize token from localStorage so admin remains logged in across reloads
  useEffect(() => {
    try {
      const t = localStorage.getItem('admin_token')
      if (t) {
        setToken(t)
        setUser('admin')
      }
    } catch (e) {}
  }, [])

  async function handleLogin(e) {
    e.preventDefault()
    setStatus('Logging in...')
    try {
      const res = await api.adminLogin(loginForm.username, loginForm.password)
      setToken(res.token)  // Fix: use 'token' not 'access_token'
      setAdminToken(res.token)
      setUser(loginForm.username)
      setStatus('Zalogowano')
      } catch (err) {
      setStatus('Błąd logowania: ' + err.message)
    }
  }

  function handleLogout() {
    clearTokens()
    setToken(null)
    setUser(null)
    setStatus('Wylogowano')
    if (typeof onLogout === 'function') {
      onLogout()
    }
  }

  

  async function handleMarkPaid(campaignId) {
    const parentEmail = prompt('Email rodzica, którego wpłata chcesz oznaczyć jako opłaconą:')
    if (!parentEmail) return
    const payload = { campaign_id: campaignId, parent_email: parentEmail }
    setStatus('Oznaczanie...')
    try {
      await api.markContributionPaid(payload, token)
      setStatus('Oznaczono jako opłacone')
    } catch (err) {
      setStatus('Błąd: ' + err.message)
    }
  }

  return (
    <div className="top-right">
      {token && (
        <div className="logout">
          <button className="btn btn-ghost" onClick={handleLogout}>Wyloguj</button>
        </div>
      )}
      <h2>Panel skarbnika</h2>
      {!token ? (
        <form onSubmit={handleLogin} style={{ maxWidth: 400 }}>
          <div className="form-row">
            <label className="form-label">Nazwa użytkownika</label>
            <input className="input" value={loginForm.username} onChange={e => setLoginForm({ ...loginForm, username: e.target.value })} />
          </div>
          <div className="form-row">
            <label className="form-label">Hasło</label>
            <input className="input" type="password" value={loginForm.password} onChange={e => setLoginForm({ ...loginForm, password: e.target.value })} />
          </div>
          <button className="btn btn-primary" type="submit">Zaloguj</button>
        </form>
      ) : (
        <div>
          <p>Użytkownik: <strong>{user}</strong></p>

          <section style={{ marginTop: 16 }}>
            <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
              <button className="btn btn-primary" onClick={() => setView('create-parent')}>Utwórz rodzica</button>
              <button className="btn btn-primary" onClick={() => setView('create-campaign')}>Utwórz zbiórkę</button>
              <button className="btn btn-primary" onClick={() => setView('parents')}>Zarządzaj rodzicami</button>
            </div>
            {view === 'create-parent' && <AdminCreateParentView adminToken={token} onBack={() => setView('list')} />}
            {view === 'create-campaign' && <AdminCreateCampaignView adminToken={token} onBack={() => setView('list')} onCreated={async ()=>{ const updated = await api.listCampaigns(); setCampaigns(updated); setView('list')}} />}
            {view === 'parents' && <AdminParentsView adminToken={token} />}
          </section>

          

          <section style={{ marginTop: 16 }}>
            <h3>Lista zbiórek</h3>
            <label style={{ display: 'block', marginBottom: 8 }}>
              <input type="checkbox" checked={showPaidCampaigns} onChange={e => setShowPaidCampaigns(e.target.checked)} /> Pokaż opłacone
            </label>
            {contribsByCampaign.length === 0 ? <p>Brak</p> : (
              <div>
                {contribsByCampaign.filter(group => {
                  if (showPaidCampaigns) return true
                  const contribs = group.contributions || []
                  const parentList = parents || []
                  let allPaid = false
                  if (parentList.length > 0) {
                    const paidByParent = new Set(contribs.filter(c => c.status === 'paid').map(c => c.parent_id))
                    allPaid = parentList.every(p => paidByParent.has(p.id))
                    // debug
                    try { console.debug('[ADMIN DBG] filter campaign', group.campaign.id, 'parents', parentList.length, 'contribs', contribs.length, 'paidByParent', paidByParent.size, 'allPaid', allPaid) } catch (e) {}
                  } else {
                    // fallback to previous logic when we don't have parents list yet
                    allPaid = contribs.length > 0 && contribs.every(c => c.status === 'paid')
                  }
                  return !allPaid
                }).map(group => (
                  <div key={group.campaign.id} className="admin-campaign">
                    <h4>
                      {group.campaign.title} — Kwota: {group.campaign.target_amount}
                      {(() => {
                        const contribs = group.contributions || []
                        const parentList = parents || []
                        let unpaid = 0
                        if (parentList.length > 0) {
                          const paidByParent = new Set(contribs.filter(c => c.status === 'paid').map(c => c.parent_id))
                          unpaid = parentList.reduce((acc, p) => acc + (paidByParent.has(p.id) ? 0 : 1), 0)
                          try { console.debug('[ADMIN DBG] badge campaign', group.campaign.id, 'parents', parentList.length, 'contribs', contribs.length, 'paidByParent', paidByParent.size, 'unpaid', unpaid) } catch (e) {}
                        } else {
                          // fallback when parents list not loaded: count contributions that are not 'paid'
                          unpaid = contribs.filter(c => c.status !== 'paid').length
                        }
                        return unpaid > 0 ? <span className="badge badge-pending" style={{ marginLeft: 8 }}>{unpaid} nieopł.</span> : null
                      })()}
                    </h4>
                    <div style={{ marginTop: 8 }}>
                      <button className="btn btn-ghost" onClick={() => {
                        const ids = new Set(expandedCampaignIds)
                        if (ids.has(group.campaign.id)) ids.delete(group.campaign.id)
                        else ids.add(group.campaign.id)
                        setExpandedCampaignIds(ids)
                      }}>{expandedCampaignIds.has(group.campaign.id) ? 'Ukryj listę rodziców' : 'Zobacz listę rodziców'}</button>
                    </div>
                    {expandedCampaignIds.has(group.campaign.id) && (
                      <div style={{ marginTop: 8 }}>
                        <AdminCampaignDetail campaign={group.campaign} token={token} onClose={() => {
                          const ids = new Set(expandedCampaignIds); ids.delete(group.campaign.id); setExpandedCampaignIds(ids)
                        }} />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
            {/* details are rendered inline beneath each campaign when expanded */}
          </section>
        </div>
      )}

      {status && <p><em>{status}</em></p>}
    </div>
  )
}
