from gemini_client import get_song_info
from models import Song
from db import get_song_by_title, add_song

import json
import requests
import re
import unicodedata


def normalize(text):
    if not text:
        return ""

    text = str(text)
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = re.sub(r"[！!？?☆★・ー\-_\s　]", "", text)

    return text


def has_missing_required(data):
    required = ["release_date", "composer", "lyricist", "arranger", "album", "series", "unit"]
    return any(not data.get(k) for k in required)


def merge_if_empty(base: dict, new: dict):
    for k, v in new.items():
        if not base.get(k) and v:
            base[k] = v


def search_wikipedia(title: str):
    try:
        search_url = "https://ja.wikipedia.org/w/api.php"

        params = {
            "action": "query",
            "list": "search",
            "srsearch": title,
            "format": "json"
        }

        res = requests.get(search_url, params=params, timeout=5)
        if res.status_code != 200:
            return None

        data = res.json()

        if not data.get("query", {}).get("search"):
            return None

        page_title = data["query"]["search"][0]["title"]

        summary_url = f"https://ja.wikipedia.org/api/rest_v1/page/summary/{page_title}"
        res2 = requests.get(summary_url, timeout=5)

        if res2.status_code != 200:
            return None

        page = res2.json()

        return {
            "release_date": "",
            "composer": "",
            "lyricist": "",
            "arranger": "",
            "album": page.get("title", ""),
            "series": "",
            "unit": "",
            "source_url": page.get("content_urls", {}).get("desktop", {}).get("page", ""),
            "confidence": "low"
        }

    except Exception as e:
        print(f"[WIKI ERROR] {e}")
        return None


def search_song(title: str, song_id: str) -> Song:
    print(f"[START] {title}")

    norm_title = normalize(title)
    print(f"[NORMALIZE] {title} -> {norm_title}")

    cached = get_song_by_title(norm_title)

    if cached:
        print(f"[DB HIT] {title}")
        return Song(
            id=cached["id"],
            title=cached["title"],
            release_date=cached["release_date"],
            composer=cached["composer"],
            lyricist=cached["lyricist"],
            arranger=cached["arranger"],
            album=cached["album"],
            series=cached["series"],
            unit=cached["unit"],
            source=cached["source"],
            source_url=cached["source_url"],
            confidence=cached["confidence"],
            status=cached["status"]
        )

    print(f"[DB MISS] {title}")

    data = {
        "release_date": "",
        "composer": "",
        "lyricist": "",
        "arranger": "",
        "album": "",
        "series": "",
        "unit": "",
        "source": "",
        "source_url": "",
        "confidence": "unknown"
    }

    print(f"[WIKI START] {title}")
    wiki_data = search_wikipedia(title)

    if wiki_data:
        print(f"[WIKI HIT] {title}: {wiki_data}")
        merge_if_empty(data, wiki_data)
        data["source"] = "Wikipedia"
    else:
        print(f"[WIKI MISS] {title}")

    if has_missing_required(data):
        print(f"[GEMINI START] {title}")

        try:
            raw = get_song_info(title)
            print(f"[GEMINI RAW] {title}: {raw}")

            gemini_data = json.loads(raw)
            print(f"[GEMINI DATA] {title}: {gemini_data}")

            if isinstance(gemini_data, dict):
                merge_if_empty(data, gemini_data)

            if data.get("source"):
                data["source"] = data["source"] + "+Gemini"
            else:
                data["source"] = "Gemini"

        except Exception as e:
            print(f"[GEMINI ERROR] {title}: {e}")
            if not data.get("source"):
                data["source"] = "unknown"
            data["confidence"] = data.get("confidence") or "low"

    else:
        print(f"[GEMINI SKIP] {title} / no missing fields")

    print(f"[FINAL DATA] {title}: {data}")

    song = Song(
        id=song_id,
        title=title,
        release_date=data.get("release_date", ""),
        composer=data.get("composer", ""),
        lyricist=data.get("lyricist", ""),
        arranger=data.get("arranger", ""),
        album=data.get("album", ""),
        series=data.get("series", ""),
        unit=data.get("unit", ""),
        source=data.get("source", ""),
        source_url=data.get("source_url", ""),
        confidence=data.get("confidence", "unknown"),
        status="done"
    )

    print(f"[SAVE START] {title}")
    add_song(song.__dict__)
    print(f"[SAVE DONE] {title}")

    return song