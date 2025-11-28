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
  const redRegex = new RegExp('mathcolor=\"red\"', 'i');
  const redMatches = [];

  // 1) body HTML
  if (redRegex.test(bodyHtml)) redMatches.push('[body]');

  // 2) math-renderer shadow/templates
  const redSnippets = await page.$$eval('math-renderer', nodes => {
    const snippets = [];
    nodes.forEach((node, idx) => {
      const collect = (html) => {
        if (html && html.toLowerCase().includes('mathcolor="red"')) {
          const text = html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
          snippets.push({ idx: idx + 1, text });
        }
      };
      // innerHTML of renderer
      collect(node.innerHTML);
      // template content (where GitHub stores MathML)
      const tmpl = node.querySelector('template');
      if (tmpl && tmpl.innerHTML) collect(tmpl.innerHTML);
      if (tmpl && tmpl.content) collect(tmpl.content.innerHTML || '');
    });
    return snippets;
  });

  if (redSnippets.length > 0) {
    console.log(`Found ${redSnippets.length} MathML elements with mathcolor="red" (likely render errors).`);
    redSnippets.forEach(s => console.log(`  [math-renderer ${s.idx}] ${s.text}`));
  } else if (redMatches.length > 0) {
    console.log('Found mathcolor="red" in body HTML.');
  }

  await browser.close();
})();
