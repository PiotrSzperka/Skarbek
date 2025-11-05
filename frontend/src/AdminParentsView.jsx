import React, { useEffect, useState } from 'react'
import * as api from './api'

export default function AdminParentsView({ adminToken }) {
  const [parents, setParents] = useState([])
  const [includeHidden, setIncludeHidden] = useState(false)
  const [status, setStatus] = useState(null)

  useEffect(() => {
    let mounted = true
    api.adminListParents(adminToken, includeHidden).then(data => {
      if (!mounted) return
      setParents(data)
    }).catch(err => { setParents([]); setStatus('Błąd pobierania: ' + err.message) })
    return () => { mounted = false }
  }, [adminToken, includeHidden])

  async function handleHide(parentId) {
    setStatus('Aktualizowanie...')
    try {
      await api.adminHideParent(parentId, adminToken)
      setStatus('Ukryto')
      const updated = await api.adminListParents(adminToken, includeHidden)
      setParents(updated)
    } catch (e) { setStatus('Błąd: ' + e.message) }
  }

  async function handleUnhide(parentId) {
    setStatus('Aktualizowanie...')
    try {
      await api.adminUnhideParent(parentId, adminToken)
      setStatus('Przywrócono')
      const updated = await api.adminListParents(adminToken, includeHidden)
      setParents(updated)
    } catch (e) { setStatus('Błąd: ' + e.message) }
  }

  return (
    <section style={{ marginTop: 16 }}>
      <h3>Lista rodziców</h3>
      <label style={{ display: 'block', marginBottom: 8 }}>
        <input type="checkbox" checked={includeHidden} onChange={e => setIncludeHidden(e.target.checked)} /> Pokaż ukrytych
      </label>
      {parents.length === 0 ? <p>Brak</p> : (
        <table className="parents-table">
          <thead>
            <tr><th>Imię</th><th>E-mail</th><th>Akcje</th></tr>
          </thead>
          <tbody>
            {parents.map(p => (
              <tr key={p.id}>
                <td>{p.name || ''}</td>
                <td>{p.email || ''}</td>
                <td>
                  {p.is_hidden ? (
                    <button className="btn" onClick={() => handleUnhide(p.id)}>Pokaż</button>
                  ) : (
                    <button className="btn" onClick={() => handleHide(p.id)}>Ukryj</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {status && <p><em>{status}</em></p>}
    </section>
  )
}
