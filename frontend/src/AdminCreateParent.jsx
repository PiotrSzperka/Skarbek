import React, { useState } from 'react'
import * as api from './api'

export default function AdminCreateParent({ adminToken }){
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
      // show error message to help debugging
      setStatus('Błąd: ' + (err && err.message ? err.message : String(err)))
    }
  }

  return (
    <div>
      <h3>Utwórz rodzica</h3>
      <form onSubmit={handleSubmit}>
        <div><label>Imię</label><input value={name} onChange={e=>setName(e.target.value)} /></div>
        <div><label>Email</label><input value={email} onChange={e=>setEmail(e.target.value)} /></div>
        <div><label>Hasło tymczasowe</label><input value={password} onChange={e=>setPassword(e.target.value)} /></div>
        <button type="submit">Utwórz</button>
      </form>
      <div>{status}</div>
    </div>
  )
}
