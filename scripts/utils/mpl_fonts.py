from __future__ import annotations

"""Matplotlib font/figure defaults tuned for OTA図版の可読性向上."""

from pathlib import Path


def use_jp_font() -> None:
    """Configure Matplotlib to render mixed-language text cleanly.

    - Prefer Japanese-capable sans-serif fonts (Noto系を最優先)
    - Align mathtext with STIX glyphs to avoid font mismatches
    - Harden vector出力と savefig の既定値 (DPI・bbox)
    - Unify legend appearance to mitigate細文字の潰れ
    """
    try:
        import matplotlib as mpl
        from matplotlib import font_manager

        asset_dir = Path(__file__).resolve().parents[2] / "assets" / "fonts"
        extra_fonts = [
            asset_dir / "NotoSansSymbols2-Regular.ttf",
            asset_dir / "NotoSansMath-Regular.ttf",
        ]

        for font_path in extra_fonts:
            if font_path.exists():
                font_manager.fontManager.addfont(str(font_path))

        families = [
            "Noto Sans CJK JP",
            "IPAexGothic",
            "IPAPGothic",
            "Yu Gothic",
            "Hiragino Sans",
            "TakaoGothic",
            "MS Gothic",
            "Meiryo",
            "DejaVu Sans",
            "Noto Sans Symbols2",
        ]

        rc_updates = {
            "font.family": "sans-serif",
            "font.sans-serif": families,
            "axes.unicode_minus": False,
            "mathtext.fontset": "stix",
            "text.antialiased": True,
            "svg.fonttype": "path",
            "pdf.fonttype": 42,
            "pdf.use14corefonts": False,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "savefig.facecolor": "white",
            "legend.frameon": True,
            "legend.framealpha": 1.0,
            "legend.facecolor": "white",
            "legend.edgecolor": "0.3",
        }

        for key, value in rc_updates.items():
            mpl.rcParams[key] = value
    except Exception:
        # フォントやバックエンドが利用できない環境では静かにフォールバック
        pass
