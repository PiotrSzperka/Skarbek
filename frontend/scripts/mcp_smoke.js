const { chromium } = require('playwright');

(async () => {
  const url = 'http://host.docker.internal:3000/#/admin';
  // host.docker.internal works inside container; from host, localhost is fine
  const localUrl = 'http://localhost:3000/#/admin';
  const useUrl = localUrl;
  console.log('Starting Playwright smoke test against', useUrl);
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  try {
    await page.goto(useUrl, { waitUntil: 'networkidle' });
    // Fill admin login
    await page.getByLabel('Nazwa użytkownika').fill('admin');
    await page.getByLabel('Hasło').fill('changeme');
    await Promise.all([
      page.getByRole('button', { name: /Zaloguj/i }).click(),
      page.waitForResponse(resp => resp.url().includes('/api/admin') || resp.status() < 400, { timeout: 3000 }).catch(()=>null)
    ]);
    console.log('Logged in, checking for create buttons...');

    const hasCreateParent = await page.getByRole('button', { name: 'Utwórz rodzica' }).count();
    const hasCreateCampaign = await page.getByRole('button', { name: 'Utwórz zbiórkę' }).count();
    console.log('Create buttons found:', { hasCreateParent, hasCreateCampaign });

    // Ensure the old embedded Tytuł input is NOT present on the list view
    const titleInputs = await page.getByLabel('Tytuł *').count().catch(()=>0);
    if (titleInputs > 0) {
      console.error('Found legacy embedded campaign create input on admin list view (FAIL)');
      process.exitCode = 2;
      await browser.close();
      return;
    }
    console.log('No legacy embedded campaign form on list view (OK)');

    // Open create-campaign view
    if (hasCreateCampaign > 0) {
      await page.getByRole('button', { name: 'Utwórz zbiórkę' }).click();
      // wait for the new view label
      await page.getByLabel('Tytuł').waitFor({ timeout: 3000 });
      console.log('Create campaign view opened and Tytuł input present (OK)');
    } else {
      console.error('Create campaign button missing (FAIL)');
      process.exitCode = 3;
      await browser.close();
      return;
    }

    console.log('Smoke test passed');
    await browser.close();
  } catch (e) {
    console.error('Smoke test error:', e);
    await browser.close();
    process.exitCode = 1;
  }
})();
