# SO!SB!Y! — Superb Owl! Super Browns! Yeah!

Ohio-centric multi-team sports hub with live scores, weather, betting tools, **Supabase community** (JSON failover), Cleveland desk bot, Superb Owl branding, and optional Twilio SMS.

## Brand

- **Name:** SO!SB!Y!
- **Banner:** Superb Owl! Super Browns! Yeah!
- **Mascot:** Classy Superb Owl (monocle, Browns crown, mitt, Cavs ball, cigar energy) — light site watermark + sidebar icon

## Secrets

```toml
ODDS_API_KEY = "..."
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_KEY = "anon_or_service_key"
TWILIO_ACCOUNT_SID = "ACxxxx"
TWILIO_AUTH_TOKEN = "xxxx"
TWILIO_FROM_NUMBER = "+1xxxx"
MOD_PASSWORD = "strong_mod_password"
```

### Supabase SQL (run once in Supabase SQL editor)

```sql
create table if not exists community_topics (
  id bigint generated always as identity primary key,
  team text, title text, author text, tags jsonb default '[]',
  created double precision, updated double precision
);
create table if not exists community_posts (
  id bigint generated always as identity primary key,
  topic_id bigint references community_topics(id) on delete cascade,
  author text, body text, created double precision,
  up int default 0, down int default 0,
  image_url text default '', link_url text default ''
);
create table if not exists community_users (
  name text primary key, avatar text, posts int default 0
);
-- Enable read/write for anon as appropriate for a fan board, or use RLS policies.
```

Without Supabase, community falls back to local `.data/community.json`.

## Auto-refresh

Default ~45s for scores while the tab is open.

## Statistical arbitrage (education)

- Cross-book 2-way ML arb scan  
- Price dispersion (best vs worst decimal)  
- Best-price implied sum / edge table  
- Conceptual z-score / live strategy notes  

## Deploy

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Limits

- No offline SMS without external worker  
- Image generation is Pillow-local (cards, Rushmore, weather, owl) — no external AI image API required  
- Users cannot edit app code  

## Suggestions

**Add:** Supabase RLS policies; CDN for assets; PWA.  
**Remove:** Nothing critical; avoid committing secrets.
