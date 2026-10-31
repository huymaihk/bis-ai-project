import sys
from pathlib import Path

# Thêm đường dẫn project root
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from agent_translator import AgentTranslator

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python run_translator.py <input_img_path> <output_img_path>")
        sys.exit(1)

    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    translator = AgentTranslator(PROJECT_DIR)
    out = translator.translate_image_keep_form(src, dst)
    print(f"TRANSLATED_IMAGE_PATH: {out}")
