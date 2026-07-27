"""Premium fixed hamburger drawer (HTML/CSS/JS). Full React components need npm publish."""
from __future__ import annotations
import streamlit.components.v1 as components


def render_drawer(open_default: bool = False) -> None:
    open_x = "0" if open_default else "-105%"
    components.html(
        f"""
<!DOCTYPE html>
<html><head>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@500;700;800&display=swap" rel="stylesheet">
<style>
  #sosby-ham {{
    position: fixed; top: 12px; left: 12px; z-index: 2147483646;
    width: 48px; height: 48px; border: none; border-radius: 14px;
    background: linear-gradient(135deg, #FF5A00, #E7B100);
    color: #fff; font-size: 22px; cursor: pointer;
    box-shadow: 0 8px 24px rgba(255,90,0,0.35);
    font-family: Outfit, system-ui, sans-serif;
  }}
  #sosby-drawer {{
    position: fixed; top: 0; left: 0; height: 100vh; width: min(300px, 88vw);
    z-index: 2147483645;
    background: linear-gradient(180deg, #FFF8EF, #F5E6C8);
    color: #4A2A12;
    box-shadow: 8px 0 32px rgba(0,0,0,0.18);
    transform: translateX({open_x});
    transition: transform 0.22s ease;
    padding: 72px 18px 24px;
    font-family: Outfit, system-ui, sans-serif;
    overflow: auto;
  }}
  #sosby-drawer h2 {{ margin: 0 0 4px; font-size: 1.2rem; font-weight: 800; }}
  #sosby-drawer p {{ font-size: 0.78rem; opacity: 0.75; margin: 0 0 16px; }}
  .nav-item {{
    padding: 10px 12px; margin: 4px 0; border-radius: 12px;
    font-weight: 600; font-size: 0.92rem;
    background: rgba(255,255,255,0.55);
    border: 1px solid rgba(74,42,18,0.06);
  }}
  .hint {{ font-size: 0.7rem; opacity: 0.65; margin-top: 18px; line-height: 1.4; }}
</style></head>
<body>
<button id="sosby-ham" aria-label="Open menu">☰</button>
<aside id="sosby-drawer">
  <h2>🦉 SO!SB!Y!</h2>
  <p>Superb Owl navigation guide</p>
  <div class="nav-item">🏠 Home</div>
  <div class="nav-item">🏈 Game Day</div>
  <div class="nav-item">📊 Analytics</div>
  <div class="nav-item">🧪 Betting Lab</div>
  <div class="nav-item">🦉 Fan Zone</div>
  <div class="nav-item">🔔 Alerts</div>
  <p class="hint">
    Use the <strong>Navigate</strong> row and Streamlit sidebar for live page links.
    A published React Streamlit component is required to route clicks into Python from this drawer.
  </p>
</aside>
<script>
(function(){{
  var open = {str(open_default).lower()};
  var btn = document.getElementById('sosby-ham');
  var dr = document.getElementById('sosby-drawer');
  function apply(){{ dr.style.transform = open ? 'translateX(0)' : 'translateX(-105%)'; }}
  apply();
  btn.onclick = function(){{ open = !open; apply(); }};
}})();
</script>
</body></html>
""",
        height=56,
        scrolling=False,
    )
