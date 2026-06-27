# config.py
import os

API_KEY = os.getenv("API_KEY")

MODEL_NAME = "gemini-2.5-flash"

CACHE_PATH = "data/cache.json"
OUTPUT_CSV = "data/output.csv"
ERROR_CSV = "data/error.csv"