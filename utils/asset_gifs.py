"""
Load optional GIFs / images from assets/.

Drop files into assets/gifs/ e.g.:
  loading.gif, victory.gif, weather.gif, betting.gif
Then: show_gif("loading") or show_gif("loading.gif")
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional

import streamlit as st

ASSETS = Path(__file__).resolve().parent.parent / "assets"
GIFS = ASSETS / "gifs"


def resolve_gif(name: str) -> Optional[Path]:
    GIFS.mkdir(parents=True, exist_ok=True)
    candidates = [
        GIFS / name,
        GIFS / f"{name}.gif",
        ASSETS / name,
        ASSETS / f"{name}.gif",
    ]
    for p in candidates:
        if p.exists() and p.is_file():
            return p
    return None


def show_gif(name: str, caption: str = "", width: Optional[int] = None) -> bool:
    path = resolve_gif(name)
    if not path:
        return False
    try:
        if width:
            st.image(str(path), caption=caption or None, width=width)
        else:
            st.image(str(path), caption=caption or None, use_container_width=True)
        return True
    except Exception:
        return False


def list_gifs() -> list:
    GIFS.mkdir(parents=True, exist_ok=True)
    return sorted([p.name for p in GIFS.glob("*.gif")])
