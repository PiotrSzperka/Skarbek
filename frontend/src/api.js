// Minimal API helper for frontend
const apiBase = '/api'

function getStoredToken() {
  return localStorage.getItem('admin_token') || localStorage.getItem('parent_token') || null
}

async function request(path, opts = {}) {
  // Merge headers from opts but ensure Content-Type remains set for JSON
  const mergedHeaders = { ...(opts.headers || {}) };
  const token = mergedHeaders.Authorization ? null : getStoredToken();
  const headers = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...mergedHeaders };

  const res = await fetch(`${apiBase}${path}`, {
    ...opts,
    headers,
  })

  if (res.status === 401) {
    // clear tokens on unauthorized
    localStorage.removeItem('admin_token')
    localStorage.removeItem('parent_token')
    const text = await res.text().catch(() => '')
    throw new Error(`401 Unauthorized: ${text}`)
  }

  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`${res.status} ${res.statusText}: ${text}`)
  }
  return res.json().catch(() => null)
}

export const listCampaigns = () => request('/campaigns/')
export const createCampaign = async (payload, token) => {
  return request('/admin/campaigns-new', {
    method: 'POST',
    body: JSON.stringify(payload),
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
}

export const adminLogin = (username, password) => request('/admin/login', {
  method: 'POST',
  body: JSON.stringify({ username, password }),
})

export const adminCreateParent = (payload, token) => request('/admin/parents', {
  method: 'POST',
  body: JSON.stringify(payload),
  headers: token ? { Authorization: `Bearer ${token}` } : undefined,
})

export const parentLogin = (email, password) => request('/parents/login', {
  method: 'POST',
  body: JSON.stringify({ email, password }),
})

export const parentGetCampaigns = (token) => request('/parents/campaigns', {
  method: 'GET',
  headers: token ? { Authorization: `Bearer ${token}` } : undefined,
})

export const parentSubmitContribution = (payload, token) => request('/parents/contributions', {
  method: 'POST',
  body: JSON.stringify(payload),
  headers: token ? { Authorization: `Bearer ${token}` } : undefined,
})

export const markContributionPaid = (payload, token) => request('/admin/contributions/mark-paid', {
  method: 'POST',
  body: JSON.stringify(payload),
  headers: token ? { Authorization: `Bearer ${token}` } : undefined,
})

export const adminListContributions = (token) => request('/admin/contributions', {
  method: 'GET',
  headers: token ? { Authorization: `Bearer ${token}` } : undefined,
})

// roster + create-contribution for admin
export const adminCampaignRoster = (campaignId, token) => request(`/admin/campaigns/${campaignId}/roster`, {
  method: 'GET',
  headers: token ? { Authorization: `Bearer ${token}` } : undefined,
})

export const adminCreateContribution = (payload, token) => request('/admin/contributions', {
  method: 'POST',
  body: JSON.stringify(payload),
  headers: token ? { Authorization: `Bearer ${token}` } : undefined,
})

// Admin parents endpoints
export const adminListParents = (token, includeHidden = false) => request(`/admin/parents${includeHidden ? '?include_hidden=true' : ''}`, {
  method: 'GET',
  headers: token ? { Authorization: `Bearer ${token}` } : undefined,
})

export const adminUpdateParent = (id, payload, token) => request(`/admin/parents/${id}`, {
  method: 'PUT',
  body: JSON.stringify(payload),
  headers: token ? { Authorization: `Bearer ${token}` } : undefined,
})

export const adminChangeParentPassword = (id, newPassword, token) => request(`/admin/parents/${id}/change-password`, {
  method: 'POST',
  body: JSON.stringify({ new_password: newPassword }),
  headers: token ? { Authorization: `Bearer ${token}` } : undefined,
})

export const adminHideParent = (id, token) => request(`/admin/parents/${id}/hide`, {
  method: 'POST',
  headers: token ? { Authorization: `Bearer ${token}` } : undefined,
})

export const adminUnhideParent = (id, token) => request(`/admin/parents/${id}/unhide`, {
  method: 'POST',
  headers: token ? { Authorization: `Bearer ${token}` } : undefined,
})

// Admin campaign management
export const adminUpdateCampaign = (id, payload, token) => request(`/admin/campaigns/${id}`, {
  method: 'PUT',
  body: JSON.stringify(payload),
  headers: token ? { Authorization: `Bearer ${token}` } : undefined,
})

export const adminCloseCampaign = (id, token) => request(`/admin/campaigns/${id}/close`, {
  method: 'POST',
  headers: token ? { Authorization: `Bearer ${token}` } : undefined,
})

export const adminDeleteCampaign = (id, token) => request(`/admin/campaigns/${id}`, {
  method: 'DELETE',
  headers: token ? { Authorization: `Bearer ${token}` } : undefined,
})

export default { listCampaigns, createCampaign, adminLogin, adminCreateParent, parentLogin, parentGetCampaigns, parentSubmitContribution, markContributionPaid }
