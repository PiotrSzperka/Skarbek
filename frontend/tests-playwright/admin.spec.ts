import { test, expect, request } from '@playwright/test';

test('admin e2e smoke (login, create parent, UI hide, create campaign)', async ({ page }) => {
  const apiBase = process.env.API_URL || 'http://localhost:8000';

  // login via API
  const req = await request.newContext({ baseURL: apiBase });
  const login = await req.post('/api/admin/login', { data: { username: 'admin', password: 'changeme' } });
  expect(login.status()).toBe(200);
  const token = (await login.json()).token;

  // seed a parent via API
  const parentEmail = `e2e+${Date.now()}@example.com`;
  const parentRes = await req.post('/api/admin/parents', {
    headers: { Authorization: `Bearer ${token}` },
    data: { name: 'E2E', email: parentEmail, password: 'e2e-pass' }
  });
  expect(parentRes.status()).toBe(200);

  // set admin token in browser localStorage and navigate to admin UI
  await page.addInitScript((t) => { localStorage.setItem('admin_token', t) }, token);
  await page.goto(process.env.FRONTEND_URL ? `${process.env.FRONTEND_URL}/#/admin` : 'http://localhost:3000/#/admin');
  await page.waitForSelector('button:has-text("Zarządzaj rodzicami")', { timeout: 5000 });

  // click parents view and verify created parent is visible
  await page.click('button:has-text("Zarządzaj rodzicami")');
  await page.waitForSelector('table.parents-table tbody tr', { timeout: 5000 });
  const text = await page.textContent('table.parents-table tbody tr');
  expect(text).toContain('E2E');

  // hide using UI button if present
  const hideBtn = await page.$('table.parents-table tbody tr td button:has-text("Ukryj")');
  if (hideBtn) {
    await hideBtn.click();
    await page.waitForTimeout(500);
  }

  // create campaign via API
  const campRes = await req.post('/api/admin/campaigns/', {
    headers: { Authorization: `Bearer ${token}` },
    data: { title: 'E2E Camp', description: 'd', target_amount: 10 }
  });
  expect(campRes.status()).toBe(200);

  await req.dispose();
});
