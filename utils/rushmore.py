"""
Mount Rushmore composite — richer backdrop, multi-source portraits, always succeeds.
"""
from __future__ import annotations
import io
from typing import List, Optional
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "SBSBY-SportsHub/2.2"})


def _fetch_image(url: str, timeout: float = 6.0) -> Optional[Image.Image]:
    try:
        r = SESSION.get(url, timeout=timeout)
        if r.status_code != 200:
            return None
        return Image.open(io.BytesIO(r.content)).convert("RGBA")
    except Exception:
        return None


def _placeholder_head(name: str, size: int = 220) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    palette = [(49,29,0,255),(255,60,0,255),(134,0,56,255),(12,35,64,255),(187,0,0,255),(0,38,104,255)]
    h = sum(ord(c) for c in name) % len(palette)
    d.ellipse([2, 2, size-3, size-3], fill=palette[h])
    initials = "".join(p[0] for p in name.split()[:2]).upper() or "?"
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size // 3)
    except Exception:
        font = ImageFont.load_default()
    bbox = d.textbbox((0, 0), initials, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    d.text(((size-tw)/2, (size-th)/2-4), initials, fill=(255,255,255,255), font=font)
    return img


def fetch_player_headshot(player_name: str) -> Image.Image:
    q = player_name.replace(" ", "%20")
    # 1 TheSportsDB
    try:
        r = SESSION.get(f"https://www.thesportsdb.com/api/v1/json/3/searchplayers.php?p={q}", timeout=6)
        if r.status_code == 200:
            for p in (r.json().get("player") or [])[:4]:
                for key in ("strCutout", "strThumb", "strRender"):
                    url = p.get(key)
                    if url and str(url).startswith("http"):
                        img = _fetch_image(url)
                        if img:
                            return img
    except Exception:
        pass
    # 2 Wikipedia thumbnail
    try:
        title = player_name.replace(" ", "_")
        r = SESSION.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}", timeout=5)
        if r.status_code == 200:
            thumb = (r.json().get("thumbnail") or {}).get("source")
            if thumb:
                img = _fetch_image(thumb)
                if img:
                    return img
    except Exception:
        pass
    # 3 UI Avatars
    img = _fetch_image(f"https://ui-avatars.com/api/?name={q}&size=256&background=1a1208&color=ffd700&bold=true")
    if img:
        return img
    return _placeholder_head(player_name)


def _circular_mask(im: Image.Image, size: int) -> Image.Image:
    im = im.resize((size, size), Image.Resampling.LANCZOS)
    # slight contrast
    try:
        im = ImageEnhance.Contrast(im).enhance(1.08)
    except Exception:
        pass
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size-1, size-1], fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(im, (0, 0))
    out.putalpha(mask)
    return out


def generate_rushmore(players: List[str], title: str = "Mount Rushmore") -> Image.Image:
    W, H = 1100, 700
    base = Image.new("RGBA", (W, H), (20, 30, 50, 255))
    d = ImageDraw.Draw(base)
    # dawn sky
    for y in range(H):
        r = int(25 + (180 - 25) * (y / H) * 0.35)
        g = int(40 + (140 - 40) * (y / H) * 0.5)
        b = int(70 + (200 - 70) * (1 - y / H) * 0.6)
        d.line([(0, y), (W, y)], fill=(r, g, b, 255))
    # sun glow
    for i in range(8, 0, -1):
        alpha = 30
        d.ellipse([W//2 - i*40, 40 - i*10, W//2 + i*40, 120 + i*10], fill=(255, 200, 100, alpha))
    # mountains layered
    d.polygon([(0,H),(0,int(H*0.58)),(180,int(H*0.40)),(320,int(H*0.52)),(480,int(H*0.28)),
               (620,int(H*0.45)),(780,int(H*0.26)),(920,int(H*0.42)),(1100,int(H*0.50)),(1100,H)],
              fill=(75, 78, 85, 255))
    d.polygon([(0,H),(0,int(H*0.72)),(220,int(H*0.60)),(450,int(H*0.68)),(700,int(H*0.55)),
               (900,int(H*0.66)),(1100,int(H*0.58)),(1100,H)], fill=(50, 52, 58, 255))
    # mist
    mist = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    md = ImageDraw.Draw(mist)
    md.rectangle([0, int(H*0.7), W, H], fill=(200, 210, 220, 40))
    base = Image.alpha_composite(base, mist)
    d = ImageDraw.Draw(base)

    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        font_name = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except Exception:
        font_title = font_name = font_small = ImageFont.load_default()

    d.text((W//2, 30), title, fill=(255,255,255,255), font=font_title, anchor="mt")
    d.text((W//2, 72), "SBSBY! · Fan Mount Rushmore", fill=(255, 230, 180, 230), font=font_small, anchor="mt")

    slots = [(150, 175, 210), (360, 140, 220), (590, 150, 210), (810, 180, 205)]
    names = (list(players) + ["?", "?", "?", "?"])[:4]

    for i, (x, y, sz) in enumerate(slots):
        name = names[i]
        try:
            head = fetch_player_headshot(name)
        except Exception:
            head = _placeholder_head(name)
        circ = _circular_mask(head, sz)
        # gold ring
        ring = Image.new("RGBA", (sz+16, sz+16), (0,0,0,0))
        rd = ImageDraw.Draw(ring)
        rd.ellipse([0,0,sz+15,sz+15], outline=(255, 215, 100, 255), width=6)
        rd.ellipse([3,3,sz+12,sz+12], outline=(120, 90, 40, 180), width=2)
        base.paste(ring, (x-8, y-8), ring)
        base.paste(circ, (x, y), circ)
        label = name if len(name) < 24 else name[:22] + "…"
        d.rounded_rectangle([x-12, y+sz+10, x+sz+12, y+sz+40], radius=10, fill=(15, 15, 20, 230))
        d.text((x+sz//2, y+sz+25), label, fill=(255,255,255,255), font=font_name, anchor="mm")

    d.text((W//2, H-20), "Fan art composite · Multi-source portraits · Not affiliated with any league",
           fill=(255,255,255,160), font=font_small, anchor="mm")
    return base.convert("RGB")


def rushmore_to_bytes(players: List[str], title: str = "Mount Rushmore") -> bytes:
    try:
        img = generate_rushmore(players, title)
    except Exception:
        # absolute last resort blank with text
        img = Image.new("RGB", (800, 500), (30, 40, 60))
        d = ImageDraw.Draw(img)
        d.text((400, 250), "Rushmore unavailable", fill=(255,255,255), anchor="mm")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
