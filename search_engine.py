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


def merge_if_empty(base: dict, new: dict):
    for k, v in new.items():
        if not base.get(k) and v:
            base[k] = v


def has_missing_required(data):
    required = ["release_date", "composer", "lyricist", "arranger", "album", "series", "unit"]
    return any(not data.get(k) for k in required)

def search_aikatsu_wiki(title: str):
    try:
        search_url = "https://all-aikatsu.fandom.com/wiki/Special:Search"

        params = {
            "query": title
        }

        res = requests.get(search_url, params=params, timeout=5)

        if res.status_code != 200:
            return None

        text = res.text

        if title not in text:
            return None

        return {
            "release_date": "",
            "composer": "",
            "lyricist": "",
            "arranger": "",
            "album": "",
            "series": "アイカツ！",
            "unit": "",
            "source_url": res.url,
            "confidence": ""
        }

    except Exception as e:
        print(f"[AIKATSU WIKI ERROR] {title}: {e}", flush=True)
        return None
    
def search_wikipedia_aikatsu(title: str):
    queries = [
        f"{title} アイカツ",
        f"{title} アイカツ!",
        f"{title} アイカツスターズ",
        f"{title} アイカツプラネット",
        f"{title} アイカツフレンズ",
        f"{title} フォト on ステージ",
        f"{title} アイカツオンパレード",
        f"{title} アイカツアカデミー",
    ]

    for q in queries:
        try:
            search_url = "https://ja.wikipedia.org/w/api.php"

            params = {
                "action": "query",
                "list": "search",
                "srsearch": q,
                "format": "json"
            }

            res = requests.get(search_url, params=params, timeout=5)
            if res.status_code != 200:
                continue

            data = res.json()
            results = data.get("query", {}).get("search", [])

            if not results:
                continue

            page_title = results[0]["title"]

            if "アイカツ" not in page_title and "STAR" not in page_title:
                continue

            summary_url = f"https://ja.wikipedia.org/api/rest_v1/page/summary/{page_title}"
            res2 = requests.get(summary_url, timeout=5)

            if res2.status_code != 200:
                continue

            page = res2.json()

            return {
                "release_date": "",
                "composer": "",
                "lyricist": "",
                "arranger": "",
                "album": page.get("title", ""),
                "series": "アイカツ！",
                "unit": "",
                "source_url": page.get("content_urls", {}).get("desktop", {}).get("page", ""),
                "confidence": "medium"
            }

        except Exception as e:
            print(f"[WIKI AIKATSU ERROR] {title}: {e}", flush=True)

    return None

def search_song(title: str, song_id: str) -> Song:
    print(f"[START] {title}", flush=True)

    norm_title = normalize(title)
    print(f"[NORMALIZE] {title} -> {norm_title}", flush=True)

    cached = get_song_by_title(norm_title)

    if cached:
        print(f"[DB HIT] {title}", flush=True)
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

    print(f"[DB MISS] {title}", flush=True)

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

    print(f"[WIKI AIKATSU START] {title}", flush=True)
    wiki_data = search_wikipedia_aikatsu(title)

    if wiki_data:
        print(f"[WIKI AIKATSU HIT] {title}: {wiki_data}", flush=True)
        merge_if_empty(data, wiki_data)
        data["source"] = "Wikipedia"
    else:
        print(f"[WIKI AIKATSU MISS] {title}", flush=True)

    print(f"[AIKATSU WIKI START] {title}", flush=True)
    aikatsu_wiki_data = search_aikatsu_wiki(title)

    if aikatsu_wiki_data:
        print(f"[AIKATSU WIKI HIT] {title}: {aikatsu_wiki_data}", flush=True)
        merge_if_empty(data, aikatsu_wiki_data)

        if data.get("source"):
            data["source"] += "+AikatsuWiki"
        else:
            data["source"] = "AikatsuWiki"
    else:
        print(f"[AIKATSU WIKI MISS] {title}", flush=True)

    if has_missing_required(data):
        print(f"[GEMINI START] {title}", flush=True)

        try:
            raw = get_song_info(title)
            print(f"[GEMINI RAW] {title}: {raw}", flush=True)

            gemini_data = json.loads(raw)
            print(f"[GEMINI DATA] {title}: {gemini_data}", flush=True)

            if isinstance(gemini_data, dict):
                merge_if_empty(data, gemini_data)

            if data.get("source"):
                data["source"] += "+Gemini"
            else:
                data["source"] = "Gemini"

        except Exception as e:
            print(f"[GEMINI ERROR] {title}: {e}", flush=True)

            if not data.get("source"):
                data["source"] = "unknown"

            data["confidence"] = data.get("confidence") or "low"

    else:
        print(f"[GEMINI SKIP] {title} / no missing fields", flush=True)

    print(f"[FINAL DATA] {title}: {data}", flush=True)

    if data.get("source") == "Gemini" and has_missing_required(data):
        print(f"[SKIP SAVE] Gemini failed or incomplete: {title}", flush=True)
        raise Exception("Gemini補完に失敗したためDB保存をスキップしました")

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

    print(f"[SAVE START] {title}", flush=True)

    try:
        add_song(song.__dict__)
        print(f"[SAVE DONE] {title}", flush=True)

    except Exception as e:
        print(f"[SAVE ERROR] {title}: {e}", flush=True)
        raise

    return song