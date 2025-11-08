import React, { useState } from 'react'
import { parentChangePasswordInitial } from './api'

export default function ParentForcePasswordChange() {
  const [oldPassword, setOldPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    // Walidacja klienta
    if (!oldPassword || !newPassword || !confirmPassword) {
      setError('Wszystkie pola są wymagane')
      return
    }

    if (newPassword.length < 6) {
      setError('Nowe hasło musi mieć min. 6 znaków')
      return
    }

    if (newPassword === oldPassword) {
      setError('Nowe hasło musi być inne niż stare')
      return
    }

    if (newPassword !== confirmPassword) {
      setError('Nowe hasła nie pasują do siebie')
      return
    }

    setLoading(true)
    try {
      const token = localStorage.getItem('parent_token')
      const response = await parentChangePasswordInitial(oldPassword, newPassword, token)
      
      // Nadpisz token nowym
      localStorage.setItem('parent_token', response.token)
      
      // Redirect do dashboardu
      window.location.href = '/parent/dashboard'
    } catch (err) {
      setError(err.message || 'Błąd podczas zmiany hasła')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 400, margin: '50px auto', padding: 20, border: '1px solid #ccc', borderRadius: 8 }}>
      <h2>Wymagana zmiana hasła</h2>
      <p style={{ color: '#666', fontSize: 14 }}>
        Ze względów bezpieczeństwa musisz zmienić swoje tymczasowe hasło przed kontynuowaniem.
      </p>
      
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: 15 }}>
          <label style={{ display: 'block', marginBottom: 5 }}>Stare hasło:</label>
          <input
            type="password"
            value={oldPassword}
            onChange={(e) => setOldPassword(e.target.value)}
            style={{ width: '100%', padding: 8, fontSize: 14 }}
            disabled={loading}
          />
        </div>

        <div style={{ marginBottom: 15 }}>
          <label style={{ display: 'block', marginBottom: 5 }}>Nowe hasło:</label>
          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            style={{ width: '100%', padding: 8, fontSize: 14 }}
            disabled={loading}
          />
        </div>

        <div style={{ marginBottom: 15 }}>
          <label style={{ display: 'block', marginBottom: 5 }}>Powtórz nowe hasło:</label>
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            style={{ width: '100%', padding: 8, fontSize: 14 }}
            disabled={loading}
          />
        </div>

        {error && (
          <div style={{ padding: 10, marginBottom: 15, backgroundColor: '#fee', color: '#c00', borderRadius: 4 }}>
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          style={{
            width: '100%',
            padding: 10,
            fontSize: 16,
            backgroundColor: '#007bff',
            color: '#fff',
            border: 'none',
            borderRadius: 4,
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Zmiana...' : 'Zmień hasło'}
        </button>
      </form>
    </div>
  )
}
