import pandas as pd
from db import add_song

CSV_PATH = "output.csv"

def convert_row(row):
    return {
        "id": str(row.get("id", "")),
        "title": str(row.get("title", "")),
        "release_date": str(row.get("release_date", "")),
        "composer": str(row.get("composer", "")),
        "lyricist": str(row.get("lyricist", "")),
        "arranger": str(row.get("arranger", "")),
        "album": str(row.get("album", "")),
        "series": str(row.get("series", "")),
        "unit": str(row.get("unit", "")),
        "source": str(row.get("source", "")),
        "source_url": str(row.get("source_url", "")),
        "confidence": str(row.get("confidence", "")),
        "status": str(row.get("status", ""))
    }


def main():
    df = pd.read_csv(CSV_PATH)

    for _, row in df.iterrows():
        song = convert_row(row)
        add_song(song)

    print("CSV → SQLite 移行完了")


if __name__ == "__main__":
    main()