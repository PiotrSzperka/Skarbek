import { test, expect } from '@playwright/test'

test('parent can cancel or confirm submit contribution', async ({ page, request }) => {
  const apiBase = 'http://localhost:8000'

  // create a fresh campaign as admin so parent has no prior contribution for it
  const adminLogin = await request.post(`${apiBase}/api/admin/login`, { data: { username: 'admin', password: 'changeme' } })
  expect(adminLogin.ok()).toBeTruthy()
  const adminToken = (await adminLogin.json()).token
  expect(adminToken).toBeTruthy()
  const ts = Date.now()
  const title = `e2e-parent-submit-${ts}`
  const createCamp = await request.post(`${apiBase}/api/admin/campaigns-new`, { data: { title, target_amount: 5 }, headers: { Authorization: `Bearer ${adminToken}` } })
  expect(createCamp.ok()).toBeTruthy()

  // parent credentials seeded earlier
  const email = 'parent1@example.com'
  const password = 'pass'

  // Ensure parent exists and can login
  const login = await request.post(`${apiBase}/api/parents/login`, { data: { email, password } })
  expect(login.ok()).toBeTruthy()
  const token = (await login.json()).token
  expect(token).toBeTruthy()

  // prepare browser with token and go to parent dashboard
  await page.addInitScript(({ t }) => { window.localStorage.setItem('parent_token', t); }, { t: token })
  await page.goto('/#/parent/dashboard')

  // Wait for parent panel
  await page.waitForSelector('text=Panel rodzica')

  // Find the campaign we created and its 'Zgłoś wpłatę' button
  const campaignHeader = page.locator(`h3:has-text("Zbiórka: ${title}")`).first()
  // fallback: if the campaign is not rendered as a detail, the list shows title in strong
  const campaignListItem = page.locator(`li:has-text("${title}")`).first()
  const submitBtn = page.locator(`li:has-text("${title}") button:has-text("Zgłoś wpłatę")`)
  // debug: dump page snippet if button not found
  if ((await submitBtn.count()) === 0) {
    console.log('DEBUG: no submit buttons found, page snippet:\n', (await page.content()).substring(0,1000))
  }
  await expect(submitBtn.first()).toBeVisible()

  // Click to show confirm UI (modal or inline)
  await submitBtn.first().click()
  await page.waitForTimeout(200)

  const modal = page.locator('text=Potwierdź zgłoszenie wpłaty').first()
  if ((await modal.count()) > 0) {
    // Modal-confirm flow
    await expect(modal).toBeVisible()
    const confirmBtn = page.locator('div[role="dialog"] button:has-text("Potwierdź")')
    const cancelBtn = page.locator('div[role="dialog"] button:has-text("Anuluj")')
    if ((await confirmBtn.count()) === 0) {
      await expect(page.locator('button:has-text("Potwierdź")').first()).toBeVisible()
    } else {
      await expect(confirmBtn.first()).toBeVisible()
    }

    // Cancel and ensure modal disappears
    await cancelBtn.first().click()
    await expect(page.locator('text=Potwierdź zgłoszenie wpłaty').first()).toHaveCount(0)
    await expect(page.locator('button:has-text("Zgłoś wpłatę")').first()).toBeVisible()

    // Click again and confirm via modal
    await page.locator('button:has-text("Zgłoś wpłatę")').first().click()
    const modal2 = page.locator('text=Potwierdź zgłoszenie wpłaty').first()
    await expect(modal2).toBeVisible()
    if ((await confirmBtn.count()) > 0) {
      await confirmBtn.first().click()
    } else {
      await page.locator('button:has-text("Potwierdź")').first().click()
    }
  } else {
    // Inline-confirm flow (older UI) - look for inline Potwierdź/Anuluj within the campaign item
    const inlineConfirm = campaignListItem.locator('button:has-text("Potwierdź")').first()
    const inlineCancel = campaignListItem.locator('button:has-text("Anuluj")').first()
    await expect(inlineConfirm).toBeVisible()
    await expect(inlineCancel).toBeVisible()

    // Cancel and ensure original button returns
    await inlineCancel.click()
    await expect(campaignListItem.locator('button:has-text("Zgłoś wpłatę")').first()).toBeVisible()

    // Click again and confirm inline
    await campaignListItem.locator('button:has-text("Zgłoś wpłatę")').first().click()
    await inlineConfirm.click()
  }

  // After confirming, status should update (either shows 'oczekuje' or no submit button)
  await page.waitForTimeout(500) // brief wait for update
  const status = page.locator('text=oczekuje').first()
  const statusCount = await status.count()
  expect(statusCount).toBeGreaterThan(0)
})
