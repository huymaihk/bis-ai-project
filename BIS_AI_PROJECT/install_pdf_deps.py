"""
BIS Textile Pipeline - PyMuPDF installer helper
Run this first if pdf_to_images() falls back to direct upload.
"""
import subprocess, sys

packages = ["pymupdf", "pdf2image"]

for pkg in packages:
    print(f"Installing {pkg}...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", pkg],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"  ✓ {pkg} installed")
    else:
        print(f"  ⚠ {pkg} failed: {result.stderr[:200]}")

