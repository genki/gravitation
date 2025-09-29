#!/usr/bin/env python3
from __future__ import annotations
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests


def build_base() -> str:
    base = os.environ.get('E2E_BASE', '').strip()
    if base:
        return base if base.endswith('/') else base + '/'
    tok = os.environ.get('AGENT_TOKEN', '').strip()
    if tok:
        return f"https://agent-gate.s21g.com/moon/{tok}/@localhost:3131/"
    return "http://localhost:3131/"


@dataclass
class Check:
    path: str
    expect: int = 200
    kind: str = 'html'


class E2E:
    def __init__(self, base: str, session: requests.Session) -> None:
        self.base = base
        self.s = session
        self.logs: list[str] = []
        self.passes = 0
        self.fails = 0

    def log(self, msg: str) -> None:
        self.logs.append(msg)
        print(msg)

    def fetch(self, url: str) -> tuple[int, str, str]:
        try:
            r = self.s.get(url, timeout=8)
            return r.status_code, r.headers.get('Content-Type', ''), r.text
        except Exception as e:
            self.log(f"ERR fetch {url}: {e}")
            return 0, '', ''

    def check_page(self, c: Check) -> None:
        url = urljoin(self.base, c.path.lstrip('/'))
        st, ct, body = self.fetch(url)
        if st != c.expect:
            self.fails += 1
            self.log(f"FAIL {c.path}: status {st} != {c.expect}")
            return
        # basic html checks
        if 'text/html' in ct:
            # stylesheet link must exist and resolve
            css_matches = re.findall(r'<link[^>]+href="([^"]*styles\.css)"', body, flags=re.I)
            if css_matches:
                css_href = css_matches[0]
                css_url = urljoin(url, css_href)
                st2, ct2, _ = self.fetch(css_url)
                if st2 != 200 or 'text/css' not in ct2:
                    self.fails += 1
                    self.log(f"FAIL css {css_url}: status={st2} ct={ct2}")
                else:
                    self.passes += 1
                    self.log(f"OK css {css_url}")
            else:
                self.fails += 1
                self.log(f"FAIL {c.path}: stylesheet link not found")
            # relative links check: avoid href="/..." within body (allow absolute http(s))
            bad_abs = re.findall(r'href="/(?!/)[^\"]+"', body)
            if bad_abs:
                self.fails += 1
                self.log(f"FAIL {c.path}: found absolute href(s): {bad_abs[:3]}")
            else:
                self.passes += 1
                self.log(f"OK relative hrefs in {c.path}")
            # nav links sanity (up to 3)
            nav_links = re.findall(r'<nav[^>]*>(.*?)</nav>', body, flags=re.I|re.S)
            if nav_links:
                hrefs = re.findall(r'href="([^"]+)"', nav_links[0])[:3]
                for h in hrefs:
                    stn, _, _ = self.fetch(urljoin(url, h))
                    if stn == 200:
                        self.passes += 1
                        self.log(f"OK nav {h}")
                    else:
                        self.fails += 1
                        self.log(f"FAIL nav {h}: {stn}")
        else:
            self.passes += 1
            self.log(f"OK non-html {c.path} ct={ct}")

    def run(self) -> int:
        self.log(f"BASE {self.base}")
        checks = [
            Check('/'),
            Check('/index.html'),
            Check('/state_of_the_art/index.html'),
            Check('/reports/index.html'),
            Check('/notifications/'),
            Check('/TODO.md'),
            Check('/memos.html'),
            Check('/data.html'),
            Check('/paper.html'),
            Check('/galaxies/index.html'),
        ]
        for c in checks:
            self.check_page(c)
        self.log(f"summary: pass={self.passes} fail={self.fails}")
        self.write_report()
        return 0 if self.fails == 0 else 2

    def write_report(self) -> None:
        out = Path('server/public/reports/e2e_site.html')
        out.parent.mkdir(parents=True, exist_ok=True)
        html = [
            '<!doctype html><html lang="ja-JP"><head><meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width,initial-scale=1">',
            '<title>E2E Site Check</title><link rel="stylesheet" href="../styles.css"></head><body>',
            '<header class="site-header"><div class="wrap"><div class="brand">E2E</div>'
            '<nav class="nav"><a href="../index.html">ホーム</a></nav></div></header>',
            '<main class="wrap">',
            f'<h1>E2E Site Check</h1><p>BASE: {self.base}</p><ul>'
        ]
        for ln in self.logs:
            cls = 'ok' if ln.startswith('OK') else ('fail' if ln.startswith('FAIL') or ln.startswith('ERR') else 'info')
            html.append(f'<li class="{cls}">{ln}</li>')
        html.append(f"</ul><p>pass={self.passes} fail={self.fails}</p></main>")
        html.append('<footer class="site-footer"><div class="wrap">ローカル配信</div></footer></body></html>')
        out.write_text("\n".join(html), encoding='utf-8')
        print('wrote', out)


def main() -> int:
    base = build_base()
    s = requests.Session()
    s.headers.update({'User-Agent': 'gravitation-e2e/1.0'})
    return E2E(base, s).run()


if __name__ == '__main__':
    raise SystemExit(main())

