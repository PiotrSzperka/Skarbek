import { test, expect } from '@playwright/test'

test('admin badge shows unpaid count and filter hides campaign when all paid', async ({ page, request }) => {
  const apiBase = 'http://localhost:8000'

  // login admin to get token
  const login = await request.post(`${apiBase}/api/admin/login`, { data: { username: 'admin', password: 'changeme' } })
  expect(login.ok()).toBeTruthy()
  const loginJson = await login.json()
  const token = loginJson.token
  expect(token).toBeTruthy()

  // create two parents
  const ts = Date.now()
  const p1email = `e2e+${ts}+1@example.com`
  const p2email = `e2e+${ts}+2@example.com`
  const p1 = await request.post(`${apiBase}/api/admin/parents`, { data: { name: 'E2E Parent1', email: p1email, password: 'p' }, headers: { Authorization: `Bearer ${token}` } })
  const p2 = await request.post(`${apiBase}/api/admin/parents`, { data: { name: 'E2E Parent2', email: p2email, password: 'p' }, headers: { Authorization: `Bearer ${token}` } })
  expect(p1.ok()).toBeTruthy()
  expect(p2.ok()).toBeTruthy()
  const p1j = await p1.json()
  const p2j = await p2.json()

  // create campaign
  const title = `e2e-campaign-${ts}`
  const campRes = await request.post(`${apiBase}/api/admin/campaigns-new`, { data: { title, target_amount: 10 } , headers: { Authorization: `Bearer ${token}` }})
  expect(campRes.ok()).toBeTruthy()
  const camp = await campRes.json()

  // set admin token in localStorage so UI loads as admin
  await page.addInitScript(({ t }) => { window.localStorage.setItem('admin_token', t); window.location.hash = '/admin' }, { t: token })
  await page.goto('/#/admin')

  // wait for admin list
  await page.waitForSelector('text=Lista zbiórek')

  // find campaign and its badge; parse initial unpaid count (may include pre-existing parents)
  const campaignHeader = page.locator(`h4:has-text("${title}")`)
  await campaignHeader.waitFor({ timeout: 5000 })
  const badge = campaignHeader.locator('span.badge-pending')
  // parse initial count if present
  let initialUnpaid = null
  if (await badge.count() > 0) {
    const txt = await badge.textContent()
    const m = txt && txt.match(/(\d+)/)
    initialUnpaid = m ? parseInt(m[1], 10) : null
  }

  // create contributions for both parents (pending)
  const c1 = await request.post(`${apiBase}/api/admin/contributions`, { data: { campaign_id: camp.id, parent_id: p1j.id, amount_expected: 10 }, headers: { Authorization: `Bearer ${token}` } })
  const c2 = await request.post(`${apiBase}/api/admin/contributions`, { data: { campaign_id: camp.id, parent_id: p2j.id, amount_expected: 10 }, headers: { Authorization: `Bearer ${token}` } })
  expect(c1.ok()).toBeTruthy()
  expect(c2.ok()).toBeTruthy()

  // reload page and expect badge now shows 2 unpaid (the two contributions we created)
  await page.reload()
  await page.waitForSelector(`h4:has-text("${title}")`)
  await expect(page.locator(`h4:has-text("${title}") >> span.badge-pending`)).toHaveText(/2\s*nieopł\./)

  // mark both contributions as paid
  await request.post(`${apiBase}/api/admin/contributions/mark-paid`, { data: { campaign_id: camp.id, parent_id: p1j.id, amount: 10 }, headers: { Authorization: `Bearer ${token}` } })
  await request.post(`${apiBase}/api/admin/contributions/mark-paid`, { data: { campaign_id: camp.id, parent_id: p2j.id, amount: 10 }, headers: { Authorization: `Bearer ${token}` } })

  // reload page; campaign should be hidden when 'Pokaż opłacone' is unchecked
  await page.reload()
  // ensure checkbox is unchecked (default)
  const checkbox = page.getByLabel('Pokaż opłacone')
  await expect(checkbox).toBeVisible()
  await expect(checkbox).not.toBeChecked()

  // campaign should not be visible
  await expect(page.locator(`h4:has-text("${title}")`)).toHaveCount(0)

  // check 'Pokaż opłacone' and campaign should appear
  await checkbox.check()
  await expect(page.locator(`h4:has-text("${title}")`)).toHaveCount(1)
})
