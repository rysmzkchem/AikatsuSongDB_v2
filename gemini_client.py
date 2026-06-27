from google import genai
from google.genai import types
from pathlib import Path
import json
import traceback

from config import API_KEY, MODEL_NAME

# =========================
# クライアント初期化
# =========================
client = genai.Client(api_key=API_KEY)

# プロンプト
PROMPT_PATH = Path("prompts/song_prompt.txt")


def get_song_info(title: str) -> str:
    try:
        prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
        prompt = prompt_template.format(title=title)

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0
            )
        )

        # -------------------------
        # 応答チェック
        # -------------------------
        if not response or not response.text:
            print("[ERROR] Gemini response empty")
            return "{}"

        text = response.text.strip()

        # -------------------------
        # JSON整形
        # -------------------------
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

        # -------------------------
        # JSONパース
        # -------------------------
        try:
            data = json.loads(text)
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