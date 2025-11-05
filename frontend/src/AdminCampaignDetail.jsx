import React, { useEffect, useState } from 'react'
import * as api from './api'

export default function AdminCampaignDetail({ campaign, token, onClose }) {
  const [rows, setRows] = useState([])
  const [status, setStatus] = useState('')

  useEffect(()=>{
    let mounted = true
    api.adminCampaignRoster(campaign.id, token).then(data=>{
      if(!mounted) return
      setRows(data.rows || [])
    }).catch(e=>{
      setStatus('Błąd ładowania rosteru')
    })
    return ()=> mounted = false
  }, [campaign.id, token])

  async function handleConfirm(row){
    // ensure contribution exists
    try{
      setStatus('Tworzenie/oznaczanie...')
      if(!row.contribution){
        await api.adminCreateContribution({ campaign_id: campaign.id, parent_id: row.parent_id, amount_expected: campaign.target_amount }, token)
      }
      // find contribution id by reloading roster
      const refreshed = await api.adminCampaignRoster(campaign.id, token)
      const r = refreshed.rows.find(x => x.parent_id === row.parent_id)
      if(!r || !r.contribution){
        setStatus('Nie udało się znaleźć rekordu wpłaty')
        return
      }
  await api.markContributionPaid({ campaign_id: campaign.id, parent_id: row.parent_id, amount: r.contribution.amount_expected }, token)
  // reload roster after marking as paid so UI shows updated status immediately
  const refreshedAfter = await api.adminCampaignRoster(campaign.id, token)
  setStatus('Oznaczono jako opłacone')
  setRows(refreshedAfter.rows)
    }catch(e){
      setStatus('Błąd: ' + (e && e.message ? e.message : String(e)))
    }
  }

  function statusLabel(statusRaw){
    if(!statusRaw) return 'brak'
    switch(statusRaw){
      case 'pending': return 'oczekuje'
      case 'paid': return 'opłacone'
      default: return statusRaw
    }
  }

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 className="panel-title">Zbiórka: {campaign.title} — Kwota: {campaign.target_amount}</h3>
        <div><button className="btn btn-ghost" onClick={onClose}>Powrót</button></div>
      </div>
      <div>{status}</div>
      <table className="contrib-table" style={{ width: '100%' }}>
        <thead>
          <tr><th>Rodzic</th><th>Email</th><th>Status</th><th>Akcje</th></tr>
        </thead>
        <tbody>
          {rows.map(row=> (
            <tr key={row.parent_id}>
              <td>{row.parent_name}</td>
              <td>{row.parent_email}</td>
              <td>{row.contribution ? statusLabel(row.contribution.status) : 'brak'}</td>
              <td>{row.contribution && row.contribution.status === 'paid' ? <em>Opłacone</em> : <button className="btn btn-primary" onClick={()=>handleConfirm(row)}>Potwierdź wpłatę</button>}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
