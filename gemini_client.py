from google import genai
from google.genai import types
from pathlib import Path
import re

from config import API_KEY, MODEL_NAME

client = genai.Client(api_key=API_KEY)

# ★これが絶対に必要
PROMPT_PATH = Path("prompts/song_prompt.txt")


def get_song_info(title: str) -> str:
    prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
    prompt = prompt_template.format(title=title)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0,
        )
    )

    if response is None or response.text is None:
        print("[ERROR] response is empty")
        return "{}"

    text = response.text.strip()

    # ★① コードブロック削除（最初にやる）
    text = text.replace("```json", "")
    text = text.replace("```", "")
    text = text.strip()

    # ★② JSONパース（ここが本命）
    import json

    try:
        data = json.loads(text)
        return json.dumps(data, ensure_ascii=False)
    except Exception:
        print("[ERROR] JSONパース失敗")
        print(text)
        return "{}"