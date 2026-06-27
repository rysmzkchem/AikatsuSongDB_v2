# config.py
import os
from google import genai
from google.genai import types
from pathlib import Path
import json
import traceback

# =========================
# APIキー取得（Cloud対応）
# =========================
API_KEY = os.getenv("API_KEY")

if not API_KEY:
    raise ValueError("API_KEY is missing. Set Streamlit Secrets or env var.")

client = genai.Client(api_key=API_KEY)

PROMPT_PATH = Path("prompts/song_prompt.txt")


def get_song_info(title: str) -> str:
    try:
        prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
        prompt = prompt_template.format(title=title)

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0)
        )

        if not response or not response.text:
            return "{}"

        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()

        try:
            data = json.loads(text)
            return json.dumps(data, ensure_ascii=False)
        except Exception:
            print("[JSON ERROR]", text)
            return "{}"

    except Exception as e:
        print("[Gemini ERROR]", str(e))
        traceback.print_exc()
        return "{}"