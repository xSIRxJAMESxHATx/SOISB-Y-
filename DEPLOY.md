# Deploy SO!SB!Y! on Streamlit Community Cloud

1. Push this folder to GitHub (`app.py` at repo root or set main file path).
2. [share.streamlit.io](https://share.streamlit.io) → New app → select repo/branch → Main file `app.py`.
3. **Secrets** (optional but recommended):

```toml
ODDS_API_KEY = "..."
TWILIO_ACCOUNT_SID = "..."
TWILIO_AUTH_TOKEN = "..."
TWILIO_FROM_NUMBER = "+1..."
MOD_PASSWORD = "..."
SUPABASE_URL = "..."
SUPABASE_KEY = "..."
# optional
REDIS_URL = "..."
SPORTS_WS_URL = "..."
```

4. Ensure `requirements.txt` installs (streamlit, pandas, plotly, pillow, requests, tenacity, fpdf2, streamlit-autorefresh).
5. After deploy, open the app once and hit **↻ Refresh now** to warm caches.

## Mobile
- Open the **sidebar** (Streamlit’s ☰ control) for team switch, dark mode, refresh interval, Profile, Settings/API.
- Main page has a second team dropdown when the sidebar is closed.

## Favicons
`assets/favicon.png` is used as `page_icon`. Full icon set lives under `assets/icons/`.
