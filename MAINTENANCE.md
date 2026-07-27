# Maintenance handbook

## Add a team
1. Add entry to `TEAMS` in `utils/api_client.py` (espn_id, espn_path, thesportsdb_id, colors, odds keys).
2. Optional: `utils/team_flavor.py`, `utils/curated_data.py` (PLAYER_POOL, DEFAULT_RUSHMORE), `utils/media_sources.py`.
3. Deploy.

## API failover
`SportsAPIClient` merges ESPN + TheSportsDB with tenacity retries, memory/disk/(optional Redis) cache.

## Errors
Use `utils.error_handler.ui_error` / `safe_ui` for new UI blocks. Toggle **Show data sources** in Settings to see raw errors.

## Do not
- Commit real API secrets.
- Scrape behind logins or violate site ToS for MaxPreps/NFHS.
