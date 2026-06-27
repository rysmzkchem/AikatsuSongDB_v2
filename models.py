# models.py

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Song:
    id: str
    title: str

    release_date: str = ""
    composer: str = ""
    lyricist: str = ""
    arranger: str = ""

    album: str = ""
    series: str = ""
    unit: str = ""

    source: str = ""
    source_url: str = ""

    confidence: str = "unknown"
    status: str = "new"

    def to_dict(self):
        return asdict(self)