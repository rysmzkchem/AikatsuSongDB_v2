import os
import json
import re
import traceback
from pathlib import Path

from google import genai
from google.genai import types


# =========================
# API設定
# =========================
API_KEY = os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-1.5-flash")

if not API_KEY:
    raise ValueError("API_KEY is missing. Streamlit Cloud の Secrets に API_KEY を設定してください。")

client = genai.Client(api_key=API_KEY)

PROMPT_PATH = Path("prompts/song_prompt.txt")


# =========================
# JSON抽出
# =========================
def extract_json(text: str) -> str:
    if not text:
        return "{}"

    text = text.strip()
    text = text.replace("```json", "")
    text = text.replace("```", "")
    text = text.strip()

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)

    return text


# =========================
# Gemini検索
# =========================
def get_song_info(title: str) -> str:
    try:
        prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
        prompt = prompt_template.format(title=title)

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json"
            )
        )

        if not response or not response.text:
            print("[ERROR] Gemini response empty")
            return "{}"

        text = extract_json(response.text)

        try:
            data = json.loads(text)
            print("[GEMINI OK]", title, data)
            return json.dumps(data, ensure_ascii=False)

        except Exception:
            print("[ERROR] JSON parse failed")
            print(text)
            return "{}"

    except Exception as e:
        print("[FATAL ERROR] Gemini API failure")
        print(str(e))
        traceback.print_exc()
        return "{}"