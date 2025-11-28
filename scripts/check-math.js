// check-math.js
// Usage: node scripts/check-math.js <url>
// Finds text nodes containing raw math markers or LaTeX commands likely not rendered.

const { chromium } = require('playwright');
const url = process.argv[2];
if (!url) {
  console.error('Usage: node scripts/check-math.js <url>');
  process.exit(1);
}

const patterns = [
  /\$\$/,            // raw $$ block markers
  /\$(.+?)\$/,       // raw inline $ ... $
  /\\frac\{/        // visible LaTeX fraction
];

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: 'networkidle' });

  const texts = await page.$$eval('body *', nodes => {
    const out = [];
    for (const n of nodes) {
      const child = n.firstChild;
      if (!child || child.nodeType !== Node.TEXT_NODE) continue;
      const t = child.textContent || '';
      const trimmed = t.trim();
      if (trimmed.length === 0) continue;
      out.push(trimmed);
    }
    return out;
  });

  const hits = [];
  texts.forEach((t, idx) => {
    if (patterns.some(p => p.test(t))) hits.push({ idx, text: t });
  });

  console.log(`Checked ${texts.length} text nodes on ${url}`);
  if (hits.length === 0) {
    console.log('No raw math markers found.');
  } else {
    console.log('Potential unrendered math:');
    hits.forEach(h => console.log(`- [${h.idx}] ${h.text}`));
  }

  await browser.close();
})();
