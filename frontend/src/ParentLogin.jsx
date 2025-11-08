import React, { useEffect, useState } from 'react'
import * as api from './api'
import { setParentToken } from './auth'

export default function ParentLogin({ onLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [status, setStatus] = useState('')

  useEffect(() => {
    const existingToken = localStorage.getItem('parent_token')
    if (!existingToken) return

    let cancelled = false

    const verify = async () => {
      setStatus('Sprawdzanie sesji...')
      try {
        await api.parentGetCampaigns(existingToken)
        if (!cancelled) {
          setStatus('')
          onLogin && onLogin()
        }
      } catch (err) {
        if (!cancelled) {
          setStatus('Sesja wygasła, zaloguj się ponownie')
          localStorage.removeItem('parent_token')
        }
      }
    }

    verify()

    return () => {
      cancelled = true
    }
  }, [onLogin])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setStatus('Logowanie...')
    try {
      const res = await api.parentLogin(email, password)
      const token = res.token
      setParentToken(token)
      
      // Sprawdź czy wymagana zmiana hasła
      if (res.require_password_change) {
        setStatus('')
        window.location.hash = '#/parent/change-password'
        return
      }
      
      setStatus('')
      onLogin && onLogin()
    } catch (err) {
      setStatus('Błąd logowania: ' + (err && err.message ? err.message : String(err)))
    }
  }

  return (
    <div className="card">
      <h3 className="panel-title">Logowanie rodzica</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <label className="form-label">Email</label>
          <input className="input" value={email} onChange={e=>setEmail(e.target.value)} />
        </div>
        <div className="form-row">
          <label className="form-label">Hasło</label>
          <input className="input" type="password" value={password} onChange={e=>setPassword(e.target.value)} />
        </div>
        <button className="btn btn-primary" type="submit">Zaloguj</button>
      </form>
      <div>{status}</div>
    </div>
  )
}
