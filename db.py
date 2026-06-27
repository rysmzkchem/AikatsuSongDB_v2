

DB_NAME = "aikatsu.db"

import re

def normalize(text):
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"[！!？?☆★・ー\-_\s]", "", text)
    return text

import sqlite3
# =========================
# 接続
# =========================
def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# 初期化
# =========================
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS songs (
        id TEXT PRIMARY KEY,
        title TEXT,
        release_date TEXT,
        composer TEXT,
        lyricist TEXT,
        arranger TEXT,
        album TEXT,
        series TEXT,
        unit TEXT,
        source TEXT,
        source_url TEXT,
        confidence TEXT,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()


# =========================
# 追加
# =========================
def add_song(song):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO songs VALUES (
        :id, :title, :release_date, :composer, :lyricist,
        :arranger, :album, :series, :unit,
        :source, :source_url, :confidence, :status
    )
    """, song)

    conn.commit()
    conn.close()


# =========================
# 全件取得
# =========================
def get_all_songs():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM songs")
    rows = cur.fetchall()

    conn.close()
    return rows


# =========================
# 検索
# =========================
def search_song_db(keyword):
    conn = get_connection()
    cursor = conn.cursor()

    keyword = normalize(keyword)

    cursor.execute("SELECT * FROM songs")
    rows = cursor.fetchall()

    result = []

    for r in rows:
        if keyword in normalize(r["title"]):
            result.append(r)

    return result


# =========================
# 更新
# =========================
def update_song(song_id, updates):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    UPDATE songs
    SET title=?,
        release_date=?,
        composer=?,
        lyricist=?,
        arranger=?,
        album=?,
        series=?,
        unit=?,
        source=?,
        source_url=?,
        confidence=?,
        status=?
    WHERE id=?
    """, (
        updates["title"],
        updates["release_date"],
        updates["composer"],
        updates["lyricist"],
        updates["arranger"],
        updates["album"],
        updates["series"],
        updates["unit"],
        updates["source"],
        updates["source_url"],
        updates["confidence"],
        updates["status"],
        song_id
    ))

    conn.commit()
    conn.close()


# =========================
# 削除
# =========================
def delete_song(song_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM songs WHERE id=?", (song_id,))

    conn.commit()
    conn.close()