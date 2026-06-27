from gemini_client import get_song_info
from models import Song
from db import init_db, save_song, get_song_by_title
import json

# DB初期化（必ず最初に実行）
init_db()


def search_song(title: str, song_id: str) -> Song:

    # -----------------------------
    # ① DBチェック
    # -----------------------------
    cached = get_song_by_title(title)

    if cached:
        print(f"[DB HIT] {title}")

        return Song(
            id=cached[0],
            title=cached[1],
            release_date=cached[2],
            composer=cached[3],
            lyricist=cached[4],
            arranger=cached[5],
            album=cached[6],
            series=cached[7],
            unit=cached[8],
            source=cached[9],
            source_url=cached[10],
            confidence=cached[11],
            status=cached[12]
        )

    # -----------------------------
    # ② Gemini検索
    # -----------------------------
    print(f"[API CALL] {title}")

    raw_json = get_song_info(title)

    try:
        data = json.loads(raw_json)
    except Exception:
        print(f"[ERROR] JSON parse failed: {title}")
        data = {}

    # -----------------------------
    # ③ Song生成
    # -----------------------------
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
        source=data.get("source", "Wikipedia/Gemini"),
        source_url=data.get("source_url", ""),
        confidence=data.get("confidence", "unknown"),
        status="done"
    )

    # -----------------------------
    # ④ DB保存
    # -----------------------------
    save_song(song)

    return song