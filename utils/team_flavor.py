"""Team slogans, phrases, inside jokes — curated with safe defaults."""
from __future__ import annotations
from typing import Dict, List

FLAVOR: Dict[str, dict] = {
    "browns": {
        "slogan": "Here We Go Brownies — Dawg Pound forever.",
        "phrases": ["Dawg Pound", "Believeland", "Factory of Sadness (we own the meme)", "Orange and Brown pride", "Cleveland rocks"],
        "witty": "Whatever the record, the lake-effect loyalty never melts.",
    },
    "guardians": {
        "slogan": "Guarded by the lake. Powered by Progressive Field.",
        "phrases": ["Go Guards", "Our time", "Jake from State Farm energy", "Cleveland baseball summers"],
        "witty": "When the bats wake up, the whole North Coast hears it.",
    },
    "cavaliers": {
        "slogan": "All for Caviland — The Land remembers 2016.",
        "phrases": ["The Land", "Caviland", "Believe", "Sword and shield", "Wine and gold"],
        "witty": "From The Shot to The Block — Northeast Ohio writes the script.",
    },
    "osu_football": {
        "slogan": "Script Ohio. Hang on tight.",
        "phrases": ["O-H!", "I-O!", "The Shoe", "Go Bucks", "Across the field"],
        "witty": "If you hear the Skull Session, you already know how Saturday goes.",
    },
    "osu_mbb": {
        "slogan": "Buckeyes in the paint — Scarlet and Gray never sleep.",
        "phrases": ["Go Bucks", "Value City Arena energy", "Scarlet pressure"],
        "witty": "When the threes rain in Columbus, the whole Big Ten checks the radar.",
    },
    "crew": {
        "slogan": "Massive. Black & gold. Nordecke loud.",
        "phrases": ["Massive", "Nordecke", "Crew forever", "Lower.com Field nights"],
        "witty": "If the drums start early, the opponents already lost the parking lot.",
    },
    "bluejackets": {
        "slogan": "CBJ — Cannon ready.",
        "phrases": ["CBJ", "Cannon fodder for the other team", "Nationwide Arena nights", "Union Blue"],
        "witty": "When that cannon fires, High Street feels it two blocks over.",
    },
    "usmnt": {
        "slogan": "I believe that we will win.",
        "phrases": ["USMNT", "I believe", "Sam's Army", "Stars and Stripes"],
        "witty": "From Concacaf chaos to World Cup dreams — always loud, always ours.",
    },
    "usab": {
        "slogan": "USA Basketball — gold standard.",
        "phrases": ["Team USA", "Dream Team DNA", "Red, white, and blue"],
        "witty": "When the USA puts five on the floor, the whole planet checks the scoreboard.",
    },
    "kent_mbb": {
        "slogan": "Golden Flashes — MAC attack.",
        "phrases": ["Go Flashes", "MAC pride", "Kent State fight"],
        "witty": "Never count out the Flashes when March starts whispering.",
    },
    "rhs_football": {
        "slogan": "Reynoldsburg Raiders — purple and orange pride.",
        "phrases": ["Go Raiders", "OCC battle", "Raider Nation"],
        "witty": "Friday nights under the lights — central Ohio classic.",
    },
    "rhs_mbb": {
        "slogan": "Raiders basketball — hard cuts, harder defense.",
        "phrases": ["Go Raiders", "Purple storm"],
        "witty": "When the gym packs out, every possession feels like a playoff game.",
    },
    "tiffin_tf": {
        "slogan": "Tiffin Dragons — track that breathes fire.",
        "phrases": ["Go Dragons", "G-MAC distance", "Spike up"],
        "witty": "Lanes, jumps, throws — Dragons measure excellence in fractions of a second.",
    },
}

DEFAULT_FLAVOR = {
    "slogan": "Ohio sports — loud, loyal, legendary.",
    "phrases": ["Believeland", "Cleveland rocks", "Ohio pride"],
    "witty": "From the lake to the campus, we show up.",
}


def get_flavor(team_key: str) -> dict:
    return FLAVOR.get(team_key, DEFAULT_FLAVOR)
