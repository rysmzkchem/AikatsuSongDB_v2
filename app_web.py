import streamlit as st
from db import get_all_songs, search_song_db

# タイトル
st.title("Aikatsu Song DB")
st.caption("アイカツ関係の楽曲調べるマン")
tab1, tab2 = st.tabs(["📚 一覧・検索", "🛠 管理"])

#tub1
with tab1:
    rows = get_all_songs()
    series_list = sorted(set(r["series"] for r in rows if r["series"]))
    unit_list = sorted(set(r["unit"] for r in rows if r["unit"]))
    composer_list = sorted(set(r["composer"] for r in rows if r["composer"]))
    lyricist_list = sorted(set(r["lyricist"] for r in rows if r["lyricist"]))
    album_list = sorted(set(r["album"] for r in rows if r["album"]))

    if "msg" in st.session_state:
        st.success(st.session_state["msg"])
        del st.session_state["msg"]
    
    st.subheader("📚 楽曲一覧")

    partial_search = st.checkbox("🔍 部分一致検索を有効にする", value=True)
    keyword = st.text_input("🔍 検索")

    if keyword:
        if partial_search:
            # 部分一致（ゆるい検索）
            rows = [
                r for r in rows
                if keyword.lower() in r["title"].lower()
            ]
        else:
            # 完全一致
            rows = [
                r for r in rows
                if keyword.lower() == r["title"].lower()
            ]
    
    #Filter
    st.subheader("🔃 ソート")

    

    sort_option = st.selectbox(
        "並び順",
        [
            "リリース日（新しい順）",
            "リリース日（古い順）",
            "曲名（A→Z）",
            "曲名（Z→A）"
        ],
        key="sort_option"
    )
    with st.sidebar:
        st.subheader("🔎 フィルター")

        series_filter = st.multiselect("シリーズ", [""] + series_list, key="series_filter")
        unit_filter = st.multiselect("ユニット", [""] + unit_list, key="unit_filter")
        composer_filter = st.multiselect("作曲者", [""] + composer_list, key="composer_filter")
        lyricist_filter = st.multiselect("作詞者", [""] + lyricist_list, key="lyricist_filter")
        album_filter = st.multiselect("アルバム", [""] + album_list, key="album_filter")
#Filter適用
    filtered = []
    for r in rows:

        if series_filter and r["series"] not in series_filter:
            continue
        if unit_filter and r["unit"] not in unit_filter:
            continue
        if composer_filter and r["composer"] not in composer_filter:
            continue
        if lyricist_filter and r["lyricist"] not in lyricist_filter:
            continue
        if album_filter and r["album"] not in album_filter:
            continue
        filtered.append(r)
    rows = filtered
    # =========================
    # ソート処理
    # =========================

    if sort_option == "リリース日（新しい順）":
        rows = sorted(rows, key=lambda x: x["release_date"], reverse=True)

    elif sort_option == "リリース日（古い順）":
        rows = sorted(rows, key=lambda x: x["release_date"])

    elif sort_option == "曲名（A→Z）":
        rows = sorted(rows, key=lambda x: x["title"])

    elif sort_option == "曲名（Z→A）":
        rows = sorted(rows, key=lambda x: x["title"], reverse=True)


st.divider()

# Row取得
for row in rows:
    with st.container():
        st.markdown("---")

        st.subheader(row["title"])

        st.write(f"📅 {row['release_date']}")
        st.write(f"💿 {row['album']} | 📺 {row['series']} | 👥 {row['unit']}")

    with st.expander("✏ 編集"):
        
        new_title = st.text_input(
            "曲名",
            row["title"],
            key="title_" + str(row["id"])
        )

        new_unit = st.text_input(
            "ユニット",
            row["unit"],
            key="unit_" + str(row["id"])
        )

        new_album = st.text_input(
            "収録アルバム",
            row["album"],
            key="album_" + str(row["id"])
        )
        new_series = st.text_input(
            "シリーズ",
            row["series"],
            key="series_" + str(row["id"])
        )

        if st.button("更新", key="upd_" + str(row["id"])):
            row_dict = dict(row)
            from db import update_song
            #未入力防止
            if not new_title:
                st.error("曲名は必須です")
                st.stop()
            update_song(row["id"], {
                "title": new_title,
                "unit": new_unit,
                "album": new_album,
                "series": new_series,

                "release_date": row["release_date"],
                "composer": row["composer"],
                "lyricist": row["lyricist"],
                "arranger": row["arranger"],

                "source": row_dict.get("source", ""),
                "source_url": row_dict.get("source_url", ""),
                "confidence": row_dict.get("confidence", ""),
                "status": row_dict.get("status", "")
            })

            st.session_state["msg"] = "更新しました"
            st.rerun()
        


            if st.button("🗑 削除", key="del_" + str(row["id"])):
                st.warning("本当に削除しますか？")
                if st.button("管理人へご連絡ください"):
                    delete_song(row["id"])
                    st.rerun()

if keyword:
        rows = search_song_db(keyword)
else:
        rows = get_all_songs()

for row in rows:
        st.write(row[1], row[2])
# CSVダウンロード（ここに入れる）
# =========================
import pandas as pd

df = pd.DataFrame(rows)

csv = df.to_csv(index=False, encoding="utf-8-sig")
st.divider()
st.download_button(
    label="📥 フィルター結果をCSVダウンロード",
    data=csv,
    file_name="aikatsu_filtered.csv",
    mime="text/csv"
)
st.divider()
#tub2
with tab2:
    st.subheader("➕ 曲の追加")

    with st.form("add_song"):
        song_id = st.text_input("ID")
        title = st.text_input("曲名")
        release_date = st.text_input("リリース日")
        composer = st.text_input("作曲")
        lyricist = st.text_input("作詞")
        arranger = st.text_input("編曲")
        album = st.text_input("アルバム")
        series = st.text_input("シリーズ")
        unit = st.text_input("ユニット")

        submitted = st.form_submit_button("追加")

        if submitted:
            from db import add_song

            add_song({
                "id": song_id,
                "title": title,
                "release_date": release_date,
                "composer": composer,
                "lyricist": lyricist,
                "arranger": arranger,
                "album": album,
                "series": series,
                "unit": unit,
                "source": "manual",
                "source_url": "",
                "confidence": "manual",
                "status": "done"
            })

            st.success("追加しました")
            st.rerun()

