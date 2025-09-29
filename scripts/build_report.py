#!/usr/bin/env python3
# HTMLレポート生成: 結果JSONから静的HTMLを生成しserver/publicに配置

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List


def load_json(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def h(s: str) -> str:
    return (
        s.replace("&", "&amp;").replace("<", "&lt;")
        .replace(">", "&gt;").replace('"', "&quot;")
    )


def write_html(out: Path, title: str, body: str) -> None:
    # depth-aware relative prefix from server/public
    try:
        rel = out.resolve().relative_to(Path('server/public').resolve())
        depth = max(len(rel.parts) - 1, 0)
    except Exception:
        depth = 0
    pref = '../' * depth
    html = (
        "<!doctype html>\n"
        "<html lang=\"ja-JP\">\n<head>\n"
        "  <meta charset=\"utf-8\">\n"
        "  <meta name=\"viewport\" "
        "content=\"width=device-width,initial-scale=1\">\n"
        f"  <title>{h(title)}</title>\n"
        f"  <link rel=\"stylesheet\" href=\"{pref}styles.css\">\n"
        "</head>\n<body>\n"
        "  <header class=\"site-header\">\n"
        "    <div class=\"wrap\">\n"
        "      <div class=\"brand\">研究進捗</div>\n"
        "      <nav class=\"nav\">\n"
        f"        <a href=\"{pref}index.html\">ホーム</a>\n"
        f"        <a href=\"{pref}memos.html\">メモ</a>\n"
        f"        <a href=\"{pref}data.html\">データ</a>\n"
        f"        <a href=\"{pref}paper.html\">論文</a>\n"
        f"        <a href=\"{pref}reports/index.html\">レポート</a>\n"
        "      </nav>\n"
        "    </div>\n"
        "  </header>\n"
        "  <main class=\"wrap\">\n" + body + "\n  </main>\n"
        "  <footer class=\"site-footer\">\n"
        "    <div class=\"wrap\">ローカル配信(開発用)</div>\n"
        "  </footer>\n"
        "</body>\n</html>\n"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")


def rr(v: float, n: int = 3) -> str:
    try:
        return f"{v:.{n}g}"
    except Exception:
        return str(v)


def build_multi_report(src: Path, out: Path) -> None:
    data = load_json(src)
    names = data.get("names", [])
    lam = data.get("lam")
    A = data.get("A")
    gscale = data.get("gas_scale")
    chi2_gr = data.get("chi2_total", {}).get("GR")
    chi2_ulw = data.get("chi2_total", {}).get("ULW")
    aic_gr = data.get("AIC", {}).get("GR")
    aic_ulw = data.get("AIC", {}).get("ULW")
    rows = []
    for nm in names:
        mus_gr = data.get("mu", {}).get("GR", {}).get(nm, {})
        mus_ulw = data.get("mu", {}).get("ULW", {}).get(nm, {})
        if isinstance(mus_gr, dict) and ("mu" in mus_gr):
            gr_txt = f"mu={rr(mus_gr['mu'])}"
        else:
            gr_txt = (
                f"mu_d={rr(getattr(mus_gr, 'mu_d', float('nan')))}, "
                f"mu_b={rr(getattr(mus_gr, 'mu_b', float('nan')))}"
            ) if isinstance(mus_gr, dict) else f"mu={rr(mus_gr)}"
        if isinstance(mus_ulw, dict) and ("mu" in mus_ulw):
            ulw_txt = f"mu={rr(mus_ulw['mu'])}"
        else:
            if isinstance(mus_ulw, dict):
                ulw_txt = (
                    f"mu_d={rr(mus_ulw.get('mu_d', float('nan')))}, "
                    f"mu_b={rr(mus_ulw.get('mu_b', float('nan')))}"
                )
            else:
                ulw_txt = f"mu={rr(mus_ulw)}"
        rows.append((nm, gr_txt, ulw_txt))

    items = []
    items.append("<h1>複数銀河・共有パラメータ比較レポート</h1>")
    items.append("<p>ソース: " + h(str(src)) + "</p>")
    items.append("<div class=card>")
    items.append(
        f"<p>共有パラメータ: λ={rr(lam)} kpc, A={rr(A)}, "
        f"gas_scale={rr(gscale)}</p>"
    )
    items.append(
        f"<p>合計χ²: GR={rr(chi2_gr,5)} / ULW={rr(chi2_ulw,5)}</p>"
    )
    if aic_gr is not None and aic_ulw is not None:
        items.append(
            f"<p>AIC: GR={rr(aic_gr,5)} / ULW={rr(aic_ulw,5)} "
            f"(ΔAIC={rr((aic_ulw - aic_gr),4)})</p>"
        )
    items.append("</div>")
    items.append("<table><thead><tr><th>Galaxy</th><th>GR</th>"
                 "<th>ULW</th></tr></thead><tbody>")
    for nm, gr_txt, ulw_txt in rows:
        items.append(
            f"<tr><td>{h(nm)}</td><td>{h(gr_txt)}</td><td>{h(ulw_txt)}</td>"
            "</tr>"
        )
    items.append("</tbody></table>")
    # Embed figures per galaxy if present
    figdir = Path("paper/figures")
    # helper: compute short galaxy note (type, distance, inclination, curve shape)
    def galaxy_note(nm: str) -> str:
        try:
            from scripts.fit_sparc_fdbl import read_sparc_meta, read_sparc_massmodels
            from pathlib import Path as _P
            meta = read_sparc_meta(_P("data/sparc/SPARC_Lelli2016c.mrt"), nm)
            rc = read_sparc_massmodels(_P("data/sparc/MassModels_Lelli2016c.mrt"), nm)
            import numpy as _np
            # outer slope
            idx = _np.argsort(rc.R)
            Rn, Vn = rc.R[idx], rc.Vobs[idx]
            slope, shape = 0.0, "?"
            if len(Rn) >= 4:
                a = int(0.7 * len(Rn)); b = len(Rn) - 1
                slope = float((Vn[b] - Vn[a]) / max(Rn[b] - Rn[a], 1e-6))
                shape = "rising" if slope > 1.0 else ("declining" if slope < -1.0 else "flat")
            Tmap = {0:"S0",1:"Sa",2:"Sab",3:"Sb",4:"Sbc",5:"Sc",6:"Scd",7:"Sd",8:"Sdm",9:"Sm",10:"Im",11:"BCD"}
            tstr = Tmap.get(getattr(meta, 'T', None), str(getattr(meta, 'T', '?'))) if meta else "?"
            dstr = f"{getattr(meta,'D_mpc', '?')} Mpc" if meta and (meta.D_mpc is not None) else "? Mpc"
            inc = getattr(meta, 'Inc_deg', None); incstr = f"{inc:.0f}°" if isinstance(inc, float) else "?"
            # gas fraction at outer radius using ULW mu if available
            mu_ulw = None
            try:
                muinfo = data.get("mu", {}).get("ULW", {}).get(nm, {})
                if isinstance(muinfo, dict) and "mu" in muinfo:
                    mu_ulw = float(muinfo["mu"])
            except Exception:
                pass
            import math as _m
            i_last = int(_np.nanargmax(Rn))
            g_gas = (rc.Vgas[i_last]**2)/max(rc.R[i_last],1e-6)
            vstar2 = rc.Vdisk[i_last]**2 + rc.Vbul[i_last]**2
            g_star = vstar2/max(rc.R[i_last],1e-6)
            if mu_ulw is None:
                mu_ulw = 0.5
            f_gas = g_gas / max(g_gas + mu_ulw*g_star, 1e-12)
            ftag = "gas-rich" if f_gas>0.5 else ("baryon-balanced" if f_gas>0.3 else "star-dominated")
            return f"Type: {h(tstr)} / D: {h(str(dstr))} / Inc: {h(incstr)} / outer slope: {slope:.2f} ({shape}) / gas frac@Rmax: {f_gas:.2f} ({ftag})"
        except Exception:
            return ""

    if figdir.exists():
        for nm in names:
            figs: List[Path] = []
            for p in sorted(figdir.glob("compare_fit_*.svg")):
                if nm in p.name:
                    figs.append(p)
            if figs:
                items.append(f"<h2>{h(nm)} の比較図</h2>")
                note = galaxy_note(nm)
                if note:
                    items.append(f"<p class=\"lead\">{note}</p>")
                for p in figs[:3]:
                    href = "../paper/figures/" + p.name
                    items.append(
                        "<figure class=\"card\">"
                        f"<img src=\"{h(href)}\" alt=\"{h(p.name)}\" "
                        "style=\"max-width:100%;height:auto\">"
                        f"<figcaption>{h(p.name)}</figcaption>"
                        "</figure>"
                    )
    items.append(
        "<p>関連: <a href=\"../figures\">図ギャラリー</a> / "
        "<a href=\"../memos.html\">メモ一覧</a></p>"
    )
    body = "\n".join(items)
    write_html(out, "共有パラメータ比較レポート", body)


def build_index(reports: Dict[str, str], out: Path) -> None:
    items = ["<h1>レポート</h1>", "<ul>"]
    for label, href in reports.items():
        items.append(f"<li><a href=\"{h(href)}\">{h(label)}</a></li>")
    items.append("</ul>")
    write_html(out, "レポート", "\n".join(items))


def main() -> int:
    pub = Path("server/public/reports")
    reports: Dict[str, str] = {}
    # ディレクトリ内のmulti_fit*.jsonを総なめ
    for src in sorted(Path("data/results").glob("multi_fit*.json")):
        label = src.stem.replace("multi_fit_", "").replace("multi_fit", "")
        label = label or "results"
        out = pub / f"{src.stem}.html"
        try:
            build_multi_report(src, out)
            reports[f"複数銀河({label})"] = f"{out.name}"
        except Exception as e:
            print(f"warn: failed to build {src}: {e}")
    # Sensitivity report (if present)
    sens = Path("data/results/sensitivity/nearby_sensitivity.json")
    if sens.exists():
        try:
            data = load_json(sens)
            # build a simple HTML table grid
            rows = ["<h1>感度分析(nearby)</h1>"]
            rows.append(f"<p>ソース: {h(str(sens))}</p>")
            items = data.get("grid", [])
            # build a header
            rows.append("<table><thead><tr><th>tag</th><th>irr_alpha</th>"
                        "<th>nl_gamma</th><th>chi2_GR</th><th>chi2_ULW</th>"
                        "<th>AIC_GR</th><th>AIC_ULW</th></tr></thead><tbody>")
            for it in items:
                tag = it.get("tag", "")
                p = it.get("params", {})
                chi = it.get("chi2_total", {})
                aic = it.get("AIC", {})
                rows.append(
                    f"<tr><td>{h(str(tag))}</td><td>{h(str(p.get('irr_alpha')))}</td>"
                    f"<td>{h(str(p.get('nl_gamma')))}</td>"
                    f"<td>{h(str(chi.get('GR')))}</td><td>{h(str(chi.get('ULW')))}</td>"
                    f"<td>{h(str(aic.get('GR')))}</td><td>{h(str(aic.get('ULW')))}</td>"
                    "</tr>"
                )
            rows.append("</tbody></table>")
            write_html(pub / "sensitivity_nearby.html",
                       "感度分析(nearby)", "\n".join(rows))
            reports["感度分析(nearby)"] = "sensitivity_nearby.html"
        except Exception as e:
            print("warn: failed sensitivity report:", e)
    build_index(reports, pub / "index.html")
    print(f"wrote {len(reports)} reports under {pub}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
