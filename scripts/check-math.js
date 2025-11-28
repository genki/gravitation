// check-math.js
// Usage: node scripts/check-math.js <url>
// Detect raw math markers ($, $$, \frac{) in wiki article text (wiki-body).

const { chromium } = require('playwright');
const url = process.argv[2];
if (!url) {
  console.error('Usage: node scripts/check-math.js <url>');
  process.exit(1);
}

const patterns = [/\$\$/, /\$(.+?)\$/, /\\frac\{/];

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: 'networkidle' });

  const bodyText = await page.$eval('#wiki-body', el => el.innerText);
  const lines = bodyText.split(/\n+/).map(l => l.trim()).filter(Boolean);

  const hits = [];
  lines.forEach((line, idx) => {
    if (patterns.some(p => p.test(line))) hits.push({ idx: idx + 1, text: line });
  });

  console.log(`Checked ${lines.length} lines (wiki-body) on ${url}`);
  if (hits.length === 0) {
    console.log('No raw math markers found.');
  } else {
    console.log('Potential unrendered math:');
    hits.forEach(h => console.log(`- [line ${h.idx}] ${h.text}`));
  }

  await browser.close();
})();
