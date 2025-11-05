import React, { useState } from 'react'
import * as api from './api'

export default function AdminCreateCampaignView({ adminToken, onBack, onCreated }){
  const [title, setTitle] = useState('')
  const [target, setTarget] = useState(0)
  const [status, setStatus] = useState('')

  const handleSubmit = async (e)=>{
    e.preventDefault()
    setStatus('Tworzenie...')
    try{
      await api.createCampaign({ title, target_amount: Number(target) }, adminToken)
      setStatus('Utworzono')
      setTitle(''); setTarget(0)
      onCreated && onCreated()
    }catch(err){
      setStatus('Błąd: ' + (err && err.message ? err.message : String(err)))
    }
  }

  return (
    <div className="card">
      <button className="btn btn-ghost" onClick={onBack}>Powrót</button>
      <h3 className="panel-title">Utwórz zbiórkę</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <label className="form-label">Tytuł</label>
          <input className="input" value={title} onChange={e=>setTitle(e.target.value)} required />
        </div>
        <div className="form-row">
          <label className="form-label">Kwota docelowa (zł)</label>
          <input className="input" type="number" value={target} onChange={e=>setTarget(e.target.value)} required />
        </div>
        <button className="btn btn-primary" type="submit">Utwórz</button>
      </form>
      <div>{status}</div>
    </div>
  )
}
