import React, { useEffect, useState } from 'react'
import api from './api'
import { clearTokens } from './auth'

export default function ParentDashboard() {
  const [campaigns, setCampaigns] = useState([])
  const [status, setStatus] = useState('')
  const [showPaid, setShowPaid] = useState(false)

  const token = localStorage.getItem('parent_token')
  const [confirmModal, setConfirmModal] = useState(null)

  useEffect(()=>{
    const load = async ()=>{
      setStatus('Ładowanie...')
      try{
        const res = await api.parentGetCampaigns(token)
        setCampaigns(res)
        setStatus('')
      }catch(e){
        setStatus('Błąd ładowania')
      }
    }
    load()
  }, [])

  const handleSubmit = async (campaignId)=>{
    // Always submit the full target amount for the campaign
    const item = campaigns.find(c => c.campaign.id === campaignId)
    if (!item) {
      alert('Nie znaleziono zbiórki')
      return
    }
    const amount = item.campaign.target_amount
    try{
      await api.parentSubmitContribution({campaign_id: campaignId, amount: Number(amount)}, token)
      // refresh list silently
      const res = await api.parentGetCampaigns(token)
      setCampaigns(res)
    }catch(e){
      // keep an inline alert to surface the error
      alert('Błąd')
    }
  }

  function statusLabel(statusRaw){
    if(!statusRaw) return 'brak wpłaty'
    switch(statusRaw){
      case 'pending': return 'oczekuje'
      case 'paid': return 'opłacone'
      default: return statusRaw
    }
  }

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 className="panel-title">Panel rodzica</h3>
        <div>
          <button className="btn btn-ghost" onClick={() => { clearTokens(); window.location = '/'; }}>Wyloguj</button>
        </div>
      </div>
      <div>{status}</div>
      <label style={{ display: 'block', marginBottom: 8 }}>
        <input type="checkbox" checked={showPaid} onChange={e => setShowPaid(e.target.checked)} /> Pokaż opłacone
      </label>
      <ul>
        {campaigns.filter(item => showPaid || !(item.contribution && item.contribution.status === 'paid')).map(item=> (
          <li key={item.campaign.id} className="admin-campaign">
            <strong>{item.campaign.title}</strong> - Kwota: {item.campaign.target_amount}
            {/* badge removed for parent view */}
            <div>Status: {item.contribution ? statusLabel(item.contribution.status) : 'brak wpłaty'}</div>
            <div>
              {item.contribution ? null : (
                <button className="btn btn-primary" onClick={()=>setConfirmModal(item.campaign.id)}>Zgłoś wpłatę</button>
              )}
            </div>
          </li>
        ))}
      </ul>

      {confirmModal && (() => {
        const sel = campaigns.find(c => c.campaign.id === confirmModal)
        const title = sel ? sel.campaign.title : ''
        return (
          <div role="dialog" aria-modal="true" style={{ position: 'fixed', left: 0, top: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999 }}>
            <div style={{ background: 'white', color: '#111', padding: 20, borderRadius: 6, maxWidth: 480, width: '90%' }}>
              <h4 style={{ margin: 0 }}>Potwierdź zgłoszenie wpłaty</h4>
              <p style={{ marginTop: 8 }}>Czy na pewno chcesz zgłosić wpłatę dla: <strong>{title}</strong>?</p>
              <div style={{ marginTop: 12 }}>
                <button className="btn btn-primary" onClick={async ()=>{ await handleSubmit(confirmModal); setConfirmModal(null) }}>Potwierdź</button>
                <button className="btn" style={{ marginLeft: 8 }} onClick={()=>setConfirmModal(null)}>Anuluj</button>
              </div>
            </div>
          </div>
        )
      })()}
    </div>
  )
}
