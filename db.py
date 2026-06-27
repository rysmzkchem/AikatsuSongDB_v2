

DB_NAME = "aikatsu.db"

import re
import unicodedata

def normalize(text):
    if not text:
        return ""

    # 全角→半角・統一
    text = unicodedata.normalize("NFKC", text)

    # 小文字化
    text = text.lower()

    # 記号・空白除去（強化版）
    text = re.sub(r"[！!？?☆★・ー\-_\s　]", "", text)

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

    # カラム存在チェック
    cur.execute("PRAGMA table_info(songs)")
    columns = [c[1] for c in cur.fetchall()]

    if "title_norm" not in columns:
        cur.execute("ALTER TABLE songs ADD COLUMN title_norm TEXT")

    conn.commit()
    conn.close()


# =========================
# 追加
# =========================
def add_song(song):
    conn = get_connection()
    cur = conn.cursor()

    song["title_norm"] = normalize(song["title"])

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
def get_song_by_title(title):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT * FROM songs
    WHERE title_norm = ?
    """, (normalize(title),))

    row = cur.fetchone()
    conn.close()
    return row
def search_song_db(keyword):
    conn = get_connection()
    cur = conn.cursor()

    keyword = normalize(keyword)

    cur.execute("""
    SELECT * FROM songs
    WHERE title_norm LIKE ?
    """, (f"%{keyword}%",))

    rows = cur.fetchall()
    conn.close()

    return rows
#存在チェック
def get_song_by_title(title):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM songs")
    rows = cur.fetchall()

    for r in rows:
        if normalize(title) == normalize(r["title"]):
            conn.close()
            return r

    conn.close()
    return None
    
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

# =========================
# 既存データ正規化更新（←ここに追加）
# =========================
def update_all_title_norm():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, title FROM songs")
    rows = cur.fetchall()

    for r in rows:
        cur.execute("""
        UPDATE songs
        SET title_norm = ?
        WHERE id = ?
        """, (normalize(r["title"]), r["id"]))

    conn.commit()
    conn.close()