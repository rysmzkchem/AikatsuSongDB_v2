from gemini_client import get_song_info
from models import Song
from db import get_song_by_title, add_song

import json
import requests

import re
import unicodedata

def normalize(text: str) -> str:
    if not text:
        return ""

    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = re.sub(r"[！!？?☆★・ー\-_\s　]", "", text)

    return text
# =========================
# Wikipedia検索（安定版）
# =========================
def search_wikipedia(title: str):
    try:
        # 検索API（summary直叩きより安定）
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

        # summary取得
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


# =========================
# メイン検索
# =========================
def search_song(title: str, song_id: str) -> Song:

    # -------------------------
    # 0. 正規化（重要）
    # -------------------------
    norm_title = normalize(title)

    # -------------------------
    # 1. DBキャッシュ（安定版）
    # -------------------------
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

    # -------------------------
    # 2. 初期安全データ
    # -------------------------
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

    # -------------------------
    # 3. Wikipedia
    # -------------------------
    wiki_data = search_wikipedia(title)

    if wiki_data:
        print(f"[WIKI HIT] {title}")
        data.update(wiki_data)
        data["source"] = "Wikipedia"

    # -------------------------
    # 4. Gemini（最終手段）
    # -------------------------
    else:
        print(f"[GEMINI CALL] {title}")

        try:
            raw = get_song_info(title)
            gemini_data = json.loads(raw)

            if isinstance(gemini_data, dict):
                data.update(gemini_data)

            data["source"] = "Gemini"

        except Exception as e:
            print(f"[GEMINI ERROR] {e}")

            # ★完全フォールバック（絶対落とさない）
            data["source"] = "unknown"
            data["confidence"] = "low"

    # -------------------------
    # 5. Song生成
    # -------------------------
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

    # -------------------------
    # 6. DB保存（必ず成功）
    # -------------------------
    add_song({
        "id": song.id,
        "title": song.title,
        "release_date": song.release_date,
        "composer": song.composer,
        "lyricist": song.lyricist,
        "arranger": song.arranger,
        "album": song.album,
        "series": song.series,
        "unit": song.unit,
        "source": song.source,
        "source_url": song.source_url,
        "confidence": song.confidence,
        "status": song.status
    })
    return song