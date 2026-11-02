import os
import sys
from pathlib import Path

PROJECT_DIR = Path(r"G:\My Drive\BIS_AI_PROJECT")
sys.path.insert(0, str(PROJECT_DIR))
import config

print("Testing Gemini API Key:", config.GEMINI_API_KEY[:10] + "...")

try:
    import google.generativeai as genai
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    resp = model.generate_content("Xin chào, phản hồi 1 câu ngắn: Hệ thống BIS Textile AI đã sẵn sàng.")
    print("SUCCESS: Gemini Response:", resp.text.strip())
except Exception as e:
    print("FAILED:", type(e), e)

