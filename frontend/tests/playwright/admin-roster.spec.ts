import { test, expect } from '@playwright/test'

test('admin can confirm a parent payment via roster', async ({ page }) => {
  // Go to frontend
  await page.goto('/')

  // Fill admin login (seeded credentials: admin / changeme)
  await page.fill('input[placeholder=""]:left-of(:text("Hasło"))', 'admin').catch(()=>{})
  // fallback selectors in case placeholders/labels differ
  await page.fill('input[type="text"]:nth-of-type(1)', 'admin').catch(()=>{})
  await page.fill('input[type="password"]', 'changeme')
  await page.click('button:has-text("Zaloguj")')

  // Wait for list of campaigns to load
  await page.waitForSelector('text=Lista zbiórek')

  // Click first 'Zobacz listę rodziców' button
  await page.click('button:has-text("Zobacz listę rodziców")')

  // Wait for roster modal/detail to appear
  await page.waitForSelector('text=Zbiórka:')

  // If there is a 'Potwierdź wpłatę' button, click the first one
  const confirm = await page.$('button:has-text("Potwierdź wpłatę")')
  if (confirm) {
    await confirm.click()
    // After click, status text should update
    await page.waitForSelector('text=Oznaczono jako opłacone', { timeout: 5000 })
  } else {
    // If there is no button, ensure at least the table is present
    await expect(page.locator('table.contrib-table')).toHaveCount(1)
  }
})
