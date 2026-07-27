# React + Streamlit integration

## What works on Streamlit Community Cloud today

1. **`streamlit.components.v1.html`** — HTML/CSS/JS (used for the ☰ drawer).
2. **Published custom components** — React/Vue packaged with `streamlit-component-lib`, built with npm, published to PyPI, then listed in `requirements.txt`.

## Full React sidebar (production path)

```bash
# scaffold (on your machine)
npx create-streamlit-component sosby_sidebar
cd sosby_sidebar/sosby_sidebar/frontend
npm install
# build React UI with Tailwind:
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init
```

`Frontend` sends values back:

```js
import { Streamlit } from "streamlit-component-lib"
Streamlit.setComponentValue({ page: "game_day", team: "browns" })
```

Python:

```python
import streamlit.components.v1 as components
sidebar = components.declare_component("sosby_sidebar", path="sosby_sidebar/frontend/build")
value = sidebar(default={"page": "home"})
if value:
    st.session_state.team_key = value.get("team")
```

Until that package is published, **top Navigate + Streamlit sidebar** remain the reliable routers.

## Tailwind CSS

- **CDN in components.html**: possible for isolated iframes (drawer).
- **Global Streamlit DOM**: no Tailwind build step on Cloud; we emulate utilities via `utils/theme.py` (Outfit font, radius, shadows, pills).
