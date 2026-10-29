"""
BIS Textile AI - Full System Diagnostic & Health Check
"""
import os
import sys
import json
import time
from pathlib import Path

PROJECT_DIR = Path(r"G:\My Drive\BIS_AI_PROJECT")
sys.path.insert(0, str(PROJECT_DIR))

results = []

def log_test(module, name, passed, details=""):
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {module} -> {name}: {details}")
    results.append({"module": module, "name": name, "passed": passed, "details": details})

print("=" * 65)
print("  🚀 BẮT ĐẦU KIỂM TRA TOÀN DIỆN HỆ THỐNG MULTI-AGENT (FULL SYSTEM TEST)")
print("=" * 65)

# 1. TEST CONFIG
try:
    import config
    has_pin = bool(config.BIS_ACCESS_PIN == "1133")
    has_model = bool(config.GEMINI_MODEL)
    log_test("Config", "BIS_ACCESS_PIN is 1133", has_pin, f"PIN={config.BIS_ACCESS_PIN}")
    log_test("Config", "Gemini Model configured", has_model, f"Model={config.GEMINI_MODEL}")
except Exception as e:
    log_test("Config", "Import config", False, str(e))

# 2. TEST LEARNING ENGINE
try:
    from learning_engine import LearningEngine
    le = LearningEngine(PROJECT_DIR)
    le.record_correction("TEST_SKU", "unit", "cái", "bộ", "Trang 99")
    ctx = le.get_context_rules_for_prompt()
    log_test("LearningEngine", "Record & retrieve few-shot rule", "TEST_SKU" in ctx, f"Rules count: {len(le.load_memory())}")
except Exception as e:
    log_test("LearningEngine", "Few-shot Engine", False, str(e))

# 3. TEST AGENT KNOWLEDGE
try:
    from agent_knowledge import AgentKnowledge
    ak = AgentKnowledge(PROJECT_DIR)
    ak.ensure_storage_structure()
    summary = ak.get_knowledge_summary()
    log_test("AgentKnowledge", "Google Drive Storage structure", ak.storage_root.exists(), f"Storage at: {ak.storage_root}")
except Exception as e:
    log_test("AgentKnowledge", "Storage structure", False, str(e))

# 4. TEST AGENT MEDIA (PILLOW IMAGE PROCESSING)
try:
    from agent_media import AgentMedia
    from PIL import Image
    am = AgentMedia(PROJECT_DIR)
    # Test generating a dummy product mockup
    dummy = Image.new("RGBA", (200, 200), (255, 0, 0, 255))
    dummy_path = PROJECT_DIR / "dummy_test_prod.png"
    dummy.save(dummy_path)
    mockup_res = am.process_product_image("TEST_SKU_MEDIA", [dummy_path])
    if dummy_path.exists():
        dummy_path.unlink()
    has_mockup = bool(mockup_res.get("composite_path"))
    log_test("AgentMedia", "Pillow Mockup Compositing Engine", has_mockup, f"Status={mockup_res.get('status')}")
except Exception as e:
    log_test("AgentMedia", "Pillow Compositing", False, str(e))

# 5. TEST AGENT TECHNICAL (PYMUPDF & CATALOGUE INTEGRITY)
try:
    import fitz  # PyMuPDF
    pdf_path = PROJECT_DIR / "catalogue_sample.pdf"
    has_pdf = pdf_path.exists()
    page_count = 0
    if has_pdf:
        doc = fitz.open(str(pdf_path))
        page_count = len(doc)
        doc.close()
    log_test("AgentTechnical", "PyMuPDF & Catalogue integrity", page_count > 0, f"Pages={page_count}")
except Exception as e:
    log_test("AgentTechnical", "PyMuPDF Parser", False, str(e))

# 6. TEST HARAVAN API CONNECTION
try:
    import requests
    haravan_token = config.HARAVAN_TOKEN
    headers = {
        "Authorization": f"Bearer {haravan_token}",
        "Content-Type": "application/json"
    }
    # Test read-only products count or shop endpoint
    resp = requests.get("https://apis.haravan.com/com/products/count.json", headers=headers, timeout=10)
    log_test("HaravanGuard", "Haravan API Token Auth", resp.status_code == 200, f"Status: {resp.status_code}, Resp: {resp.text[:60]}")
except Exception as e:
    log_test("HaravanGuard", "Haravan Connection", False, str(e))

# 7. TEST GOOGLE SHEETS CONNECTION & LOCAL CACHE RESILIENCE
try:
    from agent_operations import AgentOperations
    ao = AgentOperations(PROJECT_DIR)
    ss, ws = ao.connect_sheets()
    if ws is not None:
        log_test("AgentOperations", "Google Sheets Master Sync", True, f"Online at: {ss.url}")
    else:
        # Fallback to local cache verification
        cache_file = PROJECT_DIR / "extracted_products_cache.json"
        has_cache = cache_file.exists()
        log_test("AgentOperations", "Cache Resilience (Offline Safe Mode)", has_cache, f"Local Cache Protected (Items: {len(json.load(open(cache_file, encoding='utf-8')))} SP)")
except Exception as e:
    log_test("AgentOperations", "Data Storage", False, str(e))

# 8. TEST AGENT LEADER ORCHESTRATOR
try:
    from agent_leader import AgentLeader
    leader = AgentLeader(PROJECT_DIR)
    depts = [k for k, v in leader.departments.items() if v is not None]
    log_test("AgentLeader", "Register 5 Departments", len(depts) >= 5, f"Active depts: {depts}")
except Exception as e:
    log_test("AgentLeader", "Orchestrator Registry", False, str(e))

# 9. TEST STREAMLIT APP_UI COMPATIBILITY
try:
    import py_compile
    py_compile.compile(str(PROJECT_DIR / "app_ui.py"), doraise=True)
    log_test("AppUI", "Streamlit UI Compilation", True, "Syntax 100% Valid")
except Exception as e:
    log_test("AppUI", "Streamlit UI Compilation", False, str(e))

print("=" * 65)
passed_cnt = sum(1 for r in results if r["passed"])
failed_cnt = sum(1 for r in results if not r["passed"])
print(f"  🏁 TỔNG KẾT: {passed_cnt}/{len(results)} KIỂM TRA ĐẠT ({failed_cnt} LỖI CẦN FIX)")
print("=" * 65)
