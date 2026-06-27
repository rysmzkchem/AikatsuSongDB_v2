import streamlit as st
from db import (
    init_db,
    get_all_songs,
    search_song_db,
    get_song_by_title,
    normalize
)

from search_engine import search_song

init_db()

st.set_page_config(page_title="Aikatsu Song DB")
st.write("アイカツ関連楽曲調べるマン")

tab1, tab2 = st.tabs(["🔍 検索・一覧", "📤 CSV・追加・管理"])
st.write("TAB定義後")


# =========================
# TAB1
# =========================
with tab1:
    st.subheader("📚 楽曲一覧")

    rows = get_all_songs()

    if "msg" in st.session_state:
        st.success(st.session_state["msg"])
        del st.session_state["msg"]

    partial_search = st.checkbox("🔍 部分一致検索", value=True)
    keyword = st.text_input("🔍 検索")

    if keyword:
        if partial_search:
            rows = [r for r in rows if keyword.lower() in r["title"].lower()]
        else:
            rows = [r for r in rows if keyword.lower() == r["title"].lower()]

    all_rows = get_all_songs()

    series_list = sorted(set(r["series"] for r in all_rows if r["series"]))
    unit_list = sorted(set(r["unit"] for r in all_rows if r["unit"]))
    composer_list = sorted(set(r["composer"] for r in all_rows if r["composer"]))
    lyricist_list = sorted(set(r["lyricist"] for r in all_rows if r["lyricist"]))
    album_list = sorted(set(r["album"] for r in all_rows if r["album"]))

    with st.sidebar:
        st.subheader("🔎 フィルター")

        series_filter = st.multiselect("シリーズ", series_list)
        unit_filter = st.multiselect("ユニット", unit_list)
        composer_filter = st.multiselect("作曲者", composer_list)
        lyricist_filter = st.multiselect("作詞者", lyricist_list)
        album_filter = st.multiselect("アルバム", album_list)

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

    sort_option = st.selectbox(
        "並び順",
        ["リリース日（新しい順）", "リリース日（古い順）", "曲名（A→Z）", "曲名（Z→A）"]
    )

    if sort_option == "曲名（A→Z）":
        rows = sorted(rows, key=lambda x: x["title"])
    elif sort_option == "曲名（Z→A）":
        rows = sorted(rows, key=lambda x: x["title"], reverse=True)

    st.divider()

    for row in rows:
        with st.container():
            st.subheader(row["title"])
            st.write(row["release_date"])
            st.write(f"{row['album']} / {row['series']} / {row['unit']}")


# =========================
# TAB2
# =========================
with tab2:
    st.subheader("🛠 管理・CSV登録")

    uploaded_file = st.file_uploader(
        "CSVファイルを選択してください",
        type=["csv"]
    )

    if uploaded_file is not None:
        import pandas as pd

        df = pd.read_csv(uploaded_file)

        # ★重要：列名ゆれ・空欄対策
        df.columns = df.columns.str.strip().str.lower()
        df = df.fillna("")

        st.write("プレビュー")
        st.dataframe(df.head())

        st.write("CSV読み込み成功")

       if st.button("CSVを自動補完してDB登録"):
        from search_engine import search_song

        count = 0
        skipped = 0
        errors = 0

        status_area = st.empty()
        progress = st.progress(0)

        for i, row in df.iterrows():
            title = str(row.get("title", "")).strip()

            if not title:
                skipped += 1
                continue

            if get_song_by_title(title):
                skipped += 1
                status_area.info(f"⏭ スキップ済み: {title}")
                continue

            song_id = f"csv_{i}_{title}"

            try:
                status_area.write(f"🔍 検索中: {title}")

                result = search_song(title, song_id)

                status_area.success(
                    f"✅ 完了: {title} / source={result.source} / confidence={result.confidence}"
                )

                count += 1

            except Exception as e:
                errors += 1
                status_area.error(f"❌ エラー: {title} / {e}")
                print(f"[APP ERROR] {title}: {e}")

            progress.progress((i + 1) / len(df))

        st.success(f"登録完了: {count}件 / スキップ {skipped}件 / エラー {errors}件")
        st.rerun()

    st.divider()

    st.subheader("📥 ローカルCSV")

    if st.button("songs.csv取り込み"):
        import pandas as pd
        from search_engine import search_song

        df = pd.read_csv("songs.csv")
        df.columns = df.columns.str.strip().str.lower()
        df = df.fillna("")

        count = 0
        skipped = 0

        for i, row in df.iterrows():
            title = str(row.get("title", "")).strip()

            if not title:
                skipped += 1
                continue

            if get_song_by_title(title):
                skipped += 1
                continue

            song_id = f"import_{i}_{title}"

            search_song(title, song_id)
            count += 1

        st.success(f"{count}件インポート / {skipped}件スキップ")

    st.divider()

    st.subheader("➕ 曲追加（自動補完）")

    with st.form("add_song"):
        title = st.text_input("曲名")

        submitted = st.form_submit_button("追加")

        if submitted:
            from search_engine import search_song

            title = title.strip()

            if not title:
                st.error("曲名を入力してください")
                st.stop()

            if get_song_by_title(title):
                st.info("すでにDBに登録されています")
                st.stop()

            song_id = f"manual_{title}"

            search_song(title, song_id)

            st.success("追加完了（自動補完）")
            st.rerun()