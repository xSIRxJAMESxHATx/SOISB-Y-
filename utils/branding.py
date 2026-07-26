"""Superb Owl brand art — classy, iconic, silly swagger champion."""
from __future__ import annotations
import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

ASSETS = Path(__file__).resolve().parent.parent / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)


def _font(size: int):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()


def generate_superb_owl(size: int = 512) -> Image.Image:
    """
    Swaggering champion owl:
    - tall tufts, golden monocle, orange Browns crown
    - smug smile, tiny shades vibe, cigar with star-spark
    - mitt + spinning basketball + football + scarlet kicks
    """
    W = H = size
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size / 512.0
    def sc(v): return int(v * s)
    cx, cy = W // 2, H // 2 + sc(10)

    # winner's spotlight
    for i, r in enumerate(range(sc(200), sc(60), -sc(8))):
        d.ellipse([cx-r, cy-r-sc(30), cx+r, cy+r-sc(30)], fill=(255, 210, 80, max(8, 28 - i)))

    # cape (silly swagger)
    d.polygon([
        (cx-sc(20), cy-sc(10)), (cx-sc(130), cy+sc(40)), (cx-sc(120), cy+sc(130)),
        (cx, cy+sc(90)), (cx+sc(120), cy+sc(130)), (cx+sc(130), cy+sc(40)), (cx+sc(20), cy-sc(10)),
    ], fill=(120, 20, 45, 220))

    # body
    d.ellipse([cx-sc(95), cy-sc(25), cx+sc(95), cy+sc(125)], fill=(102, 62, 28, 255), outline=(45, 25, 10, 255), width=max(2, sc(3)))
    d.ellipse([cx-sc(58), cy+sc(15), cx+sc(58), cy+sc(105)], fill=(245, 228, 190, 255))
    # vest buttons
    for by in (sc(40), sc(60), sc(80)):
        d.ellipse([cx-sc(6), cy+by, cx+sc(6), cy+by+sc(12)], fill=(220, 170, 40, 255))

    # head
    d.ellipse([cx-sc(80), cy-sc(110), cx+sc(80), cy+sc(15)], fill=(120, 75, 32, 255), outline=(45, 25, 10, 255), width=max(2, sc(3)))
    # dramatic tufts
    d.polygon([(cx-sc(75), cy-sc(75)), (cx-sc(110), cy-sc(150)), (cx-sc(35), cy-sc(95))], fill=(95, 55, 22, 255))
    d.polygon([(cx+sc(75), cy-sc(75)), (cx+sc(110), cy-sc(150)), (cx+sc(35), cy-sc(95))], fill=(95, 55, 22, 255))

    # Browns crown — jeweled
    crown = [
        (cx-sc(60), cy-sc(100)), (cx-sc(42), cy-sc(148)), (cx-sc(22), cy-sc(108)),
        (cx, cy-sc(160)), (cx+sc(22), cy-sc(108)), (cx+sc(42), cy-sc(148)), (cx+sc(60), cy-sc(100)),
    ]
    d.polygon(crown, fill=(255, 95, 20, 255), outline=(90, 35, 0, 255))
    d.rectangle([cx-sc(60), cy-sc(108), cx+sc(60), cy-sc(92)], fill=(55, 28, 8, 255))
    for jx in (-sc(30), 0, sc(30)):
        d.ellipse([cx+jx-sc(6), cy-sc(150), cx+jx+sc(6), cy-sc(138)], fill=(255, 220, 80, 255))

    # eyes — smug
    d.ellipse([cx-sc(42), cy-sc(65), cx-sc(6), cy-sc(28)], fill=(255, 255, 245, 255), outline=(25, 15, 10, 255), width=2)
    d.ellipse([cx+sc(6), cy-sc(65), cx+sc(42), cy-sc(28)], fill=(255, 255, 245, 255), outline=(25, 15, 10, 255), width=2)
    d.ellipse([cx-sc(28), cy-sc(54), cx-sc(16), cy-sc(42)], fill=(20, 25, 40, 255))
    d.ellipse([cx+sc(18), cy-sc(54), cx+sc(30), cy-sc(42)], fill=(20, 25, 40, 255))
    # monocle
    d.ellipse([cx+sc(2), cy-sc(70), cx+sc(48), cy-sc(24)], outline=(230, 195, 70, 255), width=max(3, sc(4)))
    d.line([cx+sc(48), cy-sc(30), cx+sc(58), cy+sc(8)], fill=(190, 155, 50, 255), width=max(2, sc(2)))
    # eyebrow swagger
    d.arc([cx-sc(44), cy-sc(72), cx-sc(4), cy-sc(50)], 200, 340, fill=(40, 25, 10, 255), width=max(2, sc(3)))

    # beak + smirk
    d.polygon([(cx-sc(10), cy-sc(22)), (cx+sc(10), cy-sc(22)), (cx, cy-sc(4))], fill=(245, 165, 45, 255))
    d.arc([cx-sc(18), cy-sc(12), cx+sc(22), cy+sc(12)], 10, 160, fill=(40, 25, 10, 255), width=max(2, sc(3)))

    # cigar + star puff
    d.rounded_rectangle([cx+sc(38), cy-sc(6), cx+sc(105), cy+sc(10)], radius=sc(4), fill=(125, 72, 30, 255))
    d.rectangle([cx+sc(98), cy-sc(6), cx+sc(108), cy+sc(10)], fill=(200, 45, 40, 255))
    d.ellipse([cx+sc(108), cy-sc(18), cx+sc(130), cy+sc(6)], fill=(220, 220, 230, 120))
    # little star
    d.polygon([
        (cx+sc(120), cy-sc(22)), (cx+sc(123), cy-sc(14)), (cx+sc(131), cy-sc(14)),
        (cx+sc(125), cy-sc(9)), (cx+sc(127), cy-sc(1)), (cx+sc(120), cy-sc(6)),
        (cx+sc(113), cy-sc(1)), (cx+sc(115), cy-sc(9)), (cx+sc(109), cy-sc(14)), (cx+sc(117), cy-sc(14)),
    ], fill=(255, 230, 80, 200))

    # Cavs basketball
    d.ellipse([cx+sc(55), cy+sc(45), cx+sc(115), cy+sc(105)], fill=(110, 15, 45, 255), outline=(50, 10, 20, 255), width=2)
    d.arc([cx+sc(60), cy+sc(50), cx+sc(110), cy+sc(100)], 0, 180, fill=(255, 255, 255, 220), width=2)
    d.line([cx+sc(85), cy+sc(48), cx+sc(85), cy+sc(102)], fill=(255, 255, 255, 180), width=2)

    # Guardians mitt
    d.ellipse([cx-sc(125), cy+sc(40), cx-sc(55), cy+sc(110)], fill=(190, 100, 45, 255), outline=(90, 45, 15, 255), width=2)
    d.arc([cx-sc(115), cy+sc(55), cx-sc(70), cy+sc(95)], 200, 350, fill=(100, 50, 20, 255), width=max(2, sc(3)))

    # football
    d.ellipse([cx-sc(35), cy+sc(100), cx+sc(35), cy+sc(135)], fill=(95, 55, 22, 255), outline=(40, 20, 10, 255), width=2)
    d.line([cx-sc(12), cy+sc(117), cx+sc(12), cy+sc(117)], fill=(245, 240, 220, 255), width=2)

    # scarlet kicks
    d.ellipse([cx-sc(55), cy+sc(125), cx-sc(15), cy+sc(148)], fill=(190, 0, 0, 255))
    d.ellipse([cx+sc(15), cy+sc(125), cx+sc(55), cy+sc(148)], fill=(190, 0, 0, 255))
    d.rectangle([cx-sc(50), cy+sc(138), cx-sc(20), cy+sc(145)], fill=(240, 240, 240, 255))
    d.rectangle([cx+sc(20), cy+sc(138), cx+sc(50), cy+sc(145)], fill=(240, 240, 240, 255))

    # name plate
    d.rounded_rectangle([sc(40), H-sc(48), W-sc(40), H-sc(12)], radius=sc(10), fill=(25, 15, 8, 230))
    d.text((cx, H-sc(30)), "SO!SB!Y!  ·  SUPERB OWL", fill=(255, 215, 100, 255), font=_font(max(14, sc(18))), anchor="mm")

    return img


def save_brand_assets() -> dict:
    owl = generate_superb_owl(512)
    icon_path = ASSETS / "superb_owl_icon.png"
    owl.save(icon_path, "PNG")

    wm = generate_superb_owl(800)
    arr = wm.split()
    if len(arr) == 4:
        a = arr[3].point(lambda p: int(p * 0.11))
        wm = Image.merge("RGBA", (arr[0], arr[1], arr[2], a))
    wm_path = ASSETS / "superb_owl_watermark.png"
    wm.save(wm_path, "PNG")

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
