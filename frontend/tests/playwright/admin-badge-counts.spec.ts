import { test, expect } from '@playwright/test'

test('badge counts include parents without contribution records', async ({ page, request }) => {
  const apiBase = 'http://localhost:8000'

  // admin login
  const login = await request.post(`${apiBase}/api/admin/login`, { data: { username: 'admin', password: 'changeme' } })
  expect(login.ok()).toBeTruthy()
  const token = (await login.json()).token
  expect(token).toBeTruthy()

  const ts = Date.now()
  const pAemail = `e2e+${ts}+A@example.com`
  const pBemail = `e2e+${ts}+B@example.com`

  // create two parents
  const pA = await request.post(`${apiBase}/api/admin/parents`, { data: { name: 'Badge A', email: pAemail, password: 'p' }, headers: { Authorization: `Bearer ${token}` } })
  const pB = await request.post(`${apiBase}/api/admin/parents`, { data: { name: 'Badge B', email: pBemail, password: 'p' }, headers: { Authorization: `Bearer ${token}` } })
  expect(pA.ok()).toBeTruthy()
  expect(pB.ok()).toBeTruthy()
  const pAj = await pA.json()
  const pBj = await pB.json()

  // create campaign
  const title = `e2e-badge-count-${ts}`
  const campRes = await request.post(`${apiBase}/api/admin/campaigns-new`, { data: { title, target_amount: 20 }, headers: { Authorization: `Bearer ${token}` } })
  expect(campRes.ok()).toBeTruthy()
  const camp = await campRes.json()

  // Create only one contribution (for parent A) and leave parent B without a contribution record
  const cA = await request.post(`${apiBase}/api/admin/contributions`, { data: { campaign_id: camp.id, parent_id: pAj.id, amount_expected: 20 }, headers: { Authorization: `Bearer ${token}` } })
  expect(cA.ok()).toBeTruthy()

  // Open UI as admin
  await page.addInitScript(({ t }) => { window.localStorage.setItem('admin_token', t); window.location.hash = '/admin' }, { t: token })
  await page.goto('/#/admin')
  await page.waitForSelector('text=Lista zbiórek')

  // The badge should show unpaid equal to total parents minus paid contributions.
  // Fetch current parents count via admin API to compute expected value (handles existing DB state).
  const parentsRes = await request.get(`${apiBase}/api/admin/parents`, { headers: { Authorization: `Bearer ${token}` } })
  expect(parentsRes.ok()).toBeTruthy()
  const parentsList = await parentsRes.json()
  const totalParents = parentsList.length
  const expectedInitial = totalParents // none paid yet for this campaign except created contribution for parent A

  const header = page.locator(`h4:has-text("${title}")`)
  await header.waitFor({ timeout: 5000 })
  await expect(page.locator(`h4:has-text("${title}") >> span.badge-pending`)).toHaveText(new RegExp(`${expectedInitial}\\s*nieopł\.`))

  // Mark parent A as paid and reload. Then compute expected visibility and badge using API data
  await request.post(`${apiBase}/api/admin/contributions/mark-paid`, { data: { campaign_id: camp.id, parent_id: pAj.id, amount: 20 }, headers: { Authorization: `Bearer ${token}` } })
  await page.reload()

  // Re-fetch parents and contributions to compute expected state
  const parentsAfter = await request.get(`${apiBase}/api/admin/parents`, { headers: { Authorization: `Bearer ${token}` } })
  expect(parentsAfter.ok()).toBeTruthy()
  const parentsListAfter = await parentsAfter.json()
  const totalParentsAfter = parentsListAfter.length

  const contribsRes = await request.get(`${apiBase}/api/admin/contributions`, { headers: { Authorization: `Bearer ${token}` } })
  expect(contribsRes.ok()).toBeTruthy()
  const contribsGroups = await contribsRes.json()
  const myGroup = contribsGroups.find((g: any) => g.campaign && g.campaign.id === camp.id)
  const contribs = myGroup ? (myGroup.contributions || []) : []
  const paidCount = contribs.filter((c: any) => c.status === 'paid').length

  const allPaid = totalParentsAfter > 0 ? (paidCount === totalParentsAfter) : (contribs.length > 0 && contribs.every((c: any) => c.status === 'paid'))

  // Debug output for troubleshooting
  console.log('DEBUG: totalParentsAfter=', totalParentsAfter, 'paidCount=', paidCount, 'allPaid=', allPaid)
  const pageHtml = await page.content()
  console.log('DEBUG: page HTML snippet:', pageHtml.substring(0, 1000))

  if (allPaid) {
    // Campaign should be hidden
    // ensure admin list loaded then check absence
    await page.waitForSelector('text=Lista zbiórek')
    const headerCount = await page.locator(`h4:has-text("${title}")`).count()
    expect(headerCount).toBe(0)
  } else {
    // Campaign should be visible and badge should equal totalParentsAfter - paidCount (fallback to contribs)
    await page.waitForSelector('text=Lista zbiórek')
    // wait for the campaign header to appear
    const header = page.locator(`h4:has-text("${title}")`)
    await header.waitFor({ timeout: 10000 })
    const headerCount = await header.count()
    expect(headerCount).toBeGreaterThan(0)
    const expected = totalParentsAfter > 0 ? (totalParentsAfter - paidCount) : contribs.filter((c: any) => c.status !== 'paid').length
    await expect(page.locator(`h4:has-text("${title}") >> span.badge-pending`)).toHaveText(new RegExp(`${expected}\\s*nieopł\.`))
  }
})
