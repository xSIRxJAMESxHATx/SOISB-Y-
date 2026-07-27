"""Notable fan / official links per team (Reddit + more)."""
from __future__ import annotations

from utils.api_client import reddit_url, TEAMS

# Extra notable destinations beyond Reddit
EXTRA = {
    "browns": [
        ("Official site", "https://www.clevelandbrowns.com/"),
        ("Dawg Pound territory (search)", "https://www.google.com/search?q=Dawg+Pound+Cleveland+Browns"),
        ("Cleveland.com Browns", "https://www.cleveland.com/browns/"),
    ],
    "guardians": [
        ("Official site", "https://www.mlb.com/guardians"),
        ("Cleveland.com Guardians", "https://www.cleveland.com/guardians/"),
        ("The Scorekeeper / Tribe chat (search)", "https://www.google.com/search?q=Cleveland+Guardians+fan+forum"),
    ],
    "cavaliers": [
        ("Official site", "https://www.nba.com/cavaliers"),
        ("Cleveland.com Cavs", "https://www.cleveland.com/cavs/"),
        ("Fear the Sword", "https://www.fearthesword.com/"),
    ],
    "osu_football": [
        ("Official athletics", "https://ohiostatebuckeyes.com/sports/football"),
        ("Eleven Warriors", "https://www.elevenwarriors.com/"),
        ("BuckeyeGrove (search)", "https://www.google.com/search?q=Ohio+State+football+fan+forum"),
    ],
    "osu_mbb": [
        ("Official MBB", "https://ohiostatebuckeyes.com/sports/mens-basketball"),
        ("Eleven Warriors", "https://www.elevenwarriors.com/"),
    ],
    "crew": [
        ("Official", "https://www.columbuscrew.com/"),
        ("Massive Report", "https://www.massivereport.com/"),
    ],
    "bluejackets": [
        ("Official", "https://www.nhl.com/bluejackets"),
        ("The Cannon", "https://www.thecannonnhl.com/"),
    ],
    "usmnt": [
        ("USSF", "https://www.ussoccer.com/"),
        ("r/ussoccer", "https://www.reddit.com/r/ussoccer/"),
    ],
    "usab": [
        ("USA Basketball", "https://www.usab.com/"),
    ],
}


def fan_links_for(team_key: str) -> list:
    team = TEAMS.get(team_key) or {}
    links = []
    try:
        links.append({"name": f"Reddit · {team.get('short') or team_key}", "url": reddit_url(team_key)})
    except Exception:
        pass
    for name, url in EXTRA.get(team_key, []):
        links.append({"name": name, "url": url})
    # always a couple of generic searches
    q = (team.get("name") or team_key).replace(" ", "+")
    links.append({"name": "Google News", "url": f"https://news.google.com/search?q={q}"})
    links.append({"name": "YouTube highlights search", "url": f"https://www.youtube.com/results?search_query={q}+highlights"})
    return links
