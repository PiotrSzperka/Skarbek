import React, { useState } from 'react'
import * as api from './api'

export default function AdminCreateParentView({ adminToken, onBack }){
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [status, setStatus] = useState('')

  const handleSubmit = async (e)=>{
    e.preventDefault()
    setStatus('Tworzenie...')
    try{
      const res = await api.adminCreateParent({name, email, password}, adminToken)
      setStatus('Utworzono: ' + res.email)
      setName(''); setEmail(''); setPassword('')
    }catch(err){
      setStatus('Błąd: ' + (err && err.message ? err.message : String(err)))
    }
  }

  return (
    <div className="card">
      <button className="btn btn-ghost" onClick={onBack}>Powrót</button>
      <h3 className="panel-title">Utwórz rodzica</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <label className="form-label">Imię</label>
          <input className="input" value={name} onChange={e=>setName(e.target.value)} />
        </div>
        <div className="form-row">
          <label className="form-label">Email</label>
          <input className="input" value={email} onChange={e=>setEmail(e.target.value)} />
        </div>
        <div className="form-row">
          <label className="form-label">Hasło tymczasowe</label>
          <input className="input" value={password} onChange={e=>setPassword(e.target.value)} />
        </div>
        <button className="btn btn-primary" type="submit">Utwórz</button>
      </form>
      <div>{status}</div>
    </div>
  )
}
