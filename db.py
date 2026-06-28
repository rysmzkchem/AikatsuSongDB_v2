import os
import re
import unicodedata
from supabase import create_client


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL / SUPABASE_KEY が設定されていません")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def normalize(text):
    if not text:
        return ""

    text = str(text)
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = re.sub(r"[！!？?☆★・ー\-_\s　]", "", text)

    return text


def init_db():
    # SupabaseではSQL Editorでテーブル作成済みなので何もしない
    return


def add_song(song: dict):
    song["title_norm"] = normalize(song.get("title", ""))

    result = supabase.table("songs").upsert(song).execute()
    return result


def get_all_songs():
    result = supabase.table("songs").select("*").execute()
    return result.data


def get_song_by_title(title):
    title_norm = normalize(title)

    result = (
        supabase.table("songs")
        .select("*")
        .eq("title_norm", title_norm)
        .limit(1)
        .execute()
    )

    if result.data:
        return result.data[0]

    return None


def search_song_db(keyword):
    keyword_norm = normalize(keyword)

    result = (
        supabase.table("songs")
        .select("*")
        .ilike("title_norm", f"%{keyword_norm}%")
        .execute()
    )

    return result.data


def update_song(song_id, updates):
    updates["title_norm"] = normalize(updates.get("title", ""))

    result = (
        supabase.table("songs")
        .update(updates)
        .eq("id", song_id)
        .execute()
    )

    return result


def delete_song(song_id):
    result = (
        supabase.table("songs")
        .delete()
        .eq("id", song_id)
        .execute()
    )

    return result


def update_all_title_norm():
    rows = get_all_songs()

    for r in rows:
        update_song(
            r["id"],
            {
                **r,
                "title_norm": normalize(r.get("title", ""))
            }
        )