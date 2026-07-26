"""Superb Owl branding — logo from official asset art."""
from __future__ import annotations
import base64
import io
from pathlib import Path
from typing import Optional

from PIL import Image

ASSETS = Path(__file__).resolve().parent.parent / "assets"

# Palette pulled from the Superb Owl poster
OWL_ORANGE = "#E85A1C"
OWL_BROWN = "#5C3310"
OWL_GOLD = "#F0C14B"
OWL_CREAM = "#F5E6C8"
OWL_BRICK = "#C44B1A"


def logo_path() -> Path:
    for name in ("superb_owl_logo.png", "superb_owl_icon.png", "favicon.png"):
        p = ASSETS / name
        if p.exists():
            return p
    return ASSETS / "superb_owl_icon.png"


def icon_path() -> Path:
    p = ASSETS / "superb_owl_icon.png"
    return p if p.exists() else logo_path()


def watermark_path() -> Path:
    p = ASSETS / "superb_owl_watermark.png"
    return p if p.exists() else icon_path()


def _data_uri(path: Path, max_side: int = 0) -> str:
    if not path.exists():
        return ""
    im = Image.open(path).convert("RGBA")
    if max_side and max(im.size) > max_side:
        im.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def logo_data_uri(max_side: int = 512) -> str:
    return _data_uri(logo_path(), max_side)


def icon_data_uri(max_side: int = 128) -> str:
    return _data_uri(icon_path(), max_side)


def watermark_data_uri(max_side: int = 420) -> str:
    return _data_uri(watermark_path(), max_side)


def ensure_assets() -> dict:
    """Return paths that exist for diagnostics."""
    return {
        "logo": str(logo_path()) if logo_path().exists() else "",
        "icon": str(icon_path()) if icon_path().exists() else "",
        "watermark": str(watermark_path()) if watermark_path().exists() else "",
        "favicon": str(ASSETS / "favicon.png") if (ASSETS / "favicon.png").exists() else "",
    }
