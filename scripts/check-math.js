// check-math.js
// Usage: node scripts/check-math.js <url>
// Crawls the page with Playwright and lists text nodes where raw '$' or '$$' remain.

const { chromium } = require('playwright');
const url = process.argv[2];
if (!url) {
  console.error('Usage: node scripts/check-math.js <url>');
  process.exit(1);
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: 'networkidle' });

  const texts = await page.$$eval('body *', nodes => {
    const results = [];
    for (const n of nodes) {
      const child = n.firstChild;
      if (!child || child.nodeType !== Node.TEXT_NODE) continue;
      const t = child.textContent;
      if (!t) continue;
      const trimmed = t.trim();
      if (trimmed.length === 0) continue;
      results.push(trimmed);
    }
    return results;
  });

  const hits = [];
  texts.forEach((t, idx) => {
    if (t.includes('$$') || /\$(.+?)\$/.test(t)) {
      hits.push({ idx, text: t });
    }
  });

  console.log(`Checked ${texts.length} text nodes on ${url}`);
  if (hits.length === 0) {
    console.log('No raw $ or $$ found.');
  } else {
    console.log('Potential unrendered math:');
    hits.forEach(h => console.log(`- [${h.idx}] ${h.text}`));
  }

  await browser.close();
})();
