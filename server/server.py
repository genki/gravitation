#!/usr/bin/env python3
import os
import re
import ssl
import sys
from http.server import (ThreadingHTTPServer,
                         SimpleHTTPRequestHandler)
import json
import subprocess
import time
import mimetypes
from pathlib import Path


def main() -> int:
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "3131"))
    use_tls = (os.environ.get('NO_TLS', '') != '1')

    here = Path(__file__).resolve().parent
    pub = here / "public"
    repo_root = here.parent
    memo_dir = repo_root / "memo"
    paper_dir = repo_root / "paper"
    data_dir = repo_root / "data"
    fig_dir = here.parent / "paper" / "figures"
    if not pub.exists():
        print(f"error: missing public dir: {pub}", file=sys.stderr)
        return 1

    cert_dir = here / "certs"
    crt = cert_dir / "dev.crt"
    key = cert_dir / "dev.key"
    if use_tls and not (crt.exists() and key.exists()):
        print("error: missing TLS cert/key. Run scripts/gen_dev_cert.sh",
              file=sys.stderr)
        return 1

    # Python 3.7+: directory=pub for static root
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            # MIMEタイプ拡張とcharset付与
            ext_map = mimetypes.types_map.copy()
            ext_map.update({
                ".md": "text/markdown",
                ".tex": "text/x-tex",
                ".csv": "text/csv",
            })
            self.extensions_map = {
                k: (v + "; charset=utf-8")
                if v.startswith("text/") else v
                for k, v in ext_map.items()
            }
            super().__init__(*args, directory=str(pub), **kwargs)

        def end_headers(self) -> None:
            # すべての応答に言語ヘッダを付与
            self.send_header("Content-Language", "ja-JP")
            # site-lastmod.js は頻繁に更新されるためキャッシュしない
            try:
                if getattr(self, 'path', '').endswith('/site-lastmod.js') or getattr(self, 'path', '') == '/site-lastmod.js':
                    self.send_header('Cache-Control', 'no-store, max-age=0, must-revalidate')
            except Exception:
                pass
            super().end_headers()

        # ---- Markdown レンダリング ----
        def do_GET(self):  # type: ignore[override]
            if self.path == "/healthz":
                return self._serve_health()
            # Dynamic SOTA: only for the index route; allow static subpages under the path
            if self.path.rstrip('/') == "/state_of_the_art":
                return self._serve_sota()
            if self.path == "/state_of_the_art/index.html":
                return self._serve_sota()
            if self.path.rstrip('/') in ("/todo",):
                return self._serve_todo()
            if self.path.endswith(".md"):
                return self._serve_markdown()
            if self.path in ("/figures", "/figures/", "/figures.html"):
                return self._serve_figures()
            # repo直下の参照を一部プロキシ
            if (self.path.startswith("/paper/") or
                    self.path.startswith("/data/")):
                return self._serve_repo_file()
            return super().do_GET()

        def do_HEAD(self):  # type: ignore[override]
            if self.path.endswith(".md"):
                self.send_response(200)
                self.send_header("Content-Type",
                                 "text/html; charset=utf-8")
                self.end_headers()
                return
            if self.path in ("/figures", "/figures/", "/figures.html"):
                self.send_response(200)
                self.send_header("Content-Type",
                                 "text/html; charset=utf-8")
                self.end_headers()
                return
            return super().do_HEAD()

        def do_POST(self):  # type: ignore[override]
            if self.path == "/api/todo":
                return self._handle_todo_post()
            self.send_error(404, "unknown POST")
            return

        def _serve_markdown(self) -> None:
            # /memo/, /paper/ はrepo直下を参照
            req = self.path
            if req.startswith("/memo/"):
                src_path = memo_dir / req[len("/memo/"):]
            elif req.startswith("/paper/"):
                src_path = paper_dir / req[len("/paper/"):]
            else:
                src_path = Path(self.translate_path(req))
            if not src_path.exists() or not src_path.is_file():
                self.send_error(404, "File not found")
                return
            try:
                text = src_path.read_text(encoding="utf-8")
            except Exception as e:  # noqa: BLE001
                self.send_error(500, f"read error: {e}")
                return

            body = self._md_to_html(text)
            # Append add form at the end of /TODO.md
            try:
                req_norm = self.path.lower()
                if req_norm.endswith('/todo.md') or req_norm == '/todo.md':
                    pref = self._root_prefix()
                    form_html = (
                        '<hr>'
                        '<div class="card">'
                        '<h2>TODOを追加</h2>'
                        f'<form method="post" action="{pref}api/todo">'
                        '<input name="item" placeholder="新しいTODO..." '
                        'style="width:70%" required> '
                        '<button type="submit">追加</button>'
                        '</form>'
                        '<p class="help">ここから追加すると TODO.md の末尾に追記されます。</p>'
                        '</div>'
                    )
                    body = body + "\n" + form_html
            except Exception:
                pass
            html = self._wrap_html(title=src_path.name, body=body)

            data = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type",
                             "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _serve_repo_file(self) -> None:
            # /paper/, /data/ をrepo直下から配信（?query, #frag を除去）
            path = self.path
            # strip query and fragment for filesystem lookup
            for sep in ('?', '#'):
                if sep in path:
                    path = path.split(sep, 1)[0]
            if path.startswith("/paper/"):
                src = paper_dir / path[len("/paper/"):]
            elif path.startswith("/data/"):
                src = data_dir / path[len("/data/"):]
            else:
                self.send_error(404, "unsupported repo path")
                return

            if not src.exists() or not src.is_file():
                self.send_error(404, "File not found")
                return

            ctype, _ = mimetypes.guess_type(str(src))
            if ctype is None:
                ctype = "application/octet-stream"

            try:
                data = src.read_bytes()
            except Exception as e:  # noqa: BLE001
                self.send_error(500, f"read error: {e}")
                return

            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        # ---- TODO page ----
        def _serve_todo(self) -> None:
            todo = here.parent / 'TODO.md'
            items: list[str] = []
            if todo.exists():
                try:
                    lines = todo.read_text(encoding='utf-8').splitlines()
                    start = 0
                    for i, ln in enumerate(lines):
                        if ln.strip() == '---':
                            start = i + 1
                            break
                    seen = False
                    for ln in lines[start:]:
                        if ln.strip().lower().startswith('backlog'):
                            seen = True
                            continue
                        if not seen:
                            continue
                        if ln.strip():
                            items.append(ln.strip())
                except Exception:
                    pass
            pref = self._root_prefix()
            rows = ["<h1>研究TODO</h1>", f"<div class=card><form method=post action={pref}api/todo>"
                    "<input type=text name=item placeholder='TODO項目を1行で' style='width:70%'> "
                    "<button type=submit>追加</button></form></div>", "<ul>"]
            if items:
                for it in items:
                    rows.append(f"<li>{self._esc(it)}</li>")
            else:
                rows.append("<li><em>Backlogは空です。</em></li>")
            rows.append("</ul>")
            html = self._wrap_html(title="TODO", body="\n".join(rows))
            data = html.encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _handle_todo_post(self) -> None:
            length = int(self.headers.get('Content-Length', '0'))
            data = self.rfile.read(length) if length > 0 else b''
            try:
                payload = data.decode('utf-8', errors='ignore')
                # very simple application/x-www-form-urlencoded parser
                from urllib.parse import parse_qs
                qs = parse_qs(payload)
                item = qs.get('item', [''])[0].strip()
                if item:
                    todo = here.parent / 'TODO.md'
                    if todo.exists():
                        s = todo.read_text(encoding='utf-8')
                    else:
                        s = "# TODO\n\n---\n\nBacklog:\n\n"
                    if not s.endswith("\n"): s += "\n"
                    s += item + "\n"
                    todo.write_text(s, encoding='utf-8')
            except Exception:
                pass
            # redirect back (relative to /api/)
            self.send_response(302)
            self.send_header('Location', '../todo')
            self.end_headers()

        # ---- Figures gallery ----
        def _serve_figures(self) -> None:
            img_exts = {".png", ".jpg", ".jpeg", ".gif", ".svg"}
            items = []
            if fig_dir.exists() and fig_dir.is_dir():
                for p in sorted(fig_dir.iterdir()):
                    if p.suffix.lower() in img_exts and p.is_file():
                        rel = f"/paper/figures/{p.name}"
                        size = self._human_size(p.stat().st_size)
                        items.append((p.name, rel, size))

            body_lines = ["<h1>図ギャラリー</h1>"]
            if not items:
                if not fig_dir.exists():
                    body_lines.append(
                        "<p>paper/figures が見つかりません。</p>")
                else:
                    body_lines.append(
                        "<p>表示可能な画像がありません。</p>")
            else:
                body_lines.append('<div class="gallery">')
                for name, url, size in items:
                    body_lines.append(
                        "<figure class=\"thumb\">"
                        f"<a href=\"{url}\" target=\"_blank\">"
                        f"<img src=\"{url}\" alt=\"{self._esc(name)}\"" \
                        " loading=\"lazy\"></a>"
                        f"<figcaption>{self._esc(name)} ({size})"
                        "</figcaption></figure>"
                    )
                body_lines.append("</div>")

            html = self._wrap_html(title="Figures",
                                    body="\n".join(body_lines))
            data = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type",
                             "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _serve_health(self) -> None:
            data = b"ok\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        # ---- Dynamic SOTA ----
        def _serve_sota(self) -> None:
            # If a prebuilt static page exists, serve it (keeps parity with docs/SOTA).
            static = (here / 'public' / 'state_of_the_art' / 'index.html')
            if static.exists():
                try:
                    data = static.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
                except Exception as e:
                    print(f"[SOTA] failed to serve static: {e}", file=sys.stderr)

            # Regenerate SOTA figures if results are newer or missing
            try:
                self._maybe_regen_sota()
            except Exception as e:  # noqa: BLE001
                print(f"[SOTA] regen failed: {e}", file=sys.stderr)

            # Read metrics summary if available
            metrics = []
            try:
                csvp = (here.parent / 'assets' / 'results' / 'global_fit_summary.csv')
                if csvp.exists():
                    lines = csvp.read_text(encoding='utf-8').splitlines()
                    for ln in lines[1:]:
                        parts = ln.split(',')
                        if len(parts) >= 2:
                            metrics.append((parts[0], parts[1]))
            except Exception:
                pass

            body_lines = ["<h1>State of the Art</h1>"]
            # Progress banner (prev -> current) from data/progress.json
            try:
                p = here.parent / 'data' / 'progress.json'
                if p.exists():
                    data = json.loads(p.read_text(encoding='utf-8'))
                    hist = data.get('history', [])
                    if hist:
                        prev = hist[-2] if len(hist) >= 2 else None
                        cur = hist[-1]
                        pr_txt = (
                            (f"{float(prev['rate']):.0f}%" if prev else "—%")
                            + " → " + f"{float(cur['rate']):.0f}%"
                        )
                        when = f"<small>{cur.get('ts','')}</small>"
                        body_lines.append(
                            f"<div class=card><p><b>進捗率</b>: {pr_txt} {when}</p></div>"
                        )
            except Exception:
                pass
            # 用語注記: FDB の正式名称を明示
            body_lines.append(
                '<div class="card"><b>注:</b> FDB = Future Decoherence Bias '
                '（ULW-EM に起因する見かけ重力）。FDB3 はその3パラメータ型、'
                'FDBL は3D拡張型を表します。</div>'
            )
            if metrics:
                body_lines.append('<div class="card"><ul>')
                for k, v in metrics:
                    body_lines.append(f"<li>{self._esc(k)}: {self._esc(v)}</li>")
                body_lines.append('</ul></div>')

            figs = [
                ('改善ヒストグラム', '/paper/figures/sota_improvement_hist.png',
                 '全銀河の適合改善倍率 $\\mathrm{red}\\,\\chi^2_{\\rm GR}/\\mathrm{red}\\,\\chi^2_{\\rm FDB3}$ のヒストグラム。右側（大きい値）ほどFDB3がGR(no DM)より良い適合を与えることを示す。対数軸で裾を含めた分布を可視化。'),
                ('redχ² 散布図', '/paper/figures/sota_redchi2_scatter.png',
                 '各銀河の $(\\mathrm{red}\\,\\chi^2_{\\rm GR},\\ \\mathrm{red}\\,\\chi^2_{\\rm FDB3})$ 散布図。破線は等値線。点が破線より下に位置するほどFDB3の方が良い（小さい）赤化二乗。両対数表示で広いレンジを比較。'),
                ('VR パネル', '/paper/figures/sota_vr_panel.png',
                 '代表銀河の回転曲線。黒点は観測$V_{\\rm obs}$（誤差棒付き）、青はGR(no DM)（バリオンのみ）、橙はFDB3。内外縁の傾向差や外縁平坦域の再現性を視覚的に比較する。'),
                ('VR パネル（worst）', '/paper/figures/sota_vr_panel_worst.png',
                 '改善倍率が小さい（悪化/未改善）銀河から構成したワーストケース。FDB3の課題や系統的乖離の傾向を把握するための対照パネル。'),
            ]
            body_lines.append('<h2>SOTA 図</h2><div class="two-col">')
            for cap, url, caplong in figs:
                body_lines.append(
                    '<figure class="card">'
                    f'<img src="{url}" alt="{self._esc(cap)}" '
                    'style="max-width:100%;height:auto">'
                    f'<figcaption><b>{self._esc(cap)}</b><br>{self._esc(caplong)}</figcaption>'
                    '</figure>'
                )
            body_lines.append('</div>')

            # 基盤的な方程式群と記号解説（MathJaxレンダリング）
            eq = []
            eq.append('<h2>基盤方程式と記号</h2>')
            eq.append('<div class="card">')
            eq.append('<p><b>情報ポテンシャル</b> と 条件付き到達確率:</p>')
            eq.append(r"$$U_{\mathrm{info}}(\mathbf{x},t)=\kappa\,\ln h(\mathbf{x},t),\quad h(\mathbf{x},t)=\mathbb{P}(E\mid \mathbf{x}_t=\mathbf{x}).$$")
            eq.append('<p><b>生成子のDoobの</b> <i>h</i> <b>変換</b> と 拡散極限の見かけドリフト:</p>')
            eq.append(r"$$\mathcal{L}^{(E)} f = h^{-1}\,\mathcal{L}(h f),\qquad b_{\rm eff}=b+2D\,\nabla\ln h.$$")
            eq.append('<p><b>見かけの運動方程式</b> と 見かけ保存則:</p>')
            eq.append(r"$$m\,\ddot{\mathbf{x}}=-\nabla U_{\mathrm{info}}=-\kappa\,\nabla\ln h,\qquad \frac{d}{dt}\bigl[K+U_{\mathrm{info}}\bigr]=0.$$")
            eq.append('<p><b>弱場規格化</b>（等価原理とレンズ係数2の整合）:</p>')
            eq.append(r"$$\kappa=m c^2,\ \ h=\exp(\Phi_{\rm eff}/c^2)\ \Rightarrow\ U_{\mathrm{info}}=m\,\Phi_{\rm eff},\ \ddot{\mathbf{x}}=-\nabla\Phi_{\rm eff}. $$")
            eq.append(r"$$U_{\mathrm{info}}^{(\gamma)}=(p/c)\,\Phi_{\rm eff},\qquad \hat\alpha=2\int \nabla_\perp\!(\Phi_{\rm eff}/c^2)\,ds.$$")
            eq.append('<p><b>幾何バイアス</b>（遠方近似）:</p>')
            eq.append(r"$$h\propto 1/d^2\ \Rightarrow\ \nabla\ln h=-2\,\nabla\ln d\ (\text{観測者方向}).$$")
            eq.append('</div>')

            eq.append('<div class="card">')
            eq.append('<p><b>記号の解説</b>（主要なもの）</p>')
            eq.append('<ul>')
            eq.append(r'<li>$h(\mathbf{x},t)$: 将来の記録事象 $E$ の条件付き到達確率</li>')
            eq.append(r'<li>$U_{\mathrm{info}}$, $\kappa$: 情報ポテンシャルと規格化定数（弱場で $mc^2$）</li>')
            eq.append(r'<li>$\Phi_{\rm eff}$, $m$, $p$: 有効ポテンシャル（設計層）・質量・光の運動量</li>')
            eq.append(r'<li>$\mathcal{L}$, $b$, $D$: 基準過程の生成子・ドリフト・拡散係数</li>')
            eq.append(r'<li>$\hat\alpha$, $c$: 弱重力レンズの偏向角・光速</li>')
            eq.append('</ul>')
            eq.append('</div>')

            body_lines.extend(eq)

            # データ更新時刻（結果CSV/図の最終更新）を算出し、クライアントへ渡す
            repo = here.parent
            res_dir = repo / 'assets' / 'results'
            fig_dst = repo / 'paper' / 'figures'
            res_csv = res_dir / 'fdb3_per_galaxy.csv'
            gsum_csv = res_dir / 'global_fit_summary.csv'
            targets = [
                fig_dst / 'sota_improvement_hist.png',
                fig_dst / 'sota_redchi2_scatter.png',
                fig_dst / 'sota_vr_panel.png',
                fig_dst / 'sota_vr_panel_worst.png',
            ]
            def mtime(p: Path) -> float:
                try:
                    return p.stat().st_mtime
                except Exception:
                    return 0.0
            res_m = max(mtime(res_csv), mtime(gsum_csv))
            figs_m = min(mtime(t) for t in targets) if all(t.exists() for t in targets) else 0.0
            # Always reflect "now" at least, so viewers see the page as updated even
            # when source CSV/figs mtimes are stale (e.g., rsync/cp preserved mtimes).
            last_epoch = int(max(res_m, figs_m, time.time()) * 1000)
            body_lines.append(
                f"<script>window.SOTA_LAST_UPDATED={last_epoch};"
                "document.dispatchEvent(new CustomEvent('sota:lastmod'));</script>"
            )

            html = self._wrap_html(title="State of the Art",
                                    body="\n".join(body_lines))
            data = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type",
                             "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _maybe_regen_sota(self) -> None:
            """Regenerate SOTA figures if results CSV is newer than figures or missing.
            Runs lightweight plotting and sync scripts only (no full fits).
            """
            repo = here.parent
            res_dir = repo / 'assets' / 'results'
            fig_dst = repo / 'paper' / 'figures'
            res_csv = res_dir / 'fdb3_per_galaxy.csv'
            gsum_csv = res_dir / 'global_fit_summary.csv'
            targets = [
                fig_dst / 'sota_improvement_hist.png',
                fig_dst / 'sota_redchi2_scatter.png',
                fig_dst / 'sota_vr_panel.png',
            ]

            def mtime(p: Path) -> float:
                try:
                    return p.stat().st_mtime
                except Exception:
                    return 0.0

            res_m = max(mtime(res_csv), mtime(gsum_csv))
            figs_m = min(mtime(t) for t in targets) if all(t.exists() for t in targets) else 0.0
            need = (res_m > figs_m) or any(not t.exists() for t in targets)
            if not need:
                return

            # Run plotting + sync (best-effort)
            py = repo / '.venv' / 'bin' / 'python'
            cmd1 = [str(py), str(repo / 'scripts' / 'plot_sota_figs.py')]
            cmd2 = [str(py), str(repo / 'scripts' / 'plot_compare_shared.py'), 'DDO154', 'DDO161']
            cmd3 = ['bash', str(repo / 'scripts' / 'sync_figs_to_paper.sh')]
            for cmd in (cmd1, cmd2, cmd3):
                try:
                    subprocess.run(cmd, cwd=str(repo), check=True,
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
                except Exception as e:  # noqa: BLE001
                    print(f"[SOTA] command failed: {cmd}: {e}", file=sys.stderr)
                    break

        def _human_size(self, n: int) -> str:
            for unit in ("B", "KB", "MB", "GB"):
                if n < 1024 or unit == "GB":
                    return f"{n:.0f}{unit}"
                n /= 1024
            return f"{n:.0f}B"

        def _root_prefix(self) -> str:
            try:
                path = getattr(self, 'path', '/')
            except Exception:
                path = '/'
            for sep in ('?', '#'):
                if sep in path:
                    path = path.split(sep, 1)[0]
            segs = [s for s in path.strip('/').split('/') if s]
            # Depth should be based on directory count, not segments total.
            # Example: '/TODO.md' -> depth 0; '/state_of_the_art/index.html' -> depth 1
            depth = max(len(segs) - 1, 0)
            return '' if depth == 0 else ('../' * depth)

        def _wrap_html(self, *, title: str, body: str) -> str:
            prefix = self._root_prefix()
            return (
                "<!doctype html>\n"
                "<html lang=\"ja-JP\">\n<head>\n"
                "  <meta charset=\"utf-8\">\n"
                "  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
                f"  <title>{self._esc(title)}</title>\n"
                f"  <link rel=\"stylesheet\" href=\"{prefix}styles.css\">\n"
                f"  <script defer src=\"{prefix}site-lastmod.js\"></script>\n"
                "  <script>window.MathJax={tex:{inlineMath:[['$','$'],['\\(','\\)']]}};</script>\n"
                "  <script id=\"MathJax-script\" async\n"
                "    src=\"https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js\"></script>\n"
                "</head>\n<body>\n"
                "  <header class=\"site-header\">\n"
                "    <div class=\"wrap\">\n"
                "      <div class=\"brand\">研究進捗</div>\n"
                "      <nav class=\"nav\">\n"
                f"        <a href=\"{prefix}index.html\">ホーム</a>\n"
                f"        <a href=\"{prefix}memos.html\">メモ</a>\n"
                f"        <a href=\"{prefix}data.html\">データ</a>\n"
                f"        <a href=\"{prefix}paper.html\">論文</a>\n"
                "      </nav>\n"
                "    </div>\n"
                "  </header>\n"
                "  <main class=\"wrap\">\n" + body + "\n  </main>\n"
                "  <footer class=\"site-footer\">\n"
                "    <div class=\"wrap\">\n"
                f"      <span>{'自己署名TLS' if use_tls else 'HTTP'}で配信(開発用)</span>\n"
                "    </div>\n"
                "  </footer>\n"
                "</body>\n</html>\n"
            )

        def _esc(self, s: str) -> str:
            return (s.replace("&", "&amp;")
                      .replace("<", "&lt;")
                      .replace(">", "&gt;")
                      .replace('"', "&quot;"))

        def _md_to_html(self, s: str) -> str:
            lines = s.splitlines()
            out: list[str] = []
            in_code = False
            in_ul = False

            def flush_ul() -> None:
                nonlocal in_ul
                if in_ul:
                    out.append("</ul>")
                    in_ul = False

            for ln in lines:
                if ln.startswith("```"):
                    flush_ul()
                    if not in_code:
                        out.append("<pre><code>")
                        in_code = True
                    else:
                        out.append("</code></pre>")
                        in_code = False
                    continue

                if in_code:
                    out.append(self._esc(ln))
                    continue

                if not ln.strip():
                    flush_ul()
                    out.append("")
                    continue

                m = re.match(r"^(#{1,6})\s+(.*)$", ln)
                if m:
                    flush_ul()
                    level = len(m.group(1))
                    text = self._md_inline(m.group(2))
                    out.append(f"<h{level}>{text}</h{level}>")
                    continue

                if re.match(r"^[-*]\s+", ln):
                    if not in_ul:
                        out.append("<ul>")
                        in_ul = True
                    item = re.sub(r"^[-*]\s+", "", ln)
                    out.append(f"<li>{self._md_inline(item)}</li>")
                    continue

                if in_ul and ln.startswith("  "):
                    # 箇条書き項目の継続行を直前<li>に追記
                    if out and out[-1].startswith("<li>"):
                        cont = self._md_inline(ln.strip())
                        out[-1] = out[-1][:-5] + " " + cont + "</li>"
                        continue

                # paragraph
                out.append(f"<p>{self._md_inline(ln)}</p>")

            flush_ul()
            return "\n".join(out)

        def _md_inline(self, t: str) -> str:
            t = self._esc(t)
            # strong/em
            t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
            t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
            # code
            t = re.sub(r"`([^`]+?)`", r"<code>\1</code>", t)
            # links [text](url)
            t = re.sub(r"\[(.+?)\]\((.+?)\)",
                       r"<a href=\"\2\">\1</a>", t)
            # autolink bare URLs (http/https) not already inside href="..."
            def _auto(m: re.Match[str]) -> str:
                url = m.group(0)
                return f"<a href=\"{url}\">{url}</a>"
            t = re.sub(r"(?<!\")\bhttps?://[^\s<)]+", _auto, t)
            return t

    httpd = ThreadingHTTPServer((host, port), Handler)
    if use_tls:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(certfile=str(crt), keyfile=str(key))
        httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)

    scheme = 'https' if use_tls else 'http'
    print(f"{scheme.upper()} serving {pub} at {scheme}://{host}:{port}")
    print(f"note: access via {scheme}://localhost:{port} in browsers")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
