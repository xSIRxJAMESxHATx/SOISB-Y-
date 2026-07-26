"""Superb Owl brand art + watermark (Pillow, always succeeds)."""
from __future__ import annotations
import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

ASSETS = Path(__file__).resolve().parent.parent / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)


def _font(size: int):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()


def generate_superb_owl(size: int = 512) -> Image.Image:
    """Classy 1950s-style owl: monocle, Browns crown, glove, ball, cigar, shades energy."""
    W = H = size
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = W // 2, H // 2 + int(size * 0.05)

    # soft glow
    for r in range(int(size * 0.42), int(size * 0.2), -4):
        alpha = 18
        d.ellipse([cx-r, cy-r-20, cx+r, cy+r-20], fill=(255, 200, 80, alpha))

    # body
    d.ellipse([cx-90, cy-30, cx+90, cy+120], fill=(90, 55, 25, 255), outline=(40, 25, 10, 255), width=3)
    # belly
    d.ellipse([cx-55, cy+10, cx+55, cy+100], fill=(230, 210, 170, 255))
    # head
    d.ellipse([cx-75, cy-100, cx+75, cy+10], fill=(110, 70, 30, 255), outline=(40, 25, 10, 255), width=3)
    # ear tufts
    d.polygon([(cx-70, cy-70), (cx-95, cy-130), (cx-40, cy-90)], fill=(90, 55, 25, 255))
    d.polygon([(cx+70, cy-70), (cx+95, cy-130), (cx+40, cy-90)], fill=(90, 55, 25, 255))

    # Browns-style crown (orange-brown points)
    crown = [(cx-55, cy-95), (cx-40, cy-135), (cx-20, cy-100), (cx, cy-145),
             (cx+20, cy-100), (cx+40, cy-135), (cx+55, cy-95)]
    d.polygon(crown, fill=(255, 90, 20, 255), outline=(80, 30, 0, 255))
    d.rectangle([cx-55, cy-100, cx+55, cy-88], fill=(60, 30, 10, 255))

    # eyes + monocle
    d.ellipse([cx-40, cy-60, cx-8, cy-28], fill=(255, 255, 240, 255), outline=(20, 15, 10, 255), width=2)
    d.ellipse([cx+8, cy-60, cx+40, cy-28], fill=(255, 255, 240, 255), outline=(20, 15, 10, 255), width=2)
    d.ellipse([cx-28, cy-52, cx-18, cy-42], fill=(20, 20, 30, 255))
    d.ellipse([cx+18, cy-52, cx+28, cy-42], fill=(20, 20, 30, 255))
    # monocle on right eye
    d.ellipse([cx+5, cy-65, cx+45, cy-25], outline=(220, 190, 80, 255), width=4)
    d.line([cx+45, cy-30, cx+55, cy+5], fill=(180, 150, 60, 255), width=2)

    # sunglasses tint (classy shade over left)
    d.arc([cx-42, cy-58, cx-6, cy-30], 200, 340, fill=(30, 30, 40, 180), width=3)

    # beak
    d.polygon([(cx-8, cy-20), (cx+8, cy-20), (cx, cy-5)], fill=(240, 160, 40, 255))

    # cigar
    d.rectangle([cx+35, cy-5, cx+95, cy+8], fill=(120, 70, 30, 255))
    d.rectangle([cx+90, cy-5, cx+98, cy+8], fill=(200, 40, 40, 255))
    d.ellipse([cx+96, cy-10, cx+110, cy+5], fill=(180, 180, 190, 150))

    # basketball (Cavs wine-ish) under wing
    d.ellipse([cx+50, cy+40, cx+100, cy+90], fill=(120, 20, 50, 255), outline=(40, 10, 20, 255), width=2)
    d.arc([cx+55, cy+45, cx+95, cy+85], 0, 180, fill=(255, 255, 255, 200), width=2)

    # baseball mitt
    d.ellipse([cx-110, cy+35, cx-50, cy+95], fill=(180, 90, 40, 255), outline=(80, 40, 15, 255), width=2)
    d.arc([cx-100, cy+45, cx-60, cy+85], 200, 340, fill=(100, 50, 20, 255), width=3)

    # football suggestion (oval)
    d.ellipse([cx-30, cy+95, cx+30, cy+125], fill=(90, 50, 20, 255), outline=(40, 20, 10, 255), width=2)

    # sneakers hint
    d.ellipse([cx-50, cy+115, cx-15, cy+135], fill=(200, 0, 0, 255))
    d.ellipse([cx+15, cy+115, cx+50, cy+135], fill=(200, 0, 0, 255))

    d.text((cx, H - 28), "SO!SB!Y!", fill=(255, 220, 120, 255), font=_font(max(18, size // 16)), anchor="mt")
    return img


def save_brand_assets() -> dict:
    """Write icon + watermark files; return paths."""
    owl = generate_superb_owl(512)
    icon_path = ASSETS / "superb_owl_icon.png"
    owl.save(icon_path, "PNG")

    # watermark: large faded
    wm = generate_superb_owl(800)
    wm = ImageEnhance.Brightness(wm).enhance(1.1)
    # reduce alpha
    arr = wm.split()
    if len(arr) == 4:
        a = arr[3].point(lambda p: int(p * 0.12))
        wm = Image.merge("RGBA", (arr[0], arr[1], arr[2], a))
    wm_path = ASSETS / "superb_owl_watermark.png"
    wm.save(wm_path, "PNG")

    # favicon small
    fav = owl.resize((64, 64), Image.Resampling.LANCZOS)
    fav_path = ASSETS / "favicon.png"
    fav.save(fav_path, "PNG")
    return {"icon": str(icon_path), "watermark": str(wm_path), "favicon": str(fav_path)}


def watermark_data_uri() -> str:
    import base64
    path = ASSETS / "superb_owl_watermark.png"
    if not path.exists():
        save_brand_assets()
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"
