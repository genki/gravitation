// check-math.js
// Usage: node scripts/check-math.js <url>
// Crawls the page with Playwright and lists lines where raw '$' or '$$' remain in rendered text.
// Requires playwright (`npm install playwright`).

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

  // Grab visible text nodes
  const texts = await page.$$eval('body *', nodes => {
    return nodes
      .filter(n => n.childNodes && n.childNodes.length === 1 && n.childNodes[0].nodeType === Node.TEXT_NODE)
      .map(n => n.innerText.trim())
      .filter(t => t.length);
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
    hits.forEach(h => {
      console.log(`- [${h.idx}] ${h.text}`);
    });
  }

  await browser.close();
})();
