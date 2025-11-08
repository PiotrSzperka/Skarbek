import { test, expect } from '@playwright/test'

test('parent forced to change password on first login', async ({ page, request }) => {
  const apiBase = 'http://localhost:8000'
  
  // Listen for console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('Browser console error:', msg.text())
    }
  })
  
  page.on('pageerror', err => {
    console.log('Page error:', err.message)
  })
  
  // Step 1: Admin creates new parent with temporary password
  const adminLogin = await request.post(`${apiBase}/api/admin/login`, {
    data: { username: 'admin', password: 'changeme' }
  })
  expect(adminLogin.ok()).toBeTruthy()
  const adminToken = (await adminLogin.json()).token
  expect(adminToken).toBeTruthy()

  const timestamp = Date.now()
  const testEmail = `e2e_force_pwd_${timestamp}@example.com`
  const tempPassword = 'temp123'
  const newPassword = 'newpass456'

  const createParent = await request.post(`${apiBase}/api/admin/parents`, {
    data: {
      email: testEmail,
      password: tempPassword
    },
    headers: { Authorization: `Bearer ${adminToken}` }
  })
  expect(createParent.ok()).toBeTruthy()
  const parentData = await createParent.json()
  expect(parentData.email).toBe(testEmail)

  // Step 2: Parent logs in with temporary password
  await page.goto('/#/parent/login')
  await page.waitForSelector('h3:has-text("Logowanie rodzica")')
  
  const inputs = page.locator('.input')
  await inputs.first().fill(testEmail)  // Email field
  await inputs.last().fill(tempPassword)  // Password field
  await page.click('button:has-text("Zaloguj")')

  // Step 3: Verify redirect to password change form
  await page.waitForURL('**/parent/change-password', { timeout: 10000 })
  await page.waitForTimeout(1000)  // Give React time to render
  
  // Debug: check what's on the page
  const bodyText = await page.locator('body').textContent()
  console.log('Page content after redirect:', bodyText?.substring(0, 500))
  
  await page.waitForSelector('h2:has-text("Wymagana zmiana hasła")', { timeout: 10000 })
  
  // Verify instructions are displayed
  await expect(page.locator('text=Musisz zmienić')).toBeVisible()

  // Step 4: Fill password change form (3 password fields in order: old, new, confirm)
  const passwordInputs = page.locator('input[type="password"]')
  await passwordInputs.nth(0).fill(tempPassword)  // Stare hasło
  await passwordInputs.nth(1).fill(newPassword)   // Nowe hasło
  await passwordInputs.nth(2).fill(newPassword)   // Powtórz nowe hasło
  
  await page.click('button:has-text("Zmień hasło")')

  // Step 5: Verify redirect to dashboard after password change
  await page.waitForURL('**/parent/dashboard')
  await page.waitForSelector('text=Panel rodzica')

  // Step 6: Logout
  const logoutBtn = page.locator('button:has-text("Wyloguj")')
  if (await logoutBtn.count() > 0) {
    await logoutBtn.click()
  } else {
    // Manual logout by clearing localStorage and navigating
    await page.evaluate(() => localStorage.removeItem('parent_token'))
  }
  await page.goto('/#/parent/login')

  // Step 7: Login with new password (should NOT require password change)
  await page.waitForSelector('h3:has-text("Logowanie rodzica")')
  const loginInputs = page.locator('.input')
  await loginInputs.first().fill(testEmail)
  await loginInputs.last().fill(newPassword)
  await page.click('button:has-text("Zaloguj")')

  // Step 8: Verify successful login directly to dashboard (no password change redirect)
  await page.waitForURL('**/parent/dashboard', { timeout: 5000 })
  await page.waitForSelector('text=Panel rodzica')

  // Verify no password change form is shown
  await expect(page.locator('h2:has-text("Wymagana zmiana hasła")')).not.toBeVisible()
})

test('parent cannot access protected endpoints before password change', async ({ page, request }) => {
  const apiBase = 'http://localhost:8000'
  
  // Create parent with temporary password
  const adminLogin = await request.post(`${apiBase}/api/admin/login`, {
    data: { username: 'admin', password: 'changeme' }
  })
  const adminToken = (await adminLogin.json()).token

  const timestamp = Date.now()
  const testEmail = `e2e_guard_${timestamp}@example.com`
  const tempPassword = 'temp789'

  await request.post(`${apiBase}/api/admin/parents`, {
    data: { email: testEmail, password: tempPassword },
    headers: { Authorization: `Bearer ${adminToken}` }
  })

  // Parent logs in
  const parentLogin = await request.post(`${apiBase}/api/parents/login`, {
    data: { email: testEmail, password: tempPassword }
  })
  expect(parentLogin.ok()).toBeTruthy()
  const loginData = await parentLogin.json()
  expect(loginData.require_password_change).toBe(true)
  const parentToken = loginData.token

  // Try to access protected endpoint /parents/me - should get 403
  const meResponse = await request.get(`${apiBase}/api/parents/me`, {
    headers: { Authorization: `Bearer ${parentToken}` }
  })
  expect(meResponse.status()).toBe(403)
  const meError = await meResponse.json()
  expect(meError.detail.code).toBe('password_change_required')

  // Try to access /parents/campaigns - should get 403
  const campaignsResponse = await request.get(`${apiBase}/api/parents/campaigns`, {
    headers: { Authorization: `Bearer ${parentToken}` }
  })
  expect(campaignsResponse.status()).toBe(403)
  const campaignsError = await campaignsResponse.json()
  expect(campaignsError.detail.code).toBe('password_change_required')

  // Change password
  const changeResponse = await request.post(`${apiBase}/api/parents/change-password-initial`, {
    data: { old_password: tempPassword, new_password: 'newpass999' },
    headers: { Authorization: `Bearer ${parentToken}` }
  })
  expect(changeResponse.ok()).toBeTruthy()
  const changeData = await changeResponse.json()
  expect(changeData.require_password_change).toBe(false)
  const newToken = changeData.token

  // Now access should work with new token
  const meResponseAfter = await request.get(`${apiBase}/api/parents/me`, {
    headers: { Authorization: `Bearer ${newToken}` }
  })
  expect(meResponseAfter.ok()).toBeTruthy()
  const meData = await meResponseAfter.json()
  expect(meData.email).toBe(testEmail)
})

test('password change form validates inputs', async ({ page, request }) => {
  const apiBase = 'http://localhost:8000'
  
  // Create parent
  const adminLogin = await request.post(`${apiBase}/api/admin/login`, {
    data: { username: 'admin', password: 'changeme' }
  })
  const adminToken = (await adminLogin.json()).token

  const timestamp = Date.now()
  const testEmail = `e2e_validation_${timestamp}@example.com`
  const tempPassword = 'temp111'

  await request.post(`${apiBase}/api/admin/parents`, {
    data: { email: testEmail, password: tempPassword },
    headers: { Authorization: `Bearer ${adminToken}` }
  })

  // Login and navigate to password change
  await page.goto('/#/parent/login')
  const loginInputs = page.locator('.input')
  await loginInputs.first().fill(testEmail)
  await loginInputs.last().fill(tempPassword)
  await page.click('button:has-text("Zaloguj")')
  await page.waitForURL('**/parent/change-password')

  const passwordInputs = page.locator('input[type="password"]')
  
  // Test: new password too short
  await passwordInputs.nth(0).fill(tempPassword)
  await passwordInputs.nth(1).fill('abc')
  await passwordInputs.nth(2).fill('abc')
  await page.click('button:has-text("Zmień hasło")')
  
  await expect(page.locator('text=Nowe hasło musi mieć min. 6 znaków')).toBeVisible()

  // Test: new password same as old
  await passwordInputs.nth(1).fill(tempPassword)
  await passwordInputs.nth(2).fill(tempPassword)
  await page.click('button:has-text("Zmień hasło")')
  
  await expect(page.locator('text=Nowe hasło musi być inne niż stare')).toBeVisible()

  // Test: passwords don't match
  await passwordInputs.nth(1).fill('newpass123')
  await passwordInputs.nth(2).fill('different456')
  await page.click('button:has-text("Zmień hasło")')
  
  await expect(page.locator('text=Nowe hasła nie pasują do siebie')).toBeVisible()

  // Test: wrong old password
  await passwordInputs.nth(0).fill('wrongpassword')
  await passwordInputs.nth(1).fill('newpass123')
  await passwordInputs.nth(2).fill('newpass123')
  await page.click('button:has-text("Zmień hasło")')
  
  await expect(page.locator('text=invalid old password')).toBeVisible()
})
