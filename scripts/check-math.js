// check-math.js
// Usage: node scripts/check-math.js <url>
// Detect raw math markers ($, $$, \frac{, and \(...\) style) in wiki article text.

const { chromium } = require('playwright');
const url = process.argv[2];
if (!url) {
  console.error('Usage: node scripts/check-math.js <url>');
  process.exit(1);
}

const patterns = [
  /\$\$/,           // block markers
  /\$(.+?)\$/,      // inline $ ... $
  /\\frac\{/,      // LaTeX fraction raw
  /\(.*\\.*\)/     // parenthesis containing backslash (\(...\) style)
];

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: 'networkidle' });
  // allow client-side math renderer to replace delimiters
  await page.waitForTimeout(3000);

  const bodyText = await page.$eval('#wiki-body', el => el.innerText);
  const bodyHtml = await page.$eval('#wiki-body', el => el.innerHTML);
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

  // Detect MathML rendering errors highlighted as red (mathcolor="red")
  const redRegex = new RegExp('<[^>]*mathcolor=\"red\"[^>]*>([\\s\\S]*?)<\\\\/[^>]+>', 'gi');
  const redMatches = [...bodyHtml.matchAll(redRegex)];
  if (redMatches.length > 0) {
    console.log(`Found ${redMatches.length} MathML elements with mathcolor="red" (likely render errors).`);
    redMatches.forEach((m, i) => {
      // Extract a short, readable snippet without HTML tags
      const snippet = m[0]
        .replace(/<[^>]+>/g, ' ')    // remove tags
        .replace(/\\s+/g, ' ')       // collapse whitespace
        .trim();
      console.log(`  [${i + 1}] ${snippet}`);
    });
  }

  await browser.close();
})();
