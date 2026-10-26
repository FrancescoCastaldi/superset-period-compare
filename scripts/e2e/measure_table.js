const { chromium } = require('C:/Users/franc/Desktop/SviluppoComparison/superset/superset-frontend/node_modules/playwright');

(async () => {
  const browser = await chromium.launch({ headless: true, channel: 'chrome' });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  await page.goto('http://localhost:8088/login/');
  await page.fill('[data-test="username-input"]', 'admin');
  await page.fill('[data-test="password-input"]', 'admin');
  await page.click('[data-test="login-button"]');
  await page.waitForURL(url => !url.href.includes('/login'));

  await page.goto('http://localhost:8088/superset/dashboard/collaudo-confronto-temporale/');
  await page.waitForTimeout(6000);

  const dims = await page.evaluate(() => {
    const wrapper = document.querySelector('.table-scroll-wrapper');
    const table = document.querySelector('.hierarchical-table');
    const ths = Array.from(document.querySelectorAll('.hierarchical-table th')).map(th => ({
      text: th.innerText.trim(),
      width: th.getBoundingClientRect().width,
      offsetWidth: th.offsetWidth
    }));
    return {
      wrapperWidth: wrapper ? wrapper.getBoundingClientRect().width : null,
      tableWidth: table ? table.getBoundingClientRect().width : null,
      scrollWidth: wrapper ? wrapper.scrollWidth : null,
      clientWidth: wrapper ? wrapper.clientWidth : null,
      ths
    };
  });

  console.log('DOM Dimensions:', JSON.stringify(dims, null, 2));
  await browser.close();
})();
