// Simple auth helper using localStorage
export function setAdminToken(token) {
  if (token) localStorage.setItem('admin_token', token)
}

export function setParentToken(token) {
  if (token) localStorage.setItem('parent_token', token)
}

export function getToken() {
  return localStorage.getItem('admin_token') || localStorage.getItem('parent_token') || null
}

export function clearTokens() {
  localStorage.removeItem('admin_token')
  localStorage.removeItem('parent_token')
}

export function isAdmin() {
  return !!localStorage.getItem('admin_token')
}

export function isParent() {
  return !!localStorage.getItem('parent_token')
}

// Listen for logout across tabs
export function onStorageLogout(cb) {
  window.addEventListener('storage', (e) => {
    if ((e.key === 'admin_token' || e.key === 'parent_token') && e.newValue === null) cb()
  })
}
