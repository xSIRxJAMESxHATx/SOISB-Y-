# Deploy SO!SB!Y! (multipage)

## Structure
- `app.py` — Home + Jump links
- `pages/1_Game_Day.py` — Scores, schedule, news, watch, weather
- `pages/2_Analytics.py` — Standings, trends, leaders, greats, players
- `pages/3_Betting_Lab.py` — Educational sandbox (multi-team)
- `pages/4_Fan_Zone.py` — Community, Rushmore, moments, tickets, bot
- `pages/5_Alerts.py` — SMS + diagnostics

## Streamlit Cloud
1. Push repo to GitHub
2. Main file: `app.py`
3. Secrets (optional): ODDS_API_KEY, Twilio, Supabase, MOD_PASSWORD, REDIS_URL
4. After deploy, open **sidebar ☰** on mobile for navigation

## Offline / cache
- Toggle **Prefer cached / offline** in sidebar
- `st.cache_data` TTLs on scoreboard/schedule/standings/news
- Disk cache under `.data/http_cache/` when APIs fail briefly

## Favicon
- PNG: `assets/favicon.png`
- SVG: `assets/favicon.svg` / `assets/icons/favicon.svg`
