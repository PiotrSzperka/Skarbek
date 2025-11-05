const { chromium } = require('playwright')

async function run(){
  const browser = await chromium.launch({ headless: true })
  const page = await browser.newPage()
  const base = process.env.BASE_URL || 'http://localhost:3000'

  try{
    await page.goto(base + '/#/admin', { waitUntil: 'networkidle' })
    // wait for login form
    await page.waitForSelector('text=Nazwa użytkownika')
    // fill login
    await page.fill('input[class*=input]', 'admin')
    await page.fill('input[type=password]', 'changeme')
    await page.click('button:has-text("Zaloguj")')

    // wait for admin buttons
    await page.waitForSelector('button:has-text("Utwórz rodzica")', { timeout: 5000 })
    await page.waitForSelector('button:has-text("Utwórz zbiórkę")', { timeout: 5000 })

    // ensure inline create-campaign form is NOT present on the main admin page
    const inlineForm = await page.$('form >> text=Tytuł')
    if (inlineForm) {
      console.error('Inline create-campaign form still present on admin main page')
      await browser.close()
      process.exit(2)
    }

    // click create-campaign button
    await page.click('button:has-text("Utwórz zbiórkę")')
    // expect the dedicated view to show a heading
    await page.waitForSelector('text=Utwórz zbiórkę', { timeout: 5000 })

    console.log('SMOKE TEST PASS: Admin views behave as expected')
    await browser.close()
    process.exit(0)
  }catch(err){
    console.error('SMOKE TEST FAIL:', err)
    await browser.close()
    process.exit(1)
  }
}

run()
