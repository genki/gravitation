// check-math.js
// Usage: node scripts/check-math.js <url>
// Detect raw math markers in visible innerText only.

const { chromium } = require('playwright');
const url = process.argv[2];
if (!url) {
  console.error('Usage: node scripts/check-math.js <url>');
  process.exit(1);
}

const patterns = [
  /\$\$/,            // raw $$
  /\$(.+?)\$/,       // raw inline
  /\\frac\{/        // visible LaTeX
];

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: 'networkidle' });

  const texts = await page.$$eval('body *', nodes => {
    const out = [];
    for (const n of nodes) {
      const t = n.innerText;
      if (!t) continue;
      const trimmed = t.trim();
      if (!trimmed) continue;
      out.push(trimmed);
    }
    return out;
  });

  const hits = [];
  texts.forEach((t, idx) => {
    if (patterns.some(p => p.test(t))) hits.push({ idx, text: t });
  });

  console.log(`Checked ${texts.length} text nodes (innerText) on ${url}`);
  if (hits.length === 0) {
    console.log('No raw math markers found.');
  } else {
    console.log('Potential unrendered math:');
    hits.forEach(h => console.log(`- [${h.idx}] ${h.text}`));
  }

  await browser.close();
})();
