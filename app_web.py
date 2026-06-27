init_db()

import streamlit as st

from db import get_all_songs, search_song_db
st.write("Aikatsu Song DB")
st.write("アイカツ関連楽曲調べるマン")
tab1, tab2 = st.tabs(["🔍 検索・一覧", "📤 CSV・追加・管理"])
st.write("TAB定義後")
with tab1:
    st.subheader("📚 楽曲一覧")

    rows = get_all_songs()

    if "msg" in st.session_state:
        st.success(st.session_state["msg"])
        del st.session_state["msg"]

    # 検索
    partial_search = st.checkbox("🔍 部分一致検索", value=True)
    keyword = st.text_input("🔍 検索")

    if keyword:
        if partial_search:
            rows = [r for r in rows if keyword.lower() in r["title"].lower()]
        else:
            rows = [r for r in rows if keyword.lower() == r["title"].lower()]

    # フィルター候補（検索後じゃなく全体から作るのが安全）
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

    # フィルター
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

    # ソート
    sort_option = st.selectbox(
        "並び順",
        ["リリース日（新しい順）", "リリース日（古い順）", "曲名（A→Z）", "曲名（Z→A）"]
    )

    if sort_option == "リリース日（新しい順）":
        rows = sorted(rows, key=lambda x: x["release_date"], reverse=True)
    elif sort_option == "リリース日（古い順）":
        rows = sorted(rows, key=lambda x: x["release_date"])
    elif sort_option == "曲名（A→Z）":
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

    #st.write("TAB2 is alive")  # ← デバッグ用（重要）

    # =========================
    # CSVアップロード
    # =========================
    uploaded_file = st.file_uploader(
        "CSVファイルを選択してください",
        type=["csv"]
    )

    if uploaded_file is not None:
        import pandas as pd
        from search_engine import search_song

        df = pd.read_csv(uploaded_file)

        st.write("プレビュー")
        st.dataframe(df.head())

        st.write("CSV読み込み成功")

        if st.button("CSVを自動補完してDB登録"):
            count = 0

            for i, row in df.iterrows():
                title = row["title"]
                song_id = f"csv_{i}_{title}"

                search_song(title, song_id)
                count += 1

            st.success(f"{count}件登録しました")
            st.rerun()

    st.divider()

    # =========================
    # ローカルCSV
    # =========================
    st.subheader("📥 ローカルCSV")

    if st.button("songs.csv取り込み"):
        import pandas as pd
        from search_engine import search_song

        df = pd.read_csv("songs.csv")

        count = 0

        for i, row in df.iterrows():
            title = row["title"]
            song_id = f"import_{i}_{title}"

            search_song(title, song_id)
            count += 1

        st.success(f"{count}件インポート")

    st.divider()

    # =========================
    # 手動追加
    # =========================
    st.subheader("➕ 曲追加（自動補完）")

    with st.form("add_song"):

        title = st.text_input("曲名")

        submitted = st.form_submit_button("追加")

        if submitted:
            from search_engine import search_song

            song_id = f"manual_{title}"

            search_song(title, song_id)

            st.success("追加完了（自動補完）")
            st.rerun()