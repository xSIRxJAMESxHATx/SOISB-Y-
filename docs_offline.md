# Offline & Service Workers

## What Streamlit Cloud allows
- **No custom Service Worker** registration on `*.streamlit.app` for arbitrary offline shells.
- Browser HTTP cache still helps static assets.
- App logic offline ≈ **memory + disk (+ optional Redis) cache** + **Prefer cached / offline** toggle.

## Our strategy
1. `st.cache_data` on pure feed helpers (`utils/cached_feeds.py`)
2. Disk cache in `utils/disk_cache.py`
3. Optional Redis
4. Explicit messages via `utils/offline_mode.py` when cache is empty offline

## Session-state navigation
- `utils/nav_state.py` tracks `last_page` and `nav_history`
- `st.page_link` / `st.switch_page` for real multipage jumps
- Sidebar links stay available on every page

## GIFs
Place files in `assets/gifs/` and call `show_gif("name")`.
