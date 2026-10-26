const path = require('path');
const fs = require('fs');

// We use playwright from superset-frontend
const { chromium } = require('C:/Users/franc/Desktop/SviluppoComparison/superset/superset-frontend/node_modules/playwright');

(async () => {
  console.log('Launching browser (chrome)...');
  const browser = await chromium.launch({ headless: true, channel: 'chrome' });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  const consoleLogs = [];
  page.on('console', msg => {
    const text = `[CONSOLE ${msg.type()}] ${msg.text()}`;
    consoleLogs.push(text);
    if (msg.type() === 'error' || msg.type() === 'warning') {
      console.log(text);
    }
  });

  page.on('pageerror', err => {
    console.log(`[PAGE ERROR] ${err.toString()}`);
    consoleLogs.push(`[PAGE ERROR] ${err.toString()}`);
  });

  console.log('Navigating to login...');
  await page.goto('http://localhost:8088/login/');
  await page.waitForSelector('[data-test="username-input"]', { timeout: 15000 });
  await page.fill('[data-test="username-input"]', 'admin');
  await page.fill('[data-test="password-input"]', 'admin');
  await page.click('[data-test="login-button"]');
  await page.waitForURL(url => !url.href.includes('/login'), { timeout: 15000 });
  console.log('Logged in successfully!');

  console.log('Navigating to dashboard collaudo-confronto-temporale...');
  await page.goto('http://localhost:8088/superset/dashboard/collaudo-confronto-temporale/');
  await page.waitForTimeout(10000);
  await page.mouse.move(1, 1);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(1000);
  const outPath = 'C:/Users/franc/.gemini/antigravity/brain/3505ae0b-d652-43c6-9738-2bdefcc8e054/dashboard_screenshot.png';
  await page.screenshot({ path: outPath, fullPage: true });
  console.log(`Screenshot saved to ${outPath}`);

  fs.writeFileSync('C:/Users/franc/.gemini/antigravity/brain/3505ae0b-d652-43c6-9738-2bdefcc8e054/dashboard_console.log', consoleLogs.join('\n'));
  console.log('Console logs saved.');

  await browser.close();
  console.log('Done.');
})().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
