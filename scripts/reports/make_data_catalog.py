#!/usr/bin/env python3
from __future__ import annotations
import os, json, hashlib
from pathlib import Path
from datetime import datetime


def md5sum(p: Path) -> str:
    h = hashlib.md5()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def row(path: Path) -> dict:
    if not path.exists():
        return {"path": str(path), "exists": False}
    st = path.stat()
    return {
        "path": str(path),
        "exists": True,
        "size": st.st_size,
        "mtime": int(st.st_mtime),
        "md5": md5sum(path) if path.is_file() and st.st_size < 100*1024*1024 else None,
    }


def human_size(n: int | None) -> str:
    if not n:
        return ""
    for unit in ['B','KB','MB','GB','TB']:
        if n < 1024:
            return f"{n:.0f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def fmt_time(ts: int | None) -> str:
    if not ts:
        return ""
    return datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M UTC')


def main() -> int:
    outdir = Path('server/public/reports'); outdir.mkdir(parents=True, exist_ok=True)
    catalog: dict[str, list[dict]] = {}
    # Galaxies
    for name in ['NGC3198', 'NGC2403']:
        entries = []
        entries.append(row(Path(f'data/halpha/{name}/Halpha_SB.fits')))
        entries.append(row(Path(f'data/halpha/{name}/EM_pc_cm6.fits')))
        # SINGS raw/derived
        if name == 'NGC3198':
            entries.append(row(Path('data/sings/ngc3198_HA_SUB_dr4.fits')))
            entries.append(row(Path('data/sings/ngc3198_irac1.fits')))
        if name == 'NGC2403':
            entries.append(row(Path('data/sings/ngc2403_HA.fits')))
            entries.append(row(Path('data/sings/ngc2403_R.fits')))
            entries.append(row(Path('data/sings/ngc2403_HA_SUB.fits')))
            entries.append(row(Path('data/sings/ngc2403_irac1.fits')))
        # HALOGAS HI
        entries.append(row(Path(f'data/halogas/{name}-HR_mom1m.fits')))
        entries.append(row(Path(f'data/halogas/{name}-HR_mom0m.fits')))
        catalog[name] = entries
    # Clusters
    for c in ['Bullet', 'Abell1689', 'CL0024']:
        entries = []
        root = Path(f'data/cluster/{c}')
        entries.append(row(root / 'sigma_e.fits'))
        entries.append(row(root / 'omega_cut.fits'))
        entries.append(row(root / 'kappa_obs.fits'))
        # sample a few CXO primaries
        cxo = root / 'cxo'
        if cxo.exists():
            for p in sorted(cxo.glob('*_full_img2.fits.gz'))[:6]:
                entries.append(row(p))
        # wayback caches
        if (root / 'kappa_wayback').exists():
            for p in sorted((root/'kappa_wayback').glob('*')):
                entries.append(row(p))
        if (root / 'wayback_hunt').exists():
            for p in sorted((root/'wayback_hunt').glob('*')):
                entries.append(row(p))
        catalog[c] = entries

    # HTML render
    def render_section(title: str, items: list[dict]) -> str:
        rows = []
        rows.append('<table><thead><tr><th>Path</th><th>Status</th><th>Size</th><th>Modified (UTC)</th><th>MD5</th></tr></thead><tbody>')
        for it in items:
            exists = it.get('exists', False)
            status = '✅' if exists else '❌'
            size = human_size(it.get('size')) if exists else ''
            mtime = fmt_time(it.get('mtime')) if exists else ''
            md5 = it.get('md5') or ''
            rows.append(f"<tr><td><code>{it['path']}</code></td><td>{status}</td><td>{size}</td><td>{mtime}</td><td><small>{md5}</small></td></tr>")
        rows.append('</tbody></table>')
        return f"<h2>{title}</h2>\n<div class=card>\n" + '\n'.join(rows) + '\n</div>'

    parts = [
        '<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>データ目録（取得状況）</title><link rel="stylesheet" href="../styles.css"></head><body>',
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
        '<main class="wrap"><h1>データ目録（取得状況・再現メタ）</h1>',
        '<div class=card><p>本ページはリポジトリ内の <code>data/</code> 以下を走査し、主要ファイルの存在・サイズ・更新時刻・MD5（100MB未満）を一覧します。</p>'
        '<p><small>取得コマンド: <code>make fetch-inputs</code>（NGC 3198/2403）、<code>make fetch-bullet</code>（Bullet）、<code>make fetch-abell OBSIDS=...</code>、<code>make fetch-cl0024 OBSIDS=...</code></small></p></div>',
    ]
    for key in ['NGC3198','NGC2403']:
        parts.append(render_section(f'銀河: {key}', catalog.get(key, [])))
    for key in ['Bullet','Abell1689','CL0024']:
        parts.append(render_section(f'クラスタ: {key}', catalog.get(key, [])))
    # JSON dump link for auditing
    meta_path = outdir / 'data_catalog.json'
    meta_path.write_text(json.dumps(catalog, indent=2), encoding='utf-8')
    parts.append(f"<div class=card><p><small>JSON: reports/{meta_path.name}</small></p></div>")
    parts.append('</main></body></html>')
    (outdir/'data_catalog.html').write_text('\n'.join(parts), encoding='utf-8')
    print('wrote', outdir/'data_catalog.html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
