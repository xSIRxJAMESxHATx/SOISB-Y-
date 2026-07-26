"""Game-day weather with multi-source failover + cartoon icons + map links."""
from __future__ import annotations
import io
from typing import Any, Dict, List, Optional, Tuple
import requests
from PIL import Image, ImageDraw, ImageFont

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "SBSBY-Weather/1.0"})

# Stadium / home coordinates (lat, lon, label)
VENUES: Dict[str, Tuple[float, float, str]] = {
    "browns": (41.5061, -81.6995, "Huntington Bank Field, Cleveland"),
    "guardians": (41.4962, -81.6852, "Progressive Field, Cleveland"),
    "cavaliers": (41.4965, -81.6882, "Rocket Mortgage FieldHouse, Cleveland"),
    "osu_football": (40.0017, -83.0197, "Ohio Stadium, Columbus"),
    "osu_mbb": (40.0055, -83.0245, "Value City Arena, Columbus"),
    "crew": (39.9685, -83.0165, "Lower.com Field, Columbus"),
    "bluejackets": (39.9692, -83.0061, "Nationwide Arena, Columbus"),
    "usmnt": (40.0, -83.0, "USA match venue (varies)"),
    "usab": (40.0, -83.0, "USA Basketball venue (varies)"),
    "kent_mbb": (41.1490, -81.3412, "MAC Center, Kent"),
    "rhs_football": (39.9547, -82.8121, "Reynoldsburg, OH"),
    "rhs_mbb": (39.9547, -82.8121, "Reynoldsburg, OH"),
    "tiffin_tf": (41.1145, -83.1780, "Tiffin University, Tiffin OH"),
}


def _get_json(url: str, timeout: float = 6.0) -> Optional[dict]:
    try:
        r = SESSION.get(url, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def fetch_weather(team_key: str) -> Tuple[dict, str]:
    lat, lon, label = VENUES.get(team_key, (41.5, -81.7, "Cleveland, OH"))
    sources_tried = []

    # 1 Open-Meteo (no key)
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,precipitation"
            f"&temperature_unit=fahrenheit&wind_speed_unit=mph"
        )
        data = _get_json(url)
        if data and "current" in data:
            cur = data["current"]
            code = int(cur.get("weather_code") or 0)
            return {
                "temp_f": cur.get("temperature_2m"),
                "humidity": cur.get("relative_humidity_2m"),
                "wind_mph": cur.get("wind_speed_10m"),
                "precip": cur.get("precipitation"),
                "code": code,
                "summary": _code_to_summary(code),
                "label": label,
                "lat": lat,
                "lon": lon,
            }, "open-meteo"
    except Exception as e:
        sources_tried.append(f"open-meteo:{e}")

    # 2 wttr.in JSON
    try:
        data = _get_json(f"https://wttr.in/{lat},{lon}?format=j1")
        if data:
            cur = (data.get("current_condition") or [{}])[0]
            desc = ((cur.get("weatherDesc") or [{}])[0]).get("value") or "Weather"
            return {
                "temp_f": float(cur.get("temp_F") or 0),
                "humidity": float(cur.get("humidity") or 0),
                "wind_mph": float(cur.get("windspeedMiles") or 0),
                "precip": float(cur.get("precipMM") or 0),
                "code": 0,
                "summary": desc,
                "label": label,
                "lat": lat,
                "lon": lon,
            }, "wttr.in"
    except Exception as e:
        sources_tried.append(f"wttr:{e}")

    # 3 metaweather-style skip — use National Weather Service points
    try:
        pts = _get_json(f"https://api.weather.gov/points/{lat},{lon}")
        if pts:
            forecast_url = (pts.get("properties") or {}).get("forecast")
            if forecast_url:
                fc = _get_json(forecast_url)
                periods = ((fc or {}).get("properties") or {}).get("periods") or []
                if periods:
                    p0 = periods[0]
                    return {
                        "temp_f": p0.get("temperature"),
                        "humidity": None,
                        "wind_mph": None,
                        "precip": None,
                        "code": 0,
                        "summary": p0.get("shortForecast") or p0.get("name"),
                        "label": label,
                        "lat": lat,
                        "lon": lon,
                    }, "weather.gov"
    except Exception as e:
        sources_tried.append(f"nws:{e}")

    # 4 Open-Meteo again with minimal
    # 5 Static fallback
    return {
        "temp_f": "—",
        "humidity": "—",
        "wind_mph": "—",
        "precip": "—",
        "code": -1,
        "summary": "Weather temporarily unavailable",
        "label": label,
        "lat": lat,
        "lon": lon,
    }, "fallback"


def _code_to_summary(code: int) -> str:
    if code == 0: return "Clear / sunny"
    if code in (1, 2, 3): return "Partly cloudy"
    if code in (45, 48): return "Fog"
    if code in (51, 53, 55, 61, 63, 65): return "Rain"
    if code in (71, 73, 75, 77, 85, 86): return "Snow"
    if code in (95, 96, 99): return "Thunderstorm"
    if code in (66, 67): return "Freezing rain"
    return "Mixed conditions"


def map_links(lat: float, lon: float) -> List[dict]:
    return [
        {"name": "OpenStreetMap", "url": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=16/{lat}/{lon}"},
        {"name": "Google Maps satellite", "url": f"https://www.google.com/maps/@{lat},{lon},17z/data=!3m1!1e3"},
        {"name": "Google Maps place", "url": f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"},
        {"name": "Bing Maps", "url": f"https://www.bing.com/maps?cp={lat}~{lon}&lvl=17&style=a"},
        {"name": "Apple Maps (web)", "url": f"https://maps.apple.com/?ll={lat},{lon}&z=16"},
    ]


def weather_cartoon(summary: str, temp_f: Any, lat: float = 41.5) -> bytes:
    """Relational weather cartoon (sun, old man winter, etc.)."""
    W, H = 320, 220
    s = (summary or "").lower()
    img = Image.new("RGB", (W, H), (135, 200, 245))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except Exception:
        font = small = ImageFont.load_default()

    # scene pick
    if "snow" in s or "freezing" in s:
        img = Image.new("RGB", (W, H), (200, 220, 235))
        d = ImageDraw.Draw(img)
        d.ellipse([120, 40, 200, 110], fill=(240, 240, 250), outline=(100, 100, 120))
        d.ellipse([140, 90, 230, 160], fill=(240, 240, 250), outline=(100, 100, 120))
        for i in range(25):
            x, y = (i * 37) % W, (i * 53) % H
            d.ellipse([x, y, x+4, y+4], fill=(255, 255, 255))
        d.text((W//2, 200), "Old Man Winter says bundle up!", fill=(40, 50, 80), font=small, anchor="mt")
    elif "thunder" in s or "storm" in s or "rain" in s:
        img = Image.new("RGB", (W, H), (70, 80, 100))
        d = ImageDraw.Draw(img)
        d.ellipse([80, 30, 240, 100], fill=(90, 90, 100))
        d.polygon([(160, 90), (140, 140), (155, 140), (145, 180), (190, 120), (170, 120), (185, 90)], fill=(255, 220, 50))
        d.text((W//2, 200), "Storm mode — grab a jacket!", fill=(230, 230, 240), font=small, anchor="mt")
    elif "clear" in s or "sunny" in s:
        img = Image.new("RGB", (W, H), (120, 190, 255))
        d = ImageDraw.Draw(img)
        d.ellipse([110, 40, 210, 140], fill=(255, 220, 40), outline=(255, 180, 0), width=3)
        d.ellipse([135, 75, 150, 90], fill=(40, 40, 40))
        d.ellipse([170, 75, 185, 90], fill=(40, 40, 40))
        d.arc([140, 95, 180, 120], 0, 180, fill=(40, 40, 40), width=3)
        # sunglasses
        d.rectangle([130, 72, 190, 88], outline=(20, 20, 20), width=2)
        d.text((W//2, 200), "Sunshine with attitude!", fill=(20, 40, 80), font=small, anchor="mt")
    elif lat < 35 and ("clear" in s or "hot" in s or (isinstance(temp_f, (int, float)) and temp_f > 95)):
        img = Image.new("RGB", (W, H), (230, 200, 120))
        d = ImageDraw.Draw(img)
        d.ellipse([140, 120, 180, 200], fill=(40, 140, 60))
        d.rectangle([155, 160, 165, 210], fill=(90, 60, 30))
        d.text((W//2, 30), "Desert dry!", fill=(80, 50, 20), font=font, anchor="mt")
    else:
        d.ellipse([100, 50, 220, 140], fill=(200, 200, 210))
        d.text((W//2, 180), summary[:40] if summary else "Looking outside…", fill=(30, 40, 60), font=small, anchor="mt")

    # temp badge
    try:
        tlabel = f"{int(float(temp_f))}°F" if temp_f not in (None, "—") else "—°F"
    except Exception:
        tlabel = "—°F"
    d.rounded_rectangle([10, 10, 90, 40], radius=8, fill=(20, 20, 30))
    d.text((50, 25), tlabel, fill=(255, 220, 100), font=font, anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
