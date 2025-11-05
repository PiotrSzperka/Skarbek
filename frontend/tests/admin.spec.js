const { chromium } = require('playwright')

async function run(){
  const browser = await chromium.launch({ headless: true })
  const page = await browser.newPage()
  const base = process.env.FRONTEND_URL || (process.env.BASE_URL || 'http://localhost:3000')
  const api = process.env.API_URL || 'http://localhost:8000'
  const { request: apiRequestFactory } = require('playwright')

  try{
    // perform admin login via API to get token (use Playwright request to avoid CORS)
    const apiRequest = await apiRequestFactory.newContext({ baseURL: api })
    const loginRes = await apiRequest.post('/api/admin/login', { data: { username: 'admin', password: 'changeme' } })
    if (loginRes.status() !== 200) throw new Error('Could not obtain admin token')
    const tokenJson = await loginRes.json()
    const token = tokenJson.token

    // set admin token in localStorage so frontend requests include it
    await page.addInitScript((t) => { localStorage.setItem('admin_token', t) }, token)

    // now navigate to admin UI
  await page.goto(base + '/#/admin', { waitUntil: 'networkidle' })
    await page.waitForSelector('button:has-text("Zarządzaj rodzicami")', { timeout: 5000 })

    // create parent via admin API using token (Node request to avoid CORS)
    const parentRes = await apiRequest.post('/api/admin/parents', {
      headers: { Authorization: `Bearer ${token}` },
      data: { name: 'E2E', email: `e2e+${Date.now()}@example.com`, password: 'e2e-pass' }
    })
    if (parentRes.status() !== 200) throw new Error('Failed to create parent via API')

    // go to parents view and verify a row appears
    await page.click('button:has-text("Zarządzaj rodzicami")')
    await page.waitForSelector('table.parents-table tbody tr', { timeout: 5000 })

    // hide the first parent found (UI button will call API using token from localStorage)
    const firstHide = await page.$('table.parents-table tbody tr td button:has-text("Ukryj")')
    if (firstHide) {
      await firstHide.click()
      await page.waitForTimeout(500)
    }

    // create campaign via admin API
    const campRes = await apiRequest.post('/api/admin/campaigns/', {
      headers: { Authorization: `Bearer ${token}` },
      data: { title: 'E2E Camp', description: 'd', target_amount: 10 }
    })
    if (campRes.status() !== 200) throw new Error('Failed to create campaign')

    console.log('E2E admin flow smoke OK')
    await browser.close()
    process.exit(0)
  }catch(err){
    console.error('E2E FAIL', err)
    await browser.close()
    process.exit(1)
  }
}

run()
