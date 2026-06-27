from gemini_client import get_song_info
from models import Song
from db import get_song_by_title, save_song
import json
import requests

# =========================
# Wikipedia検索
# =========================
def search_wikipedia(title: str):
    try:
        url = f"https://ja.wikipedia.org/api/rest_v1/page/summary/{title}"
        res = requests.get(url, timeout=5)

        if res.status_code != 200:
            return None

        data = res.json()

        return {
            "release_date": "",
            "composer": "",
            "lyricist": "",
            "arranger": "",
            "album": data.get("title", ""),
            "series": "",
            "unit": "",
            "source_url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
            "confidence": "low",
        }

    except Exception:
        return None


# =========================
# メイン検索（DB → Wiki → Gemini）
# =========================
def search_song(title: str, song_id: str) -> Song:

    # -------------------------
    # ① DBキャッシュ
    # -------------------------
    cached = get_song_by_title(title)

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
    # ② 初期データ（安全ベース）
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
    # ③ Wikipedia
    # -------------------------
    wiki_data = search_wikipedia(title)

    if wiki_data:
        print(f"[WIKIPEDIA HIT] {title}")
        data.update(wiki_data)
        data["source"] = "Wikipedia"

    # -------------------------
    # ④ Geminiフォールバック
    # -------------------------
    else:
        print(f"[API CALL] {title}")

        try:
            raw_json = get_song_info(title)
            gemini_data = json.loads(raw_json)

            if isinstance(gemini_data, dict):
                data.update(gemini_data)

            data["source"] = "Gemini"

        except Exception:
            print(f"[ERROR] Gemini JSON parse failed: {title}")
            data["source"] = "unknown"

    # -------------------------
    # ⑤ Song生成
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
    # ⑥ DB保存
    # -------------------------
    save_song(song)

    return song