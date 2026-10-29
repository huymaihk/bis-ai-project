import sys
import os
from pathlib import Path
import runpy

ROOT_DIR = Path(__file__).parent.resolve()
BIS_DIR = ROOT_DIR / "BIS_AI_PROJECT"

if BIS_DIR.exists():
    sys.path.insert(0, str(BIS_DIR))
    os.chdir(str(BIS_DIR))
    runpy.run_path(str(BIS_DIR / "app_ui.py"), run_name="__main__")
else:
    raise FileNotFoundError("Thư mục BIS_AI_PROJECT không tồn tại!")
