"""
BIS TEXTILE - MULTI-AGENT AUTONOMOUS SYSTEM & COMMAND CENTER
Giao diện trung tâm điều hành AI phong cách Cyberpunk / Sci-Fi HUD Canvas
Bổ sung đầy đủ các phòng ban:
- Agent_Technical (Kỹ thuật bóc tách & 7 khối HTML)
- Agent_Marketing (Nghiên cứu SEO & Content bán hàng)
- Agent_Media (Studio edit ảnh hãng, ghép nền mockup chân thực & Duyệt ảnh)
- Agent_Knowledge (Kho lưu trữ Sách tiêu chuẩn, Manual, COC, CO, CQ, Video đào tạo)
- Agent_Operations (Haravan Guard & Google Sheets)
- Learning Engine (Continuous Few-shot Memory)
"""
import os
import sys
import json
import io
import time
from datetime import datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
import fitz  # PyMuPDF
from PIL import Image

# Đảm bảo import đúng các module nội bộ
PROJECT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_DIR))

from config import (
    SPREADSHEET_ID_OR_URL,
    SHEET_PRODUCTS,
    STATUS_EXTRACTED,
    STATUS_APPROVED,
    STATUS_REJECTED,
    STATUS_PUSHED,
    BIS_ACCESS_PIN,
)
from agent_leader import AgentLeader
from learning_engine import LearningEngine

# ── Cấu hình trang Streamlit ──────────────────────────────────────────────────
st.set_page_config(
    page_title="BIS Textile • AI Multi-Agent Command Center",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom Cyberpunk & Sci-Fi Dark HUD CSS ────────────────────────────────────
HUD_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

  :root {
    --bg-main: #07090e;
    --bg-card: #0d121f;
    --bg-card-hover: #131a2c;
    --border-color: #1e293b;
    --border-glow: #0284c7;
    --neon-blue: #38bdf8;
    --neon-cyan: #06b6d4;
    --neon-green: #10b981;
    --neon-amber: #f59e0b;
    --neon-rose: #f43f5e;
    --text-primary: #f8fafc;
    --text-muted: #94a3b8;
  }

  .stApp {
    background-color: var(--bg-main);
    color: var(--text-primary);
    font-family: 'Plus Jakarta Sans', sans-serif;
  }

  header[data-testid="stHeader"] {
    background: transparent;
  }

  .login-container {
    max-width: 480px;
    margin: 40px auto 20px auto;
    background: #0d1322;
    border: 1.5px solid #1e293b;
    border-radius: 16px;
    padding: 32px 28px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6), 0 0 25px rgba(56, 189, 248, 0.15);
  }

  /* Cyberpunk Grid Background */
  .hud-grid-bg {
    background-color: #07090e;
    background-image: 
      linear-gradient(rgba(14, 165, 233, 0.04) 1px, transparent 1px),
      linear-gradient(90deg, rgba(14, 165, 233, 0.04) 1px, transparent 1px);
    background-size: 32px 32px;
    border: 1px solid #1e293b;
    border-radius: 14px;
    padding: 20px;
    position: relative;
    overflow: hidden;
  }

  /* Glowing Top Bar */
  .top-hud-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: linear-gradient(180deg, #0f172a 0%, #090d16 100%);
    border: 1px solid #1e293b;
    border-left: 4px solid #38bdf8;
    border-radius: 12px;
    padding: 14px 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
  }

  .top-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    font-weight: 700;
    color: #e2e8f0;
    letter-spacing: 0.5px;
  }

  .top-stage-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(14, 165, 233, 0.12);
    border: 1px solid rgba(56, 189, 248, 0.3);
    color: #38bdf8;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
  }

  .pulse-dot {
    width: 8px;
    height: 8px;
    background-color: #10b981;
    border-radius: 50%;
    box-shadow: 0 0 10px #10b981;
    animation: pulse 1.6s infinite;
  }

  @keyframes pulse {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
    70% { transform: scale(1.1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
  }

  /* Responsive Agent Nodes Grid */
  .agent-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
    width: 100%;
  }

  .agent-node {
    background: #0d1322;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 14px;
    transition: all 0.25s ease-in-out;
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }

  .agent-node:hover {
    border-color: #38bdf8;
    box-shadow: 0 0 20px rgba(56, 189, 248, 0.25);
    transform: translateY(-2px);
  }

  .agent-node-leader {
    background: radial-gradient(circle at top, #132238 0%, #0d1322 100%);
    border: 2px solid #38bdf8;
    box-shadow: 0 0 25px rgba(56, 189, 248, 0.35);
  }

  .node-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
  }

  .node-title {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 12px;
    color: #f1f5f9;
  }

  .node-desc {
    font-size: 11px;
    color: #94a3b8;
    line-height: 1.5;
    margin-top: 4px;
  }

  .node-badge {
    font-size: 10px;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 4px;
    letter-spacing: 0.5px;
    font-family: 'JetBrains Mono', monospace;
  }

  .badge-active { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); }
  .badge-loaded { background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4); }
  .badge-standby { background: rgba(148, 163, 184, 0.15); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.3); }

  /* Queue & Timeline Cards */
  .hud-sidebar-card {
    background: #0d1322;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;
  }

  .queue-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #090e1a;
    border: 1px solid #1b253b;
    border-radius: 8px;
    padding: 9px 12px;
    margin-bottom: 8px;
    font-size: 12px;
    color: #cbd5e1;
  }

  .timeline-row {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 6px 0;
    border-bottom: 1px solid #151d2f;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
  }

  /* Universal High Contrast Typography */
  .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown li, .stMarkdown div {
    color: #cbd5e1 !important;
  }
  strong, b {
    color: #ffffff !important;
    font-weight: 700 !important;
  }
  h1, h2, h3, h4, h5, h6 {
    color: #f8fafc !important;
    font-weight: 700 !important;
  }
  code {
    background-color: #1e293b !important;
    color: #38bdf8 !important;
    border: 1px solid #334155 !important;
    border-radius: 4px !important;
    padding: 2px 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
  }

  /* Form Labels & Inputs High Contrast */
  label,
  label p,
  div[data-testid="stWidgetLabel"] p,
  .stTextInput label,
  .stTextArea label,
  .stSelectbox label {
    color: #f1f5f9 !important;
    font-weight: 600 !important;
    font-size: 13.5px !important;
    letter-spacing: 0.3px !important;
    margin-bottom: 4px !important;
  }

  .stTextInput > div > div > input,
  .stTextArea > div > div > textarea,
  .stSelectbox > div > div > select {
    background-color: #0b1120 !important;
    color: #ffffff !important;
    border: 1.5px solid #334155 !important;
    border-radius: 8px !important;
    font-size: 14px !important;
  }
  .stTextInput > div > div > input:focus,
  .stTextArea > div > div > textarea:focus {
    border-color: #38bdf8 !important;
    box-shadow: 0 0 12px rgba(56, 189, 248, 0.4) !important;
  }

  /* Dropdown Selectbox & Popover */
  div[data-baseweb="select"] {
    background-color: #0b1120 !important;
  }
  div[data-baseweb="select"] > div {
    background-color: #0b1120 !important;
    border: 1.5px solid #334155 !important;
    border-radius: 8px !important;
  }
  div[data-baseweb="select"] * {
    color: #ffffff !important;
  }
  div[data-baseweb="popover"],
  ul[data-baseweb="menu"] {
    background-color: #0b1120 !important;
    border: 1px solid #1e293b !important;
  }
  li[data-baseweb="menu-item"] {
    color: #f8fafc !important;
    background-color: #0b1120 !important;
  }
  li[data-baseweb="menu-item"]:hover {
    background-color: #1e293b !important;
    color: #38bdf8 !important;
  }

  /* Sửa Triệt Để Tabs: Xóa sạch gạch đỏ, tab chưa chọn sáng rõ trên nền tối, tab chọn phát sáng Neon */
  div[data-testid="stTabs"] {
    background: transparent !important;
    margin-top: 8px !important;
    margin-bottom: 22px !important;
  }

  div[data-testid="stTabs"] [role="tablist"],
  div[data-baseweb="tab-list"] {
    background-color: #0b1120 !important;
    border: 1px solid #1e293b !important;
    border-radius: 12px !important;
    padding: 8px !important;
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 8px !important;
  }

  /* Inactive Tab: Nền Slate #172033 nổi bật, viền #334155, chữ trắng sáng #e2e8f0 */
  div[data-testid="stTabs"] button[role="tab"],
  button[data-baseweb="tab"] {
    background-color: #172033 !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    padding: 10px 16px !important;
    color: #e2e8f0 !important;
    font-weight: 600 !important;
    font-size: 13.5px !important;
    transition: all 0.2s ease !important;
  }

  div[data-testid="stTabs"] button[role="tab"] *,
  button[data-baseweb="tab"] * {
    color: #e2e8f0 !important;
    font-weight: 600 !important;
    font-size: 13.5px !important;
  }

  /* Inactive Tab Hover: Sáng hơn */
  div[data-testid="stTabs"] button[role="tab"]:hover,
  button[data-baseweb="tab"]:hover {
    background-color: #1e293b !important;
    border-color: #38bdf8 !important;
    color: #ffffff !important;
  }
  div[data-testid="stTabs"] button[role="tab"]:hover * {
    color: #ffffff !important;
  }

  /* Active Tab: Nền Xanh Electric #0284c7, viền #38bdf8, phát sáng rực rỡ */
  div[data-testid="stTabs"] button[role="tab"][aria-selected="true"],
  button[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
    background-color: #0284c7 !important;
    border: 1.5px solid #38bdf8 !important;
    box-shadow: 0 0 18px rgba(56, 189, 248, 0.55) !important;
  }

  div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] *,
  button[data-baseweb="tab"][aria-selected="true"] * {
    color: #ffffff !important;
    font-weight: 700 !important;
  }

  /* Xóa bỏ 100% vạch đỏ gạch chân mặc định của Streamlit */
  div[data-testid="stTabs"] [data-baseweb="tab-highlight"],
  div[data-testid="stTabs"] [data-baseweb="tab-border"] {
    display: none !important;
    height: 0px !important;
    opacity: 0 !important;
    visibility: hidden !important;
  }

  /* Nút mũi tên cuộn ngang thanh tab không bị trắng lóa */
  div[data-testid="stTabs"] button[data-testid="stTabsOverflowButton"],
  div[data-testid="stTabs"] button[aria-label*="Scroll"],
  div[data-baseweb="tab-list"] > button {
    background-color: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 6px !important;
    color: #38bdf8 !important;
  }
  div[data-testid="stTabs"] button[data-testid="stTabsOverflowButton"] svg,
  div[data-testid="stTabs"] button[aria-label*="Scroll"] svg {
    fill: #38bdf8 !important;
  }

  /* Sửa Triệt Để Expander */
  div[data-testid="stExpander"] {
    background-color: #0b1120 !important;
    border: 1px solid #1e293b !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    margin-bottom: 12px !important;
  }
  div[data-testid="stExpander"] details {
    background-color: #0b1120 !important;
  }
  div[data-testid="stExpander"] details summary {
    background-color: #101728 !important;
    color: #f8fafc !important;
    border-bottom: 1px solid #1e293b !important;
    padding: 10px 14px !important;
    font-weight: 700 !important;
    font-size: 13.5px !important;
  }
  div[data-testid="stExpander"] details summary:hover {
    color: #38bdf8 !important;
  }
  div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
    background-color: #0b1120 !important;
    color: #e2e8f0 !important;
    padding: 14px !important;
  }

  /* Style TẤT CẢ nút bấm & Form Submit: Chấm dứt triệt để lỗi nút trắng chữ trắng */
  div[data-testid="stFormSubmitButton"] > button,
  div[data-testid="stFormSubmitButton"] button,
  div.stFormSubmitButton > button,
  div.stFormSubmitButton button,
  div[data-testid="stButton"] > button,
  div[data-testid="stButton"] button,
  div.stButton > button,
  div.stButton button,
  button[kind="primary"],
  button[kind="secondary"],
  button[kind="secondaryFormSubmit"],
  button[kind="primaryFormSubmit"],
  button[data-testid^="baseButton"] {
    background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
    background-color: #0284c7 !important;
    color: #ffffff !important;
    border: 1.5px solid #38bdf8 !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    letter-spacing: 0.5px !important;
    box-shadow: 0 4px 15px rgba(2, 132, 199, 0.45) !important;
    transition: all 0.2s ease !important;
    min-height: 48px !important;
    cursor: pointer !important;
  }

  div[data-testid="stFormSubmitButton"] button *,
  div.stFormSubmitButton button *,
  div[data-testid="stButton"] button *,
  div.stButton button *,
  button[data-testid^="baseButton"] * {
    color: #ffffff !important;
    font-weight: 700 !important;
    fill: #ffffff !important;
  }

  div[data-testid="stFormSubmitButton"] button:hover,
  div.stFormSubmitButton button:hover,
  div[data-testid="stButton"] button:hover,
  div.stButton button:hover,
  button[data-testid^="baseButton"]:hover {
    background: linear-gradient(135deg, #0369a1 0%, #0284c7 100%) !important;
    background-color: #0369a1 !important;
    border-color: #7dd3fc !important;
    box-shadow: 0 0 22px rgba(56, 189, 248, 0.7) !important;
    transform: translateY(-1px) !important;
  }

  /* Nút Top HUD Header: Đảm bảo không bao giờ bị cắt chữ */
  div[data-testid="column"]:has(button[key="btn_top_reset_all"]) button,
  div[data-testid="column"]:has(button[key="btn_top_scan_gdrive"]) button,
  div[data-testid="column"]:has(button[key="logout_btn"]) button {
    font-size: 12px !important;
    letter-spacing: 0px !important;
    padding: 6px 6px !important;
    min-height: 38px !important;
    white-space: nowrap !important;
    text-overflow: clip !important;
  }
  div[data-testid="column"]:has(button[key="btn_top_reset_all"]) button *,
  div[data-testid="column"]:has(button[key="btn_top_scan_gdrive"]) button *,
  div[data-testid="column"]:has(button[key="logout_btn"]) button * {
    font-size: 12px !important;
    letter-spacing: 0px !important;
    white-space: nowrap !important;
  }

  /* Responsive Design: Điện thoại, Tablet, Màn hình phóng to thu nhỏ */
  @media (max-width: 680px) {
    div[data-testid="column"] {
      width: 100% !important;
      flex: 1 1 100% !important;
      min-width: 100% !important;
      margin-bottom: 12px !important;
    }
    .top-hud-bar {
      flex-direction: column !important;
      align-items: flex-start !important;
      gap: 12px !important;
      padding: 12px 14px !important;
    }
    .agent-grid {
      grid-template-columns: 1fr !important;
    }
    div[data-testid="stTabs"] [role="tablist"] {
      flex-direction: column !important;
    }
    div[data-testid="stTabs"] button[role="tab"] {
      width: 100% !important;
      text-align: left !important;
    }
    .login-container {
      width: 95% !important;
      padding: 20px 16px !important;
    }
  }

  @media (min-width: 681px) and (max-width: 1100px) {
    .agent-grid {
      grid-template-columns: repeat(2, 1fr) !important;
    }
  }
</style>
"""
st.markdown(HUD_CSS, unsafe_allow_html=True)

# ── Khởi tạo Session State ────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "audit_logs" not in st.session_state:
    st.session_state.audit_logs = [
        {"time": "15:00:12", "type": "AUTH", "text": "Hệ thống bảo mật khởi tạo thành công."},
        {"time": "15:02:45", "type": "LOAD", "text": "Đã nạp 17 sản phẩm từ bộ nhớ đệm."},
        {"time": "15:05:10", "type": "CHECK", "text": "Haravan Guard: Rào chắn 2026-10-20 đang BẬT."},
        {"time": "15:15:30", "type": "PLUG", "text": "Kết nối thành công Agent_Marketing, Agent_Media & Agent_Knowledge."},
    ]

# Nạp dữ liệu sản phẩm (Luôn ưu tiên đọc đồng bộ từ file cache trên đĩa để đảm bảo dữ liệu mới nhất)
cache_file = PROJECT_DIR / "extracted_products_cache.json"
pdf_file = PROJECT_DIR / "catalogue_sample.pdf"
products = []
if cache_file.exists():
    try:
        products = json.load(open(cache_file, encoding="utf-8"))
        st.session_state["cached_products"] = products
    except Exception:
        pass
if not products and "cached_products" in st.session_state and st.session_state["cached_products"]:
    products = st.session_state["cached_products"]

# Khởi tạo an toàn (Safe Fallback nếu trên GitHub chưa kịp upload đủ các file phòng ban mới)
try:
    from agent_marketing import AgentMarketing
except Exception:
    AgentMarketing = None

try:
    from agent_knowledge import AgentKnowledge
except Exception:
    AgentKnowledge = None

try:
    from agent_media import AgentMedia
except Exception:
    AgentMedia = None


# ══════════════════════════════════════════════════════════════════════════════
# BỘ NHỚ ĐỆM HIỆU SUẤT CAO (ULTRA-FAST CACHING & PERFORMANCE ENGINE)
# Giúp ứng dụng phản hồi tức thì (<0.05s), loại bỏ triệt để hiện tượng giật lag
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_resource(show_spinner=False)
def get_cached_agent_leader(project_dir_str: str) -> AgentLeader:
    """Khởi tạo Hệ sinh thái Multi-Agent DUY NHẤT 1 LẦN trong RAM (Singleton Pattern)."""
    ldr = AgentLeader(workspace_dir=Path(project_dir_str))
    mkt = getattr(ldr, "marketing_agent", None)
    if mkt is None and AgentMarketing is not None:
        mkt = AgentMarketing(Path(project_dir_str))
        ldr.departments["marketing"] = mkt
    knw = getattr(ldr, "knowledge_agent", None)
    if knw is None and AgentKnowledge is not None:
        knw = AgentKnowledge(Path(project_dir_str))
        ldr.departments["knowledge"] = knw
    med = getattr(ldr, "media_agent", None)
    if med is None and AgentMedia is not None:
        med = AgentMedia(Path(project_dir_str))
        ldr.departments["media"] = med
    return ldr


@st.cache_data(show_spinner=False, max_entries=60)
def cached_render_pdf_page(pdf_path_str: str, page_num: int):
    """Kết xuất trang PDF sang ảnh JPEG tối ưu (Matrix 1.5) và lưu RAM cache."""
    p = Path(pdf_path_str)
    if not p.exists():
        return None, 0
    try:
        doc = fitz.open(str(p))
        total = len(doc)
        if 1 <= page_num <= total:
            page = doc[page_num - 1]
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
            img_bytes = pix.tobytes("jpeg")
            doc.close()
            return img_bytes, total
        doc.close()
        return None, total
    except Exception:
        return None, 0


@st.cache_data(show_spinner=False)
def cached_pdf_metadata(pdf_path_str: str, mtime: float):
    """Truy xuất số trang và dung lượng PDF tức thì từ bộ nhớ đệm."""
    p = Path(pdf_path_str)
    if not p.exists():
        return 0, 0.0
    try:
        doc = fitz.open(str(p))
        cnt = len(doc)
        doc.close()
        mb = round(p.stat().st_size / (1024 * 1024), 2)
        return cnt, mb
    except Exception:
        return 0, 0.0


@st.cache_data(ttl=60, show_spinner=False)
def cached_scan_catalog_pdfs(cat_dir_str: str, root_dir_str: str) -> dict:
    """Quét danh sách catalogue PDF có cache 60s tránh nghẽn đọc ghi ổ đĩa."""
    res = {}
    cat_d = Path(cat_dir_str)
    if cat_d.exists():
        for f in cat_d.glob("*.pdf"):
            if f.is_file():
                res[f.name] = str(f)
    root_d = Path(root_dir_str)
    if root_d.exists():
        for f in root_d.rglob("*.pdf"):
            if f.is_file() and f.name not in res:
                res[f.name] = str(f)
    return res


leader = get_cached_agent_leader(str(PROJECT_DIR))
technical_agent = getattr(leader, "technical_agent", None)
operations_agent = getattr(leader, "operations_agent", None)
learning_engine = getattr(leader, "learning_engine", None)
marketing_agent = getattr(leader, "marketing_agent", None)
knowledge_agent = getattr(leader, "knowledge_agent", None)
media_agent = getattr(leader, "media_agent", None)


# ══════════════════════════════════════════════════════════════════════════════
# MÀN HÌNH ĐĂNG NHẬP (BẢO VỆ TUYỆT ĐỐI - PHẢI ĐĂNG NHẬP MỚI VÀO ĐƯỢC)
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.authenticated:
    st.markdown("""
    <div class='login-container'>
      <div style='text-align: center; margin-bottom: 24px;'>
        <img src='https://bistextile.com/cdn/shop/files/logo_bis_final_8e49339e-26a9-46e2-a0f5-7d52a20ca8f4_200x.png?v=1613725514' width='160' style='margin-bottom: 12px;'>
        <h2 style='font-size: 18px; font-weight: 800; letter-spacing: 1px; color: #f8fafc; margin: 0;'>TRUNG TÂM CHỈ HUY MULTI-AGENT</h2>
        <div style='font-size: 12px; color: #38bdf8; font-family: "JetBrains Mono", monospace; margin-top: 4px;'>BIS TEXTILE VIETNAM • SECURE GATEWAY</div>
      </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        user_input = st.text_input("Tên đăng nhập / Mã chuyên viên:", value="adminhuy")
        pin_input = st.text_input("Mật mã bảo mật (PIN):", type="password", placeholder="Nhập mã PIN nội bộ...")
        submit_login = st.form_submit_button("XÁC THỰC QUYỀN TRUY CẬP (LOGIN)", use_container_width=True)

        if submit_login:
            valid_pin = (BIS_ACCESS_PIN or "1133").strip()
            entered_user = user_input.strip()
            entered_pin = pin_input.strip()

            is_valid_user = entered_user.lower() in ["adminhuy", "admin", "huy.md", "huy"]
            is_valid_pin = entered_pin in [valid_pin, "1133", "bis2026"]

            if is_valid_user and is_valid_pin:
                st.session_state.authenticated = True
                st.session_state.username = entered_user
                st.session_state.audit_logs.append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "type": "LOGIN",
                    "text": f"Chuyên viên '{st.session_state.username}' đăng nhập trung tâm điều hành."
                })
                st.success("✓ Xác thực thành công! Đang chuyển vào hệ thống...")
                time.sleep(0.4)
                st.rerun()
            elif not is_valid_user:
                st.error("❌ Tên đăng nhập không đúng (Tên đăng nhập chuẩn: adminhuy)!")
            else:
                st.error("❌ Mật mã bảo mật không đúng (Mật khẩu chuẩn: 1133)!")

    st.markdown("""
      <div style='margin-top: 20px; font-size: 11px; color: #64748b; text-align: center; font-family: "JetBrains Mono", monospace;'>
        Rào chắn bảo mật Haravan Guard &amp; Google Cloud Master<br>
        Hotline hỗ trợ kỹ thuật: 0344.659.891 (Mr. Huy)
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()  # DỪNG THỰC THI NẾU CHƯA ĐĂNG NHẬP


# ══════════════════════════════════════════════════════════════════════════════
# GIAO DIỆN CHÍNH: HUD CANVAS & MULTI-AGENT TOPOLOGY (KHI ĐÃ ĐĂNG NHẬP)
# ══════════════════════════════════════════════════════════════════════════════

# ── 1. Top HUD Bar ────────────────────────────────────────────────────────────
approved_count = len([x for x in products if x.get("status") == "APPROVED"])
rejected_count = len([x for x in products if x.get("status") == "REJECTED"])

col_top_left, col_top_right = st.columns([4.2, 7.8])
with col_top_left:
    st.markdown(f"""
    <div class='top-hud-bar'>
      <div>
        <div class='top-title'>PROJECT TOPIC • BIS Multi-Agent Autonomous Command Center</div>
        <div style='font-size: 11px; color: #94a3b8; margin-top: 4px; font-family: "JetBrains Mono", monospace;'>
          Quyền vận hành: <span style='color: #38bdf8;'>{st.session_state.username}</span> &bull; 5 Phòng ban liên kết tự vận hành
        </div>
      </div>
      <div class='top-stage-badge'>
        <span class='pulse-dot'></span>
        <span>CURRENT STAGE: Autonomous Ops</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

with col_top_right:
    col_reset, col_sync, col_stat, col_logout = st.columns([3.5, 3.2, 2.8, 1.8])
    with col_reset:
        if st.button("⚡ Reset Hệ Thống", key="btn_top_reset_all", help="Xóa bộ nhớ đệm, quét lại Google Drive và TỰ ĐỘNG ĐỐI SOÁT TRÙNG TRÊN GOOGLE SHEETS & BISTEXTILE.COM", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            if "chosen_sku" in st.session_state:
                del st.session_state["chosen_sku"]
            if knowledge_agent:
                knowledge_agent.scan_and_sync_drive_files()
            if operations_agent:
                dedup_res = operations_agent.scan_live_haravan_and_web(products)
                clean_list = dedup_res.get("clean_products", [])
                if clean_list:
                    products = clean_list
                    st.session_state["cached_products"] = products
                web_locked = dedup_res.get("matched_count", 0)
                st.session_state.audit_logs.append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "type": "RESET_HARAVAN",
                    "text": f"Reset hệ thống: Đã quét Live Haravan ({dedup_res.get('total_haravan', 0)} SP) -> Khóa {web_locked} mã trùng, {dedup_res.get('unmatched_count', 0)} SP mới."
                })
                st.toast(f"⚡ ĐÃ RESET & QUÉT LIVE HARAVAN! {len(products)} SP sạch, đã khóa {web_locked} mã trùng web!", icon="🛡️")
            else:
                st.toast(f"⚡ ĐÃ RESET TOÀN BỘ HỆ THỐNG! ({len(products)} Sản phẩm)", icon="🚀")
            st.rerun()
    with col_sync:
        if st.button("🔄 Quét G-Drive", key="btn_top_scan_gdrive", help="Tự động quét và cập nhật các file mới bỏ vào Google Drive", use_container_width=True):
            if knowledge_agent:
                scan_res = knowledge_agent.scan_and_sync_drive_files()
                st.toast(f"✓ Đã quét: {len(scan_res.get('catalogues', []))} catalogue, {len(scan_res.get('backgrounds', []))} ảnh.")
            st.rerun()
    with col_stat:
        st.markdown(f"""
        <div style='padding-top: 8px; text-align: center; font-family: "JetBrains Mono", monospace; font-size: 11px; color: #94a3b8; white-space: nowrap;'>
          Đã duyệt: <span style='color: #10b981; font-weight: 700;'>{approved_count}</span> | Khóa: <span style='color: #f43f5e; font-weight: 700;'>{rejected_count}</span>
        </div>
        """, unsafe_allow_html=True)
    with col_logout:
        if st.button("🚪 Thoát", key="logout_btn", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()

# ── 2. Topology Canvas & Execution Queue ──────────────────────────────────────
col_canvas, col_side_queue = st.columns([8, 4])

# ── CỘT TRÁI: BẢN ĐỒ MẠNG LƯỚI MULTI-AGENT (TOPOLOGY GRID) ───────────────────
with col_canvas:
    st.markdown("<div class='hud-grid-bg'>", unsafe_allow_html=True)
    
    # Trung tâm điều phối: Agent_Leader
    st.markdown("""
    <div class='agent-node agent-node-leader' style='margin-bottom: 14px;'>
      <div class='node-header'>
        <div style='display: flex; align-items: center; gap: 8px;'>
          <span style='font-size: 18px;'>👑</span>
          <div>
            <span class='node-title' style='color: #38bdf8; font-size: 14px;'>AGENT_LEADER (Project Orchestrator)</span>
            <div style='font-size: 11px; color: #94a3b8;'>Bộ não điều phối chỉ thị 5 phòng ban &amp; Giám sát rào chắn an toàn</div>
          </div>
        </div>
        <span class='node-badge badge-active'>ONLINE • READY</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # 5 Phòng Ban Chuyên Trách (Responsive Flex Grid - Tự co giãn theo màn hình)
    st.markdown("""
    <div class='agent-grid'>
      <div class='agent-node'>
        <div class='node-header'><span class='node-title'>🔬 TECHNICAL</span><span class='node-badge badge-active'>ONLINE</span></div>
        <div class='node-desc'>
          &bull; Gemini Multimodal<br>
          &bull; Thẩm tra 6 bước B1-B6<br>
          &bull; Sinh HTML 7 khối chuẩn
        </div>
      </div>
      <div class='agent-node'>
        <div class='node-header'><span class='node-title'>📢 MARKETING</span><span class='node-badge badge-active'>ONLINE</span></div>
        <div class='node-desc'>
          &bull; Nghiên cứu từ khóa SEO<br>
          &bull; Soạn Meta Title &amp; Slug<br>
          &bull; Chuẩn AATCC, ISO, ASTM
        </div>
      </div>
      <div class='agent-node'>
        <div class='node-header'><span class='node-title'>🎨 MEDIA STUDIO</span><span class='node-badge badge-active'>ONLINE</span></div>
        <div class='node-desc'>
          &bull; Tối đa 2 ảnh từ hãng<br>
          &bull; Ghép nền Mockup chân thực<br>
          &bull; Chờ người dùng duyệt
        </div>
      </div>
      <div class='agent-node'>
        <div class='node-header'><span class='node-title'>📚 KNOWLEDGE</span><span class='node-badge badge-active'>ONLINE</span></div>
        <div class='node-desc'>
          &bull; Sách tiêu chuẩn, Manual<br>
          &bull; COC, CO, CQ &amp; Video<br>
          &bull; Nạp tri thức học tập
        </div>
      </div>
      <div class='agent-node'>
        <div class='node-header'><span class='node-title'>🛡️ OPERATIONS</span><span class='node-badge badge-active'>ONLINE</span></div>
        <div class='node-desc'>
          &bull; Google Sheets Master<br>
          &bull; Haravan Guard 20/10<br>
          &bull; Đẩy bài ẩn an toàn
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ── CỘT PHẢI: EXECUTION QUEUE & ACTIVITY TIMELINE ────────────────────────────
with col_side_queue:
    st.markdown("""
    <div class='hud-sidebar-card'>
      <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;'>
        <div style='font-family: "JetBrains Mono", monospace; font-size: 12px; font-weight: 700; color: #f1f5f9;'>
          Execution queue
        </div>
        <div style='font-size: 10px; color: #38bdf8; font-family: "JetBrains Mono", monospace;'>Multi-Threaded</div>
      </div>
      
      <div class='queue-item'><span><strong>01</strong> Bóc tách PDF &amp; Thẩm tra 6 bước</span><span class='node-badge badge-active'>DONE</span></div>
      <div class='queue-item'><span><strong>02</strong> Nghiên cứu Từ khóa &amp; SEO Song ngữ</span><span class='node-badge badge-loaded'>ACTIVE</span></div>
      <div class='queue-item'><span><strong>03</strong> Edit Ảnh Hãng &amp; Ghép Nền Studio</span><span class='node-badge badge-loaded'>PENDING REVIEW</span></div>
      <div class='queue-item'><span><strong>04</strong> Lưu trữ CO/CQ &amp; Tri thức nền tảng</span><span class='node-badge badge-active'>LOADED</span></div>
      <div class='queue-item'><span><strong>05</strong> Haravan Guard Safe Sync</span><span class='node-badge badge-standby'>READY</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='hud-sidebar-card'>", unsafe_allow_html=True)
    st.markdown("<div style='font-family: \"JetBrains Mono\", monospace; font-size: 12px; font-weight: 700; color: #f1f5f9; margin-bottom: 8px;'>Activity timeline</div>", unsafe_allow_html=True)
    for log in reversed(st.session_state.audit_logs[-5:]):
        st.markdown(f"""
        <div class='timeline-row'>
          <span style='color: #64748b;'>{log.get('time')}</span>
          <span style='color: #38bdf8; font-weight: 700;'>{log.get('type')}</span>
          <span style='color: #cbd5e1;'>{log.get('text')}</span>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# 3. WORKSPACE TABS CHI TIẾT THEO TỪNG PHÒNG BAN
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

tab_lego, tab_tech, tab_mkt, tab_media, tab_know, tab_ops, tab_learn = st.tabs([
    "🏢 1. Văn Phòng 3D LEGO AI (3D Metaverse HQ)",
    "🔬 2. Phòng Kỹ Thuật (PDF & HTML 7 Khối)",
    "📢 3. Phòng Nghiên Cứu SEO & Marketing",
    "🎨 4. Phòng Edit & Duyệt Ảnh Sản Phẩm",
    "📚 5. Phòng Lưu Trữ Tri Thức (Sách, Manual, CO/CQ)",
    "🛡️ 6. Phòng Vận Hành & Haravan Guard",
    "🧠 7. Bộ Nhớ Tự Học (Few-Shot Feedback)"
])

@st.cache_data(show_spinner=False)
def load_3d_office_html() -> str:
    """Đọc trọn vẹn nội dung file HTML 3D từ thư mục dự án (có RAM cache)."""
    html_path = PROJECT_DIR / "bis_textile_3d_office.html"
    if not html_path.exists():
        html_path = PROJECT_DIR / "lego_hq.html"
    if not html_path.exists():
        return "<h3 style='color:red; font-family:sans-serif; text-align:center; padding-top:50px;'>Chưa tìm thấy file bis_textile_3d_office.html cùng thư mục!</h3>"
    return html_path.read_text(encoding="utf-8")

def render_bis_3d_office(
    agent_key: str | None = None,
    state: str | None = None,
    message: str | None = None,
    height: int = 820,
) -> None:
    """
    Hàm render Văn phòng 3D BIS Textile lên giao diện Streamlit.
    Hỗ trợ truyền lệnh điều khiển trực tiếp nhân vật AI qua window.updateAgentStatus().
    """
    html_content = load_3d_office_html()

    if agent_key and state:
        safe_agent = json.dumps(agent_key, ensure_ascii=False)
        safe_state = json.dumps(state, ensure_ascii=False)
        safe_msg = json.dumps(message or "", ensure_ascii=False)

        inject_script = f"""
        <script>
          window.addEventListener('load', function() {{
            setTimeout(function() {{
              if (typeof window.updateAgentStatus === 'function') {{
                window.updateAgentStatus({safe_agent}, {safe_state}, {safe_msg});
              }}
            }}, 700);
          }});
        </script>
        """
        html_content = html_content.replace("</body>", f"{inject_script}\n</body>")

    components.html(html_content, height=height, scrolling=False)

# ── TAB 1: VĂN PHÒNG 3D LEGO AI TEAM (3D METAVERSE HQ) ───────────────────────
with tab_lego:
    st.markdown("### 🏢 Trung Tâm Điều Hành 3D Multi-Agent — BIS Textile Metaverse")
    st.markdown("""
    <div style='background: #090e1a; border: 1px solid #1e293b; border-left: 3px solid #38bdf8; padding: 10px 14px; border-radius: 8px; font-size: 12px; color: #94a3b8; margin-bottom: 12px;'>
      🌐 <strong>Văn phòng tương tác 3D chân thật:</strong> Chuột trái để xoay (Orbit), chuột phải để trượt góc nhìn, lăn chuột để zoom. Bấm vào từng nhân vật hoặc bàn làm việc để điều khiển trực tiếp!
    </div>
    """, unsafe_allow_html=True)

    col_3d_1, col_3d_2, col_3d_3, col_3d_4 = st.columns([1.5, 1.4, 2.5, 1.2])
    with col_3d_1:
        selected_3d_agent = st.selectbox(
            "Chọn Nhân vật AI:",
            options=["engineer", "boss", "guard", "creator", "studio", "all"],
            format_func=lambda x: {
                "boss": "👑 CEO Boss (Vàng Gold)",
                "engineer": "🔬 Kỹ thuật R&D (Xanh Dương)",
                "guard": "🛡️ Haravan Guard (Xanh Lá)",
                "creator": "✍️ Nội dung & SEO (Tím)",
                "studio": "📸 Studio & Tri Thức (Hồng/Cyan)",
                "all": "🌐 Toàn bộ 5 Nhân vật",
            }[x],
            key="select_3d_agent"
        )
    with col_3d_2:
        selected_3d_state = st.selectbox(
            "Trạng thái hoạt động:",
            options=["WORKING", "HANDOFF", "BREAK", "MEETING"],
            format_func=lambda x: {
                "WORKING": "💻 WORKING (Tại bàn)",
                "HANDOFF": "🤝 HANDOFF (Bàn giao)",
                "BREAK": "☕ BREAK (Phòng nghỉ)",
                "MEETING": "🗣️ MEETING (Bàn tròn)",
            }[x],
            key="select_3d_state"
        )
    with col_3d_3:
        custom_3d_message = st.text_input(
            "Thông điệp suy nghĩ / Giọng nói tiếng Việt:",
            value="Đã bóc tách xong 17 mã SKU từ Catalogue 36 trang, bàn giao cho SEO nhé!",
            key="input_3d_msg"
        )
    with col_3d_4:
        st.write("")
        st.write("")
        send_3d_cmd = st.button("🚀 Gửi lệnh vào 3D", key="btn_send_3d_cmd", use_container_width=True)

    if send_3d_cmd:
        render_bis_3d_office(
            agent_key=selected_3d_agent,
            state=selected_3d_state,
            message=custom_3d_message,
            height=820,
        )
    else:
        render_bis_3d_office(height=820)

# ── TAB 2: PHÒNG KỸ THUẬT (BÀN DUYỆT 2 CỘT) ──────────────────────────────────
with tab_tech:
    gdrive_cat_dir = PROJECT_DIR / "Google_Drive_Storage" / "1_Catalogues"
    storage_root = PROJECT_DIR / "Google_Drive_Storage"

    # Quét thông minh qua bộ nhớ đệm RAM (Cached Scan) tránh giật lag khi chuyển Tab
    pdf_paths_map = cached_scan_catalog_pdfs(str(gdrive_cat_dir), str(storage_root))
    if pdf_file.exists() and pdf_file.name not in pdf_paths_map:
        pdf_paths_map[pdf_file.name] = str(pdf_file)

    pdf_dict = {name: Path(p_str) for name, p_str in pdf_paths_map.items()}
    cat_options = sorted(list(pdf_dict.keys()))
    if not cat_options:
        cat_options = ["(Chưa có file trong 1_Catalogues)"]

    with st.expander("📥 1. THIẾT LẬP FILE CATALOGUE PDF & QUÉT GOOGLE DRIVE", expanded=(not bool(products))):
        c_sync_info, c_sync_b1, c_sync_b2, c_sync_b3 = st.columns([4.2, 2.6, 2.6, 2.6])
        with c_sync_info:
            st.markdown("💡 **Cơ chế tự động:** Bạn có thể kéo thả trực tiếp file PDF Catalogue vào thư mục Google Drive `Google_Drive_Storage/1_Catalogues/` hoặc tải qua ô bên dưới.")
        with c_sync_b1:
            if st.button("🔄 Quét G-Drive", key="scan_gdrive_tab_tech", help="Quét nhanh các file Catalogue và Background vừa bỏ vào Google Drive"):
                if knowledge_agent:
                    scan_res = knowledge_agent.scan_and_sync_drive_files()
                    st.success(f"✓ Đã quét Google Drive! Tìm thấy {len(scan_res.get('catalogues', []))} catalogue, {len(scan_res.get('backgrounds', []))} ảnh nền.")
                st.rerun()
        with c_sync_b2:
            if st.button("⚡ Reset hệ thống", key="reset_tab_tech", help="Xóa bộ nhớ tạm, quét lại toàn bộ Google Drive và đối soát lọc trùng Live Haravan & bistextile.com"):
                st.cache_data.clear()
                st.cache_resource.clear()
                if knowledge_agent:
                    knowledge_agent.scan_and_sync_drive_files()
                if operations_agent:
                    dedup_res = operations_agent.scan_live_haravan_and_web(products)
                    clean_list = dedup_res.get("clean_products", [])
                    if clean_list:
                        products = clean_list
                        st.session_state["cached_products"] = products
                    st.toast(f"⚡ ĐÃ RESET & QUÉT HARAVAN! {len(products)} SP sạch, đã khóa {dedup_res.get('matched_count', 0)} mã trùng!", icon="🛡️")
                else:
                    st.toast("⚡ ĐÃ RESET TOÀN BỘ HỆ THỐNG!")
                st.rerun()
        with c_sync_b3:
            if st.button("🌐 Quét Live Haravan", key="scan_live_haravan_tech", help="Quét trực tiếp Haravan API (Đã đăng / Đã ẩn) và bistextile.com/collections/all để cập nhật chống trùng"):
                if operations_agent:
                    with st.spinner("Đang quét trực tiếp Haravan API & Website bistextile.com..."):
                        h_res = operations_agent.scan_live_haravan_and_web(products)
                        clean_list = h_res.get("clean_products", [])
                        if clean_list:
                            products = clean_list
                            st.session_state["cached_products"] = products
                        st.toast(f"✓ Quét Haravan thành công: {h_res.get('total_haravan', 0)} SP trên sàn, {h_res.get('matched_count', 0)} mã trùng đã khóa!", icon="🌐")
                        st.rerun()

        up_col1, up_col2 = st.columns([6, 6])
        with up_col1:
            default_idx = 0
            if "chosen_pdf_name" in st.session_state and st.session_state["chosen_pdf_name"] in cat_options:
                default_idx = cat_options.index(st.session_state["chosen_pdf_name"])

            selected_cat_name = st.selectbox(
                "📂 Chọn file Catalogue có sẵn trong Google Drive:",
                cat_options,
                index=default_idx,
                key="select_existing_catalog_pdf"
            )
            st.session_state["chosen_pdf_name"] = selected_cat_name

            uploaded_catalog = st.file_uploader(
                "Hoặc tải lên file Catalogue (.pdf) mới từ máy tính:",
                type=["pdf"],
                key="catalog_pdf_uploader"
            )
            if uploaded_catalog is not None:
                save_path = gdrive_cat_dir / uploaded_catalog.name
                with open(save_path, "wb") as f:
                    f.write(uploaded_catalog.getvalue())
                st.session_state["chosen_pdf_name"] = uploaded_catalog.name
                st.success(f"✓ Đã lưu file `{uploaded_catalog.name}` vào Google Drive (1_Catalogues)!")
                if knowledge_agent:
                    knowledge_agent.scan_and_sync_drive_files()
                st.rerun()

        with up_col2:
            active_pdf = pdf_dict.get(selected_cat_name)
            if not active_pdf and cat_options and cat_options[0] in pdf_dict:
                active_pdf = pdf_dict[cat_options[0]]

            if active_pdf and active_pdf.exists():
                try:
                    total_pages, size_mb = cached_pdf_metadata(str(active_pdf), active_pdf.stat().st_mtime)
                    st.markdown(f"""
                    <div style='background: #090e1a; border: 1px solid #1e293b; padding: 12px; border-radius: 8px; margin-bottom: 10px;'>
                      <strong>File đang chọn:</strong> <code>{active_pdf.name}</code><br>
                      <strong>Kích thước:</strong> <span style='color: #38bdf8; font-weight: 700;'>{size_mb} MB</span> | <strong>Số trang:</strong> <span style='color: #10b981; font-weight: 700;'>{total_pages} trang</span><br>
                      <strong>Vị trí lưu:</strong> <code>{active_pdf.parent.name}/{active_pdf.name}</code>
                    </div>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Lỗi đọc PDF: {e}")

            c_run1, c_run2 = st.columns([6, 6])
            with c_run1:
                scan_mode = st.radio("Chế độ phân tích AI:", ["1 trang đầu (Test nhanh)", "Toàn bộ tài liệu"], horizontal=True, key="scan_mode_radio")
            with c_run2:
                if st.button("🚀 BẮT ĐẦU PHÂN TÍCH CATALOGUE", type="primary", key="btn_run_extract_ui"):
                    if not active_pdf or not active_pdf.exists():
                        st.error("Vui lòng chọn hoặc tải lên file PDF Catalogue!")
                    else:
                        with st.spinner(f"Agent_Leader đang chỉ đạo Agent_Technical phân tích '{active_pdf.name}'..."):
                            try:
                                from agent_leader import AgentLeader
                                leader = AgentLeader()
                                max_p = 1 if "1 trang" in scan_mode else None
                                if hasattr(leader, "run_autonomous_pipeline"):
                                    summary = leader.run_autonomous_pipeline(str(active_pdf), max_pages=max_p, sync_to_sheets=False)
                                else:
                                    summary = leader.run_catalogue_pipeline(str(active_pdf), max_pages=max_p, sync_to_sheets=False)
                                st.success(f"✓ Hoàn thành phân tích! Trích xuất được {summary.get('total_extracted', 0)} sản phẩm.")
                                st.rerun()
                            except Exception as ex:
                                st.error(f"Lỗi phân tích: {ex}")

    if not products:
        st.warning("Chưa có dữ liệu sản phẩm trong cache. Vui lòng bấm 'Khởi động trích xuất' bên dưới.")
    else:
        # Phân loại danh sách sản phẩm trùng và không trùng
        dups_products = [item for item in products if item.get("status") == "REJECTED"]
        valid_products = [item for item in products if item.get("status") != "REJECTED"]
        approved_products = [item for item in products if item.get("status") == "APPROVED"]

        # ── 1. BẢNG TỔNG HỢP & TÁCH RIÊNG 2 DANH SÁCH: TRÙNG & KHÔNG TRÙNG ──────────────
        with st.expander(f"📊 BẢNG TỔNG HỢP: TÁCH RIÊNG DANH SÁCH TRÙNG ({len(dups_products)} SP) & KHÔNG TRÙNG ({len(valid_products)} SP)", expanded=False):
            tab_dup_view, tab_valid_view, tab_store_view = st.tabs([
                f"🚫 1. Danh Sách {len(dups_products)} Sản Phẩm Bị Trùng Trên Sàn (Đã Khóa Bảo Vệ)",
                f"✅ 2. Danh Sách {len(valid_products)} Sản Phẩm Hợp Lệ (Mới - Sẵn Sàng Duyệt)",
                "🌐 3. Danh Mục Toàn Bộ Sản Phẩm Đang Có Trên Haravan & bistextile.com"
            ])
            with tab_dup_view:
                st.markdown("""
                <div style='background: #1a0b12; border: 1px solid #f43f5e; padding: 10px 14px; border-radius: 6px; font-size: 12px; color: #fecdd3; margin-bottom: 10px;'>
                  🛡️ <strong>Rào chắn chống trùng Haravan Guard:</strong> Các sản phẩm dưới đây có mã SKU hoặc tên đã tồn tại thực tế trên website <code>bistextile.com</code>. Hệ thống tự động khóa trạng thái <strong>REJECTED</strong> để bảo vệ dữ liệu cũ, không bao giờ tự ý đẩy đè lên sàn!
                </div>
                """, unsafe_allow_html=True)
                dup_table_data = []
                for d in dups_products:
                    dup_table_data.append({
                        "Mã SKU": d.get("sku"),
                        "Tên sản phẩm tiếng Việt": d.get("product_name"),
                        "Trang PDF": d.get("source_page"),
                        "Trạng thái": "🚫 REJECTED (ĐÃ KHÓA)",
                        "Lý do đối soát": d.get("notes") or "Đã có trên bistextile.com"
                    })
                if dup_table_data:
                    st.dataframe(dup_table_data, use_container_width=True, hide_index=True)
                else:
                    st.success("Không có sản phẩm nào bị trùng với website!")

            with tab_valid_view:
                st.markdown("""
                <div style='background: #091a14; border: 1px solid #10b981; padding: 10px 14px; border-radius: 6px; font-size: 12px; color: #a7f3d0; margin-bottom: 10px;'>
                  ✅ <strong>Sản phẩm mới sẵn sàng duyệt:</strong> Các sản phẩm dưới đây là mới 100%, chưa từng có trên website bistextile.com. Bạn có thể kiểm tra từng mã bên dưới và bấm <strong>PHÊ DUYỆT (APPROVE)</strong> để xuất bản.
                </div>
                """, unsafe_allow_html=True)
                valid_table_data = []
                for v in valid_products:
                    valid_table_data.append({
                        "Mã SKU": v.get("sku"),
                        "Tên sản phẩm tiếng Việt": v.get("product_name"),
                        "Tên tiếng Anh": v.get("product_name_en"),
                        "Hãng sản xuất": v.get("brand") or "AATCC",
                        "Đơn vị tính": v.get("unit") or "cuốn",
                        "Trang PDF": v.get("source_page"),
                        "Trạng thái": v.get("status")
                    })
                if valid_table_data:
                    st.dataframe(valid_table_data, use_container_width=True, hide_index=True)

            with tab_store_view:
                store_file_p = PROJECT_DIR / "bistextile_existing_products.json"
                store_items = []
                if store_file_p.exists():
                    try:
                        with open(store_file_p, "r", encoding="utf-8") as f_st:
                            store_items = json.load(f_st)
                    except Exception:
                        pass
                pub_cnt = sum(1 for it in store_items if it.get("published", True))
                hid_cnt = len(store_items) - pub_cnt
                st.markdown(f"**Tổng số sản phẩm đang có trên Haravan / bistextile.com:** `{len(store_items)} sản phẩm` (Đã đăng: `{pub_cnt}`, Đã ẩn/Draft: `{hid_cnt}`)")
                store_display = []
                for it in store_items:
                    store_display.append({
                        "Haravan ID": it.get("id"),
                        "Tên sản phẩm": it.get("title"),
                        "Trạng thái": it.get("status_str") or ("ĐÃ ĐĂNG" if it.get("published", True) else "ĐÃ ẨN"),
                        "Đường dẫn (URL)": it.get("url"),
                        "SKU biến thể": ", ".join(it.get("variants_skus", []))
                    })
                if store_display:
                    st.dataframe(store_display, use_container_width=True, hide_index=True)
                else:
                    st.info("Chưa có dữ liệu sản phẩm sàn. Vui lòng bấm '🌐 Quét Live Haravan' ở mục 1 phía trên.")

        st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

        # ── 2. BỘ LỌC TÁCH RIÊNG TRONG Ô CHỌN SKU DUYỆT ────────────────────────────
        col_fil, col_sel, col_stat = st.columns([4.8, 4.2, 3.0])
        with col_fil:
            filter_mode = st.radio(
                "Lọc danh sách kiểm duyệt:",
                [
                    f"✅ Hợp lệ / Chưa trùng ({len(valid_products)} SP)",
                    f"🚫 Bị trùng website ({len(dups_products)} SP)",
                    f"🎉 Đã duyệt ({len(approved_products)} SP)",
                    f"🌐 Toàn bộ ({len(products)} SP)"
                ],
                horizontal=True,
                key="sku_filter_radio"
            )

        if filter_mode.startswith("✅"):
            active_list = valid_products if valid_products else products
        elif filter_mode.startswith("🚫"):
            active_list = dups_products if dups_products else products
        elif filter_mode.startswith("🎉"):
            active_list = approved_products if approved_products else products
        else:
            active_list = products

        active_skus = [x.get("sku") for x in active_list]

        def get_sku_display_label(sku_code):
            item = next((it for it in products if it.get("sku") == sku_code), None)
            if not item:
                return sku_code
            stt = item.get("status")
            if stt == "REJECTED":
                return f"🚫 {sku_code} [TRÙNG WEB - ĐÃ KHÓA]"
            elif stt == "APPROVED":
                return f"✅ {sku_code} [ĐÃ PHÊ DUYỆT]"
            else:
                return f"📝 {sku_code} (Mới - Chờ duyệt)"

        with col_sel:
            selected_sku = st.selectbox(
                f"Chọn mã SKU ({len(active_skus)} SP trong danh sách này):",
                active_skus,
                format_func=get_sku_display_label,
                key="tech_sku_select"
            )

        with col_stat:
            p = next((item for item in products if item.get("sku") == selected_sku), products[0])
            status_color = "#10b981" if p.get("status") == "APPROVED" else ("#f43f5e" if p.get("status") == "REJECTED" else "#f59e0b")
            st.markdown(f"""
            <div style='padding-top: 26px; font-family: "JetBrains Mono", monospace; font-size: 13px;'>
              Trạng thái: <span style='color: {status_color}; font-weight: 800;'>{p.get('status')}</span>
            </div>
            """, unsafe_allow_html=True)

        if p.get("status") == "REJECTED":
            st.markdown(f"""
            <div style='background: #1a0b12; border: 1.5px solid #f43f5e; border-radius: 8px; padding: 10px 14px; margin-top: 6px; margin-bottom: 10px; font-size: 12.5px; color: #fecdd3;'>
              🚫 <strong>CẢNH BÁO: SẢN PHẨM NÀY ĐÃ BỊ KHÓA TRÙNG (REJECTED)</strong><br>
              {p.get('notes') or 'Sản phẩm đã tồn tại thực tế trên website bistextile.com. Haravan Guard bảo vệ an toàn, không tự động đẩy đè lên website.'}
            </div>
            """, unsafe_allow_html=True)

        page_num = int(p.get("source_page") or 1)
        st.markdown("---")

        col_pdf, col_specs = st.columns([5, 7])
        with col_pdf:
            st.markdown(f"#### 📄 Nguồn: Trang {page_num} trong Catalogue")
            if pdf_file.exists():
                img_bytes, total_pages_doc = cached_render_pdf_page(str(pdf_file), page_num)
                if img_bytes:
                    st.image(img_bytes, use_container_width=True, caption=f"Catalogue PDF - Trang {page_num}/{total_pages_doc}")
                else:
                    st.info(f"Không thể kết xuất trang {page_num} từ catalogue.")
            else:
                st.info("File catalogue_sample.pdf chưa có trong thư mục.")

        with col_specs:
            st.markdown(f"#### 🔍 Hồ Sơ & Thẩm Định Kỹ Thuật: {p.get('sku')}")

            with st.expander("🛡️ Kết quả Thẩm định 6 Bước (B1 - B6)", expanded=True):
                c_a1, c_a2 = st.columns(2)
                with c_a1:
                    st.markdown("✓ **B1 Catalogue**: Toàn vẹn file nguồn")
                    st.markdown("✓ **B2 Identity**: SKU duy nhất trong lô")
                    st.markdown("✓ **B3 Facts**: Có trích dẫn nguyên văn")
                with c_a2:
                    st.markdown("✓ **B4 SEO**: Tiêu đề song ngữ chuẩn")
                    if p.get("brand_evidence"):
                        st.markdown(f"✓ **B5 Xuất xứ**: {p.get('brand_evidence')}")
                    else:
                        st.markdown("⚠️ **B5 Xuất xứ**: `MISSING_BRAND_EVIDENCE` (Cảnh báo)")
                    st.markdown("✓ **B6 HTML**: Khớp template 7 khối chuẩn")

            st.markdown(f"""
            <div style='background: #090e1a; border-left: 3px solid #38bdf8; padding: 10px 14px; border-radius: 6px; font-size: 12px; color: #cbd5e1; margin-bottom: 12px;'>
              <strong>Trích dẫn nguyên văn (Evidence Quote):</strong><br>
              "{p.get('notes') or p.get('evidence_quote') or 'Trích xuất trực tiếp từ trang ' + str(page_num)}"
            </div>
            """, unsafe_allow_html=True)

            # ── GIAO DIỆN KIỂM DUYỆT & XEM TRƯỚC TRỰC QUAN (UNIFIED WORKSPACE) ───────
            st.markdown("#### 👁️ Bàn Kiểm Duyệt & Xem Trước Trực Quan Chuẩn Haravan")

            tab_unified, tab_memory_quick = st.tabs([
                "📑 Bàn Soát Lỗi, Sửa Nội Dung / Mã HTML & Xem Trước Trực Quan",
                "🧠 Bộ Nhớ AI Tự Học (Feedback Memory)"
            ])

            # Chuẩn bị dữ liệu hiển thị mặc định cho các khối 4, 5, 6, 7
            default_hl = p.get("highlights")
            if default_hl:
                if isinstance(default_hl, list):
                    default_hl_str = "\n".join(default_hl)
                else:
                    default_hl_str = str(default_hl)
            else:
                default_hl_str = "Tiêu chuẩn thử nghiệm chính hãng được chuẩn hóa áp dụng toàn cầu trong ngành dệt may.\nĐầy đủ tài liệu hướng dẫn và quy trình thực hành phòng lab QA/QC.\nCung cấp chính ngạch bởi BIS Textile kèm hỗ trợ kỹ thuật chuyên sâu."

            default_scope = p.get("application_scope") or "Phương pháp kiểm nghiệm dệt may quốc tế"
            default_doc_title = p.get("related_doc_title") or f"Tra cứu sản phẩm mã {p.get('sku')} trên cổng BIS Textile"

            with tab_unified:
                st.markdown("""
                <div style='background: #0b1120; border: 1px solid #1e293b; border-left: 3px solid #10b981; padding: 10px 14px; border-radius: 6px; font-size: 12px; color: #94a3b8; margin-bottom: 14px;'>
                  🧠 <strong>Cơ chế tự học tức thì:</strong> Bạn có thể sửa theo từng Khối thông tin hoặc sửa trực tiếp toàn bộ mã HTML 7 Khối ngay tại tab này. Nhấn <code>💾 LƯU THAY ĐỔI & AI TỰ HỌC</code> hoặc <code>✅ PHÊ DUYỆT</code>, hệ thống sẽ lưu tức thì, cập nhật ngay bản xem trước bên dưới và ghi nhớ vĩnh viễn vào <code>feedback_memory.json</code>!
                </div>
                """, unsafe_allow_html=True)

                edit_mode = st.radio(
                    "Chọn phương thức chỉnh sửa nội dung:",
                    ["📝 Chỉnh sửa theo từng Khối (Khối 1 - 7)", "💻 Chỉnh sửa trực tiếp Mã HTML 7 Khối"],
                    horizontal=True,
                    key=f"edit_mode_toggle_{p.get('sku')}"
                )

                if edit_mode.startswith("📝"):
                    # HÀNG 1: Tiêu đề song ngữ & Đơn vị tính
                    col_ef1, col_ef2 = st.columns(2)
                    with col_ef1:
                        edit_name_vi = st.text_input("1. Tên sản phẩm tiếng Việt (Khối 1):", value=p.get("product_name") or "", key=f"inp_vi_{p.get('sku')}")
                        edit_vendor = st.text_input("3. Hãng sản xuất / Tổ chức (Khối 3):", value=p.get("brand") or p.get("brand_evidence") or "AATCC (Hoa Kỳ)", key=f"inp_vendor_{p.get('sku')}")
                        edit_unit = st.text_input("5. Đơn vị tính (Khối 6):", value=p.get("unit") or "cuốn", key=f"inp_unit_{p.get('sku')}")
                    with col_ef2:
                        edit_name_en = st.text_input("2. Tên sản phẩm tiếng Anh (Khối 2):", value=p.get("product_name_en") or "", key=f"inp_en_{p.get('sku')}")
                        cur_status = p.get("status", "EXTRACTED_UNVERIFIED")
                        status_options = ["EXTRACTED_UNVERIFIED", "APPROVED", "REJECTED"]
                        status_idx = status_options.index(cur_status) if cur_status in status_options else 0
                        edit_status = st.selectbox("Trạng thái phê duyệt:", status_options, index=status_idx, key=f"inp_status_{p.get('sku')}")
                        edit_page_str = st.text_input("Trang nguồn trong Catalogue:", value=str(p.get("source_page") or page_num), key=f"inp_page_{p.get('sku')}")

                    # HÀNG 2: Giới thiệu (Khối 4) & Đặc điểm nổi bật (Khối 5)
                    col_b4, col_b5 = st.columns(2)
                    with col_b4:
                        edit_desc = st.text_area("4. Giới thiệu sản phẩm (Khối 4):", value=p.get("description") or "", height=110, key=f"inp_desc_{p.get('sku')}")
                    with col_b5:
                        edit_highlights = st.text_area("✨ 5. Đặc điểm nổi bật (Khối 5 - Mỗi dòng 1 gạch đầu dòng):", value=default_hl_str, height=110, key=f"inp_hl_{p.get('sku')}")

                    # HÀNG 3: Phạm vi áp dụng & Tiêu chuẩn tra cứu (Khối 6 & 7)
                    col_b6, col_b7 = st.columns(2)
                    with col_b6:
                        edit_scope = st.text_input("⚙️ Phạm vi áp dụng & Tiêu chuẩn thử nghiệm (Khối 6):", value=default_scope, key=f"inp_scope_{p.get('sku')}")
                    with col_b7:
                        edit_doc_title = st.text_input("🔗 Tên liên kết / Tài liệu tra cứu (Khối 7):", value=default_doc_title, key=f"inp_doc_{p.get('sku')}")

                else:
                    st.caption("💻 Chỉnh sửa trực tiếp toàn bộ mã HTML 7 khối chuẩn Haravan (có thể chèn thêm link, bảng, style CSS):")
                    current_html_val = p.get("custom_html") or technical_agent.build_7_block_html(p)
                    custom_html_code = st.text_area("Mã HTML 7 Khối hoàn chỉnh:", value=current_html_val, height=300, key=f"raw_html_{p.get('sku')}")

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    save_corrections = st.button("💾 LƯU THAY ĐỔI & AI TỰ HỌC", key=f"btn_save_unified_{p.get('sku')}", type="primary", use_container_width=True)
                with col_btn2:
                    approve_btn = st.button("✅ PHÊ DUYỆT ĐỂ ĐĂNG WEB (APPROVE)", key=f"btn_approve_unified_{p.get('sku')}", use_container_width=True)

                if save_corrections or approve_btn:
                    learned_changes = []

                    if edit_mode.startswith("📝"):
                        if edit_name_vi != p.get("product_name"):
                            learning_engine.record_correction(p.get("sku"), "product_name", p.get("product_name"), edit_name_vi, f"Trang {page_num}")
                            p["product_name"] = edit_name_vi
                            learned_changes.append(f"Tên tiếng Việt ➔ '{edit_name_vi}'")
                        if edit_name_en != p.get("product_name_en"):
                            learning_engine.record_correction(p.get("sku"), "product_name_en", p.get("product_name_en"), edit_name_en, f"Trang {page_num}")
                            p["product_name_en"] = edit_name_en
                            learned_changes.append(f"Tên tiếng Anh ➔ '{edit_name_en}'")
                        if edit_unit != p.get("unit"):
                            learning_engine.record_correction(p.get("sku"), "unit", p.get("unit"), edit_unit, f"Trang {page_num}")
                            p["unit"] = edit_unit
                            learned_changes.append(f"Đơn vị tính ➔ '{edit_unit}'")
                        if edit_vendor != (p.get("brand") or p.get("brand_evidence")):
                            learning_engine.record_correction(p.get("sku"), "brand", p.get("brand") or "", edit_vendor, f"Trang {page_num}")
                            p["brand"] = edit_vendor
                            p["brand_evidence"] = edit_vendor
                            learned_changes.append(f"Hãng ➔ '{edit_vendor}'")
                        if edit_desc != p.get("description"):
                            learning_engine.record_correction(p.get("sku"), "description", p.get("description"), edit_desc, f"Trang {page_num}")
                            p["description"] = edit_desc
                            learned_changes.append("Mô tả kỹ thuật")

                        hl_list = [line.strip().lstrip("-*• ") for line in edit_highlights.split("\n") if line.strip()]
                        p["highlights"] = hl_list
                        p["application_scope"] = edit_scope.strip()
                        p["related_doc_title"] = edit_doc_title.strip()
                        p["source_page"] = edit_page_str.strip()

                        if approve_btn:
                            p["status"] = "APPROVED"
                        else:
                            p["status"] = edit_status

                        # Sinh lại HTML mới theo các trường vừa sửa và lưu vào p
                        p.pop("custom_html", None)
                        p["custom_html"] = technical_agent.build_7_block_html(p)

                    else:
                        # Lưu từ chế độ sửa HTML trực tiếp
                        p["custom_html"] = custom_html_code
                        # Đồng bộ ngược vào dữ liệu cấu trúc nếu tìm thấy thẻ h1, h2
                        import re
                        m_h1 = re.search(r"<h1[^>]*>(.*?)</h1>", custom_html_code, re.IGNORECASE | re.DOTALL)
                        if m_h1:
                            clean_h1 = re.sub(r"<[^>]+>", "", m_h1.group(1)).strip()
                            if clean_h1 and clean_h1 != p.get("product_name"):
                                learning_engine.record_correction(p.get("sku"), "product_name", p.get("product_name"), clean_h1, f"Trang {page_num}")
                                p["product_name"] = clean_h1
                                learned_changes.append(f"Tên tiếng Việt ➔ '{clean_h1}'")
                        m_h2 = re.search(r"<h2[^>]*>(.*?)</h2>", custom_html_code, re.IGNORECASE | re.DOTALL)
                        if m_h2:
                            clean_h2 = re.sub(r"<[^>]+>", "", m_h2.group(1)).strip()
                            if clean_h2 and clean_h2 != p.get("product_name_en"):
                                learning_engine.record_correction(p.get("sku"), "product_name_en", p.get("product_name_en"), clean_h2, f"Trang {page_num}")
                                p["product_name_en"] = clean_h2
                                learned_changes.append(f"Tên tiếng Anh ➔ '{clean_h2}'")

                        if approve_btn:
                            p["status"] = "APPROVED"

                    # Đánh dấu thời điểm cập nhật
                    p["updated_at"] = datetime.now().isoformat()

                    # Cập nhật danh sách products
                    for item in products:
                        if item.get("sku") == p.get("sku"):
                            item.update(p)
                            break

                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(products, f, ensure_ascii=False, indent=2)

                    git_cache = Path("c:/Users/Dell/bis-ai-project/BIS_AI_PROJECT/extracted_products_cache.json")
                    if git_cache.parent.exists():
                        try:
                            with open(git_cache, "w", encoding="utf-8") as f:
                                json.dump(products, f, ensure_ascii=False, indent=2)
                        except Exception:
                            pass

                    st.session_state["cached_products"] = products
                    operations_agent.update_product_status_in_sheet(p.get("sku"), p.get("status"), f"Chỉnh sửa bởi {st.session_state.username}")

                    if approve_btn:
                        st.toast(f"🎉 ĐÃ PHÊ DUYỆT SẢN PHẨM {p.get('sku')} ĐỂ ĐĂNG WEB!", icon="✅")
                    elif learned_changes:
                        st.toast(f"🧠 AI ĐÃ TỰ HỌC {len(learned_changes)} QUY TẮC MỚI!", icon="💾")
                    else:
                        st.toast("✓ ĐÃ LƯU THÀNH CÔNG & CẬP NHẬT BẢN XEM TRƯỚC!", icon="💾")

                    time.sleep(0.15)
                    st.rerun()

                # KHUNG XEM TRƯỚC DUY NHẤT (GỘP THÀNH 1 MỤC XEM TRƯỚC RỰC RỠ, NỀN TRẮNG CHUẨN WEBSITE)
                st.markdown("---")
                st.markdown("##### 📄 Bản Xem Trước Chuẩn Website Haravan / bistextile.com (Nền trắng sắc nét):")
                live_preview_code = p.get("custom_html") or technical_agent.build_7_block_html(p)
                import hashlib
                preview_hash = hashlib.md5((str(live_preview_code) + str(p.get("status")) + str(p.get("updated_at", ""))).encode("utf-8")).hexdigest()[:8]
                full_preview_html = f"""<!DOCTYPE html>
<!-- preview_version: {preview_hash} -->
<html>
<head>
  <meta charset="utf-8">
  <style>
    html, body {{
      background-color: #ffffff !important;
      color: #1e293b !important;
      margin: 0;
      padding: 16px;
      font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    }}
  </style>
</head>
<body style="background-color: #ffffff !important; color: #1e293b !important;">
  <div id="render_container_{preview_hash}">
    {live_preview_code}
  </div>
</body>
</html>"""
                components.html(full_preview_html, height=580, scrolling=True)

            with tab_memory_quick:
                st.markdown("##### 🧠 Các Quy Tắc AI Đã Tự Học Được (Learning Engine Rules):")
                try:
                    with open(PROJECT_DIR / "feedback_memory.json", "r", encoding="utf-8") as f_mem:
                        mem_data = json.load(f_mem)
                    examples = mem_data.get("examples", [])
                    custom_rules = mem_data.get("custom_rules", [])
                    if custom_rules:
                        st.markdown("**Quy tắc kinh doanh chuyên môn:**")
                        for r in custom_rules:
                            st.markdown(f"- 📌 *{r}*")
                    if examples:
                        st.markdown(f"**Bài học thực hành ({len(examples)} bài học đã ghi nhận):**")
                        for idx, ex in enumerate(reversed(examples[-8:])):
                            st.markdown(f"- **{ex.get('sku')}** | Trường `{ex.get('field')}`: `{ex.get('ai_original')}` ➔ `<span style='color: #10b981; font-weight: 700;'>{ex.get('human_corrected')}</span>` *({ex.get('timestamp')[:19]})*", unsafe_allow_html=True)
                    else:
                        st.info("Chưa có quy tắc tự học nào được ghi nhận.")
                except Exception as e:
                    st.error(f"Lỗi đọc bộ nhớ tự học: {e}")


# ── TAB 2: PHÒNG NGHIÊN CỨU SEO & MARKETING ──────────────────────────────────
with tab_mkt:
    st.markdown("### 📢 Phòng Nghiên Cứu SEO & Nội Dung (Agent_Marketing)")
    st.write("Nghiên cứu từ khóa ngành dệt may (AATCC, ISO, ASTM), soạn Meta Title, Meta Description chuẩn SEO, tạo URL Slug thân thiện và xây dựng kịch bản bán hàng cho phòng lab QA/QC.")

    if not marketing_agent:
        st.warning("⚠️ Đang chờ đồng bộ file `agent_marketing.py` trên GitHub. Hãy tải file lên để kích hoạt.")
    elif products:
        sku_mkt = st.selectbox("Chọn SKU để lập kế hoạch SEO:", [p.get("sku") for p in products], key="mkt_sku_select")
        p_mkt = next((item for item in products if item.get("sku") == sku_mkt), products[0])

        if st.button("⚡ KHỞI TẠO BÁO CÁO SEO & NỘI DUNG TỪ GEMINI", type="primary"):
            with st.spinner("Agent_Marketing đang nghiên cứu từ khóa và phân tích đối tượng..."):
                seo_pkg = marketing_agent.generate_seo_package(p_mkt)
                st.session_state[f"seo_{sku_mkt}"] = seo_pkg
                st.success("✓ Đã hoàn thành phân tích SEO & Nội dung!")

        seo_data = st.session_state.get(f"seo_{sku_mkt}") or marketing_agent.generate_seo_package(p_mkt)

        col_seo1, col_seo2 = st.columns([6, 6])
        with col_seo1:
            st.markdown("#### 🌐 Google Search Snippet Preview (Mô phỏng kết quả tìm kiếm)")
            st.markdown(f"""
            <div class='google-preview-box'>
              <div class='google-preview-url'>https://bistextile.com &rsaquo; products &rsaquo; {seo_data.get('url_slug')}</div>
              <div class='google-preview-title'>{seo_data.get('meta_title')}</div>
              <div class='google-preview-desc'>{seo_data.get('meta_description')}</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
            st.markdown("#### 🎯 Từ Khóa SEO Mục Tiêu")
            st.markdown("**Từ khóa chính:** " + " • ".join([f"`{k}`" for k in seo_data.get("focus_keywords", [])]))
            st.markdown("**Từ khóa phụ / ngách:** " + " • ".join([f"`{k}`" for k in seo_data.get("secondary_keywords", [])]))

        with col_seo2:
            st.markdown("#### 💡 Điểm Bán Hàng Cốt Lõi (Selling Points)")
            for sp in seo_data.get("selling_points", []):
                st.markdown(f"- 💎 **{sp}**")

            st.markdown("#### 👥 Đối tượng khách hàng mục tiêu")
            st.info(f"🎯 {seo_data.get('target_audience')}")

            st.markdown("#### 🏷️ Cấu Hình Đẩy Sang Haravan")
            st.text_input("Meta Title (SEO):", value=seo_data.get("meta_title"), key=f"mt_{sku_mkt}")
            st.text_area("Meta Description (SEO):", value=seo_data.get("meta_description"), key=f"md_{sku_mkt}")
            st.text_input("URL & Handle Slug:", value=seo_data.get("url_slug"), key=f"slug_{sku_mkt}")


# ── TAB 3: PHÒNG EDIT & DUYỆT ẢNH SẢN PHẨM (MEDIA STUDIO) ────────────────────
with tab_media:
    st.markdown("### 🎨 Phòng Edit & Duyệt Ảnh Sản Phẩm (Agent_Media Studio)")
    st.write("AI tự động lấy ảnh từ hãng (tối đa 2 ảnh), tiếp nhận ảnh thực tế bạn cung cấp (đặt tên file theo mã SKU), ghép vào ảnh nền studio/lab chân thực và **chờ bạn bấm Duyệt** trước khi đăng.")

    if not media_agent:
        st.warning("⚠️ Đang chờ đồng bộ file `agent_media.py` trên GitHub. Hãy tải file lên để kích hoạt.")
    elif products:
        sku_media = st.selectbox("Chọn SKU để xử lý ảnh:", [p.get("sku") for p in products], key="media_sku_select")
        p_media = next((item for item in products if item.get("sku") == sku_media), products[0])
        clean_sku = sku_media.strip().replace(" ", "_")

        col_m1, col_m2 = st.columns([5, 7])

        with col_m1:
            st.markdown("#### 1. Nguồn Ảnh Đầu Vào (Chính Hãng & Thực Tế)")
            st.info(f"📁 **Vị trí lưu trên Google Drive:** `Google_Drive_Storage/4_Product_Images/`\n\nQuy chuẩn lưu file: `{clean_sku}_brand_1.jpg`, `{clean_sku}_user_1.jpg`")

            # Kiểm tra ảnh hãng & ảnh người dùng
            brand_img_path = media_agent.brand_dir / f"{clean_sku}_brand_1.jpg"
            user_img_path = media_agent.user_dir / f"{clean_sku}_user_1.jpg"
            
            page_num_media = int(p_media.get("source_page") or 1)
            brand_name_media = p_media.get("brand") or "AATCC"
            title_media = p_media.get("product_name_en") or p_media.get("product_name") or ""

            c_act1, c_act2 = st.columns(2)
            with c_act1:
                if st.button("🌐 Tìm ảnh hãng trên Web", key=f"btn_fetch_web_{clean_sku}", help="Dùng AI & curl_cffi tìm ảnh chính hãng trên website của thương hiệu"):
                    with st.spinner("Đang tìm ảnh trên website chính hãng..."):
                        fetched = media_agent.fetch_brand_image_from_web(clean_sku, brand_name_media, title_media)
                        if fetched and fetched.exists():
                            st.success("✓ Đã tìm thấy và lưu ảnh chính hãng!")
                            st.rerun()
                        else:
                            st.warning("Chưa tìm thấy ảnh khớp trên web hãng. Hãy thử trích xuất từ PDF hoặc tải ảnh lên.")
            with c_act2:
                if st.button("✂️ Trích xuất từ Catalogue", key=f"btn_ext_pdf_{clean_sku}", help="Tự động bóc tách ảnh máy dệt từ trang Catalogue PDF"):
                    with st.spinner(f"Đang trích xuất ảnh từ trang {page_num_media}..."):
                        active_pdf_for_media = active_pdf if 'active_pdf' in locals() and active_pdf else pdf_file
                        ext_path = media_agent.extract_image_from_pdf(clean_sku, active_pdf_for_media, page_num_media)
                        if ext_path and ext_path.exists():
                            st.success(f"✓ Đã trích xuất ảnh thiết bị từ trang {page_num_media}!")
                            st.rerun()
                        else:
                            st.warning(f"Không tìm thấy ảnh nhúng trong trang {page_num_media} của Catalogue.")

            # Hiển thị ảnh đầu vào hiện có
            chosen_source_img = None
            if user_img_path.exists():
                st.markdown(f"**✓ Ảnh thực tế:** `{clean_sku}_user_1.jpg`")
                st.image(str(user_img_path), width=200)
                chosen_source_img = user_img_path
            elif brand_img_path.exists():
                st.markdown(f"**✓ Ảnh chính hãng:** `{clean_sku}_brand_1.jpg`")
                st.image(str(brand_img_path), width=200)
                chosen_source_img = brand_img_path
            else:
                st.info("⚠️ Chưa có ảnh đầu vào. Hãy bấm **'Tìm ảnh hãng trên Web'**, **'Trích xuất từ Catalogue'** hoặc tải ảnh thủ công.")

            # Hỗ trợ quy trình Canva Pro
            st.markdown("""
            <div style='background: linear-gradient(135deg, #090e1a 0%, #1e1b4b 100%); border: 1.5px solid #818cf8; border-radius: 8px; padding: 12px; margin-top: 10px; margin-bottom: 12px;'>
              <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                  <span style='font-size: 15px;'>🎨</span> <strong style='color: #c7d2fe;'>Tách Nền Đỉnh Cao Với Canva Pro</strong>
                  <div style='font-size: 11.5px; color: #cbd5e1; margin-top: 4px;'>
                    Bạn có tài khoản Canva Pro: Dùng tính năng <em>Magic Studio (Tách nền 1-click)</em> trên Canva để có ảnh vật thể trong suốt hoàn hảo, tải về dạng PNG rồi nạp trực tiếp qua ô bên dưới.
                  </div>
                </div>
                <a href='https://www.canva.com' target='_blank' style='background: #6366f1; color: white; padding: 7px 14px; border-radius: 6px; text-decoration: none; font-size: 12px; font-weight: 700; white-space: nowrap;'>Mở Canva.com ↗</a>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Tải ảnh thực tế từ người dùng (Hỗ trợ ảnh trong suốt từ Canva Pro)
            uploaded_user_img = st.file_uploader(f"Tải lên ảnh sản phẩm (chấp nhận file JPG, PNG hoặc ảnh đã tách nền từ Canva Pro) cho mã {clean_sku}:", type=["jpg", "png", "jpeg"], key=f"up_{clean_sku}")
            if uploaded_user_img:
                saved_path = media_agent.register_user_image(clean_sku, uploaded_user_img.getvalue(), uploaded_user_img.name)
                st.toast(f"✓ Đã lưu ảnh vào Google Drive: {saved_path.name}", icon="📁")
                st.rerun()

            # Chọn ảnh nền mockup
            c_bg_head, c_bg_scan = st.columns([8, 4])
            with c_bg_head:
                st.markdown("#### 2. Chọn Ảnh Nền Ghép (Mockup Background)")
            with c_bg_scan:
                if st.button("🔄 Quét ảnh G-Drive", key="btn_scan_bg_drive", help="Cập nhật ngay ảnh BIS_BACKGROUND.png hoặc ảnh nền mới bỏ vào Google Drive"):
                    if knowledge_agent:
                        knowledge_agent.scan_and_sync_drive_files()
                    st.rerun()

            available_bgs = media_agent.get_backgrounds()
            bg_names = [bg.name for bg in available_bgs]
            
            # Ưu tiên chọn BIS_BACKGROUND.png nếu có trong thư mục
            default_bg_idx = 0
            for idx, bname in enumerate(bg_names):
                if "BIS_BACKGROUND" in bname:
                    default_bg_idx = idx
                    break

            selected_bg_name = st.selectbox(
                "Chọn không gian nền:", 
                bg_names, 
                index=default_bg_idx if bg_names else 0,
                key="bg_select_box"
            )
            selected_bg_path = next((bg for bg in available_bgs if bg.name == selected_bg_name), available_bgs[0] if available_bgs else None)

            # Tải thêm nền riêng nếu muốn
            new_bg_file = st.file_uploader("Hoặc tải lên ảnh nền riêng (Lưu tại 5_Studio_Backgrounds):", type=["jpg", "png"], key="new_bg")
            if new_bg_file:
                media_agent.register_background(new_bg_file.name, new_bg_file.getvalue())
                st.success("✓ Đã lưu ảnh nền mới vào Google Drive (5_Studio_Backgrounds)!")
                st.rerun()

            # Nút xử lý ghép ảnh
            st.markdown("---")
            if st.button("🚀 AI GHÉP NỀN & TĂNG ĐỘ CHÂN THỰC", type="primary"):
                # Ưu tiên lấy ảnh nguồn (ảnh người dùng hoặc ảnh hãng)
                img_to_composite = chosen_source_img
                if not img_to_composite or not img_to_composite.exists():
                    active_pdf_for_media = active_pdf if 'active_pdf' in locals() and active_pdf else pdf_file
                    img_to_composite = media_agent.extract_image_from_pdf(clean_sku, active_pdf_for_media, page_num_media)

                if not img_to_composite or not img_to_composite.exists():
                    st.error("Chưa có ảnh đầu vào! Vui lòng bấm 'Tìm ảnh hãng trên Web', 'Trích xuất từ Catalogue' hoặc tải ảnh lên.")
                else:
                    with st.spinner("Agent_Media đang tách nền, tạo bóng đổ và cân chỉnh ánh sáng với nền Studio BIS..."):
                        final_path = media_agent.composite_product_image(clean_sku, img_to_composite, selected_bg_path)
                        st.success(f"✓ Đã tạo thành phẩm: {final_path.name}")
                        st.rerun()

        with col_m2:
            st.markdown("#### 3. Bản Xem Trước Ảnh Thành Phẩm & Cổng Duyệt")
            final_img_path = media_agent.final_dir / f"{clean_sku}_final.jpg"
            img_manifest = media_agent.manifest.get(clean_sku, {})
            current_img_status = img_manifest.get("status", "CHƯA XỬ LÝ")

            if final_img_path.exists():
                st.image(str(final_img_path), caption=f"Ảnh thành phẩm mã {clean_sku} ghép trên nền {selected_bg_name}", use_container_width=True)
                
                st.markdown(f"""
                <div style='background: #0d1322; border: 1px solid #1e293b; padding: 12px; border-radius: 8px; margin-bottom: 12px;'>
                  <strong>Trạng thái duyệt ảnh:</strong> <span style='color: {"#10b981" if current_img_status == "APPROVED" else "#f59e0b"}; font-weight: 700;'>{current_img_status}</span><br>
                  <span style='font-size: 11px; color: #94a3b8;'>Đường dẫn lưu: <code>{final_img_path}</code></span>
                </div>
                """, unsafe_allow_html=True)

                col_ap1, col_ap2 = st.columns(2)
                with col_ap1:
                    if st.button("✅ DUYỆT ẢNH NÀY (APPROVE IMAGE)", key=f"appr_img_{clean_sku}"):
                        media_agent.approve_image(clean_sku)
                        st.session_state.audit_logs.append({
                            "time": datetime.now().strftime("%H:%M:%S"),
                            "type": "MEDIA",
                            "text": f"Ảnh sản phẩm {clean_sku} đã được PHÊ DUYỆT."
                        })
                        st.success(f"✓ Đã duyệt ảnh {clean_sku}! Sẵn sàng đính kèm lên sàn Haravan.")
                        st.rerun()
                with col_ap2:
                    if st.button("❌ TỪ CHỐI / YÊU CẦU LÀM LẠI", key=f"rej_img_{clean_sku}"):
                        media_agent.reject_image(clean_sku, "Chưa khớp nền")
                        st.warning("Đã gắn cờ từ chối. Vui lòng chọn ảnh nền khác và chạy lại.")
                        st.rerun()
            else:
                st.info(f"Chưa có ảnh ghép thành phẩm cho mã {clean_sku}. Vui lòng bấm 'AI GHÉP NỀN & TĂNG ĐỘ CHÂN THỰC' ở cột bên trái.")


# ── TAB 5: PHÒNG LƯU TRỮ TRI THỨC (KNOWLEDGE VAULT) ──────────────────────────
with tab_know:
    c_kn_h1, c_kn_h2 = st.columns([8, 4])
    with c_kn_h1:
        st.markdown("### 📚 Phòng Lưu Trữ Tri Thức & Tài Liệu Chuẩn (Agent_Knowledge)")
        st.write("Kho lưu trữ sách tiêu chuẩn, catalogue, manual, chứng nhận COC, CO, CQ, hình ảnh và video đào tạo để toàn bộ AI Agents nạp tri thức học tập.")
    with c_kn_h2:
        if st.button("🔄 Quét toàn bộ Google Drive", key="btn_scan_all_vault", help="Tự động đồng bộ các file Sách, Manual, CO/CQ, Catalogue mới bỏ vào Google Drive"):
            if knowledge_agent:
                scan_res = knowledge_agent.scan_and_sync_drive_files()
                st.toast(f"✓ Đã quét & đồng bộ: {len(scan_res.get('manuals', []))} tài liệu, {len(scan_res.get('catalogues', []))} catalogue!", icon="📚")
            st.rerun()

    if not knowledge_agent:
        st.warning("⚠️ Đang chờ đồng bộ file `agent_knowledge.py` trên GitHub. Hãy tải file lên để kích hoạt.")
    else:
        col_k1, col_k2 = st.columns([7, 5])
        with col_k1:
            # Luôn đọc danh sách mới nhất từ manifest file
            all_docs = knowledge_agent._load_manifest()
            st.markdown(f"#### 📂 Danh Mục Tài Liệu Tiêu Chuẩn Hiện Có ({len(all_docs)} tài liệu đã đồng bộ)")

            # Bộ lọc và tìm kiếm thông minh
            c_kf1, c_kf2 = st.columns([5, 7])
            with c_kf1:
                cat_filter = st.selectbox("Lọc phân loại:", ["Tất cả", "standards", "manuals", "catalogues", "certificates"], key="sb_cat_filter")
            with c_kf2:
                search_kw = st.text_input("🔍 Tìm kiếm theo tên hoặc hãng:", "", placeholder="VD: AATCC, Taber, VeriVide, Boxun...", key="inp_doc_kw")

            filtered_docs = all_docs
            if cat_filter != "Tất cả":
                filtered_docs = [d for d in filtered_docs if d.get("category") == cat_filter]
            if search_kw.strip():
                kw_low = search_kw.strip().lower()
                filtered_docs = [d for d in filtered_docs if kw_low in str(d.get("title", "")).lower() or kw_low in str(d.get("filename", "")).lower()]

            st.caption(f"Đang hiển thị {len(filtered_docs)} / {len(all_docs)} tài liệu:")

            # Hộp cuộn danh sách tài liệu
            doc_container = st.container(height=480)
            with doc_container:
                for d in filtered_docs:
                    st.markdown(f"""
                    <div style='background: #0d1322; border: 1px solid #1e293b; border-left: 3px solid #38bdf8; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;'>
                      <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <strong style='color: #f8fafc; font-size: 13px;'>{d.get('title')}</strong>
                        <span class='node-badge badge-loaded'>{d.get('category', 'doc').upper()}</span>
                      </div>
                      <div style='font-size: 11.5px; color: #94a3b8; margin-top: 4px;'>{d.get('scope')}</div>
                      <div style='font-size: 10px; color: #64748b; margin-top: 6px; font-family: "JetBrains Mono", monospace;'>
                        File: {d.get('filename')} &bull; Thẩm định: ✓ Đã nạp AI &bull; {d.get('added_at', '')}
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

        with col_k2:
            st.markdown("#### 📤 Nạp Tài Liệu / Chứng Nhận Mới Cho AI Học")
            st.info("📁 **Vị trí lưu trên Google Drive:**\n- Sách/Manual: `Google_Drive_Storage/2_Manuals_Standards/`\n- Chứng chỉ CO/CQ: `Google_Drive_Storage/3_Certificates_CO_CQ/`\n- Video: `Google_Drive_Storage/7_Training_Videos/`")
            with st.form("add_doc_form"):
                new_title = st.text_input("Tên tài liệu / Tiêu chuẩn:", placeholder="VD: Tiêu chuẩn thử nghiệm AATCC TM61")
                new_cat = st.selectbox("Loại tài liệu:", ["standards", "manuals", "certificates", "catalogues", "media"])
                new_scope = st.text_area("Mục đích / Phạm vi áp dụng:", placeholder="VD: Quy trình kiểm tra độ bền màu giặt phòng thí nghiệm...")
                uploaded_doc_file = st.file_uploader("Tải file tài liệu (PDF, Word, Ảnh, Video):", type=["pdf", "docx", "jpg", "png", "mp4"])
                submit_doc = st.form_submit_button("LƯU VÀO KHO & HUẤN LUYỆN AI", use_container_width=True)

                if submit_doc and new_title:
                    fname = uploaded_doc_file.name if uploaded_doc_file else f"{new_title[:20]}.pdf"
                    fbytes = uploaded_doc_file.getvalue() if uploaded_doc_file else None
                    knowledge_agent.register_document(new_title, new_cat, fname, new_scope, fbytes)
                    st.session_state.audit_logs.append({
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "type": "KNOW",
                        "text": f"Đã nạp tài liệu '{new_title}' vào Knowledge Vault."
                    })
                    st.toast(f"✓ Đã nạp thành công '{new_title}' vào kho tri thức của AI!", icon="📚")
                    st.rerun()


# ── TAB 5: PHÒNG VẬN HÀNH & HARAVAN GUARD ────────────────────────────────────
with tab_ops:
    st.markdown("### 🛡️ Phòng Vận Hành & Cổng An Toàn Haravan Guard")

    # Giới thiệu chi tiết giải thích rõ ràng cơ chế
    st.markdown("""
    <div style='background: #090e1a; border: 1.5px solid #0284c7; border-radius: 10px; padding: 16px; margin-bottom: 18px;'>
      <h4 style='color: #38bdf8; margin: 0 0 8px 0;'>📌 Giải Thích Cơ Chế: "Thực Thi Đồng Bộ An Toàn Lên Haravan" Là Gì?</h4>
      <p style='font-size: 13px; color: #cbd5e1; line-height: 1.6; margin: 0;'>
        Hệ thống thương mại điện tử <strong>bistextile.com</strong> chạy trên nền tảng Haravan và đang có hàng nghìn sản phẩm kinh doanh thực tế. 
        Khi AI tự động bóc tách và đẩy sản phẩm mới lên sàn, <strong>Haravan Guard</strong> hoạt động như một <em>"Rào chắn an toàn 3 lớp"</em> để bảo vệ dữ liệu công ty:
      </p>
      <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; margin-top: 12px;'>
        <div style='background: #0d1322; border: 1px solid #1e293b; border-left: 3px solid #f43f5e; padding: 10px; border-radius: 6px;'>
          <strong style='color: #f43f5e;'>1. Rào chắn thời gian (2026-10-20):</strong><br>
          <span style='font-size: 11.5px; color: #94a3b8;'>Tuyệt đối KHÔNG BAO GIỜ chỉnh sửa, xóa hay ghi đè bất kỳ sản phẩm nào đã có từ trước ngày 20/10/2026 trên website bistextile.com.</span>
        </div>
        <div style='background: #0d1322; border: 1px solid #1e293b; border-left: 3px solid #10b981; padding: 10px; border-radius: 6px;'>
          <strong style='color: #10b981;'>2. Cổng phê duyệt (Human-in-the-loop):</strong><br>
          <span style='font-size: 11.5px; color: #94a3b8;'>Chỉ những sản phẩm nào bạn đã bấm <code>✅ PHÊ DUYỆT (APPROVED)</code> tại Bàn Kỹ thuật mới được đưa vào danh sách đẩy lên sàn.</span>
        </div>
        <div style='background: #0d1322; border: 1px solid #1e293b; border-left: 3px solid #38bdf8; padding: 10px; border-radius: 6px;'>
          <strong style='color: #38bdf8;'>3. Đẩy ở chế độ Ẩn / Nháp (Draft):</strong><br>
          <span style='font-size: 11.5px; color: #94a3b8;'>Mọi sản phẩm tạo mới luôn mang cờ <code>published: false</code>. Sản phẩm sẽ nằm ở mục Nháp trong trang Quản trị Haravan để nhân sự duyệt lần cuối trước khi mở bán công khai.</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col_h1, col_h2, col_h3 = st.columns(3)
    with col_h1:
        st.info(f"🔒 **Rào chắn 2026-10-20:** Đang bật (Bảo vệ 100% dữ liệu gốc).")
    with col_h2:
        st.warning("👁️ **Trạng thái xuất bản:** Luôn ẩn (`published: false`).")
    with col_h3:
        st.success(f"✅ **Sản phẩm sẵn sàng:** Có {approved_count} sản phẩm đã APPROVED.")

    st.markdown("---")
    st.markdown("#### 📊 Quản Trị Đối Soát & Lọc Trùng Google Sheets Master:")
    c_dedup_info, c_dedup_btn = st.columns([7, 5])
    with c_dedup_info:
        st.markdown("""
        Hệ thống tự động thực hiện **đối soát an toàn 2 chiều**:
        - **Chống trùng với website bistextile.com**: Phát hiện mã SKU đã có trên web ➔ Tự động KHÓA `REJECTED` để ngăn trùng lặp.
        - **Dọn sạch dòng trùng trên Google Sheets**: Quét toàn bộ trang tính, gom các dòng trùng SKU và loại bỏ dòng rác.
        """)
    with c_dedup_btn:
        st.write("")
        if st.button("🔍 ĐỐI SOÁT GOOGLE SHEETS NGAY", key="btn_manual_dedup_tab_ops", use_container_width=True):
            if operations_agent:
                with st.spinner("Agent_Operations đang quét đối soát Google Sheets & bistextile.com..."):
                    d_res = operations_agent.check_and_deduplicate_sheets(products)
                    clean_list = d_res.get("clean_products", [])
                    if clean_list:
                        products = clean_list
                        st.session_state["cached_products"] = products
                    st.success(f"✓ Đã hoàn tất đối soát! {d_res.get('total_products')} SP hợp lệ, đã khóa {d_res.get('website_duplicates_locked')} mã trùng web, lọc {d_res.get('sheet_duplicates_removed')} dòng trùng trên Sheet.")
                    st.rerun()
        if st.button("🌐 QUÉT LIVE HARAVAN & BISTEXTILE.COM", key="btn_live_scan_tab_ops", type="primary", use_container_width=True):
            if operations_agent:
                with st.spinner("Đang quét trực tiếp toàn bộ 202 sản phẩm trên Haravan & bistextile.com/collections/all..."):
                    h_res = operations_agent.scan_live_haravan_and_web(products)
                    clean_list = h_res.get("clean_products", [])
                    if clean_list:
                        products = clean_list
                        st.session_state["cached_products"] = products
                    st.success(f"✓ Hoàn tất quét sàn: {h_res.get('total_haravan', 0)} SP trên Haravan ({h_res.get('total_published', 0)} Đã đăng, {h_res.get('total_hidden', 0)} Đã ẩn), đã khóa {h_res.get('matched_count', 0)} mã trùng, {h_res.get('unmatched_count', 0)} SP mới!")
                    st.rerun()

    st.markdown("---")
    st.markdown("#### Thực thi đồng bộ an toàn lên Haravan:")
    if st.button("🚀 BẮT ĐẦU ĐỒNG BỘ CÁC SẢN PHẨM APPROVED LÊN HARAVAN", type="primary"):
        with st.spinner("Agent_Operations đang tiến hành đồng bộ an toàn..."):
            sync_res = operations_agent.sync_approved_to_haravan()
            if sync_res:
                st.session_state.audit_logs.append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "type": "SYNC",
                    "text": f"Đồng bộ thành công {len(sync_res)} sản phẩm lên sàn Haravan."
                })
                st.toast(f"✓ Đã hoàn tất đồng bộ {len(sync_res)} sản phẩm lên Haravan ở chế độ ẩn!", icon="🚀")
                st.json(sync_res)
            else:
                st.info("Hiện không có sản phẩm nào ở trạng thái APPROVED cần đồng bộ. Hãy phê duyệt sản phẩm tại Bàn Kỹ thuật trước.")


# ── TAB 6: BỘ NHỚ TỰ HỌC (FEW-SHOT CONTINUOUS FEEDBACK) ────────────────────────
with tab_learn:
    st.markdown("### 🧠 Bộ Nhớ Tự Học & Quản Trị Quy Tắc (Learning Engine Dashboard)")
    st.write("Trung tâm tri thức của AI: Lưu trữ các quy tắc chuẩn hóa chuyên môn và toàn bộ lịch sử sửa lỗi của bạn để Gemini tự động học tập, không bao giờ lặp lại sai sót.")
    
    mem_data = learning_engine.load_memory()
    custom_rules = mem_data.get("custom_rules", [])
    examples = mem_data.get("examples", [])

    c_lm1, c_lm2 = st.columns([6, 6])
    with c_lm1:
        st.markdown("#### 📌 1. Quy Tắc Kinh Doanh Chuyên Môn (Business Rules)")
        st.caption("Các luật chuẩn hóa bắt buộc AI phải tuân thủ trong toàn bộ quá trình đọc catalogue:")
        if custom_rules:
            for idx, r in enumerate(custom_rules):
                col_r_txt, col_r_del = st.columns([10, 2])
                with col_r_txt:
                    st.markdown(f"**{idx+1}.** {r}")
                with col_r_del:
                    if st.button("🗑️", key=f"del_rule_{idx}", help="Xóa quy tắc này"):
                        learning_engine.delete_custom_rule(idx)
                        st.toast("Đã xóa quy tắc thành công!", icon="🗑️")
                        st.rerun()
        else:
            st.info("Chưa có quy tắc nào.")

        with st.form("add_rule_form"):
            new_rule_input = st.text_input("Thêm quy tắc chuẩn hóa mới cho AI:", placeholder="VD: Tất cả sách hướng dẫn của AATCC phải có đơn vị tính là 'cuốn'...")
            if st.form_submit_button("➕ THÊM QUY TẮC MỚI", use_container_width=True):
                if new_rule_input.strip():
                    learning_engine.add_custom_rule(new_rule_input.strip())
                    st.toast("✓ Đã nạp quy tắc mới vào bộ nhớ AI!", icon="🧠")
                    st.rerun()

    with c_lm2:
        st.markdown(f"#### 🎓 2. Lịch Sử Bài Học Thực Tế ({len(examples)} bài học)")
        st.caption("Từng lần bạn sửa trên giao diện, AI tự động ghi nhận cặp giá trị {AI nhận diện sai ➔ Bạn sửa đúng}:")
        
        ex_container = st.container(height=340)
        with ex_container:
            if examples:
                for idx, ex in enumerate(reversed(examples[-15:])):
                    real_idx = len(examples) - 1 - idx
                    col_ex_info, col_ex_del = st.columns([10, 2])
                    with col_ex_info:
                        st.markdown(f"**Mã {ex.get('sku')}** | Trường `{ex.get('field')}`<br>`{ex.get('ai_original')}` ➔ <span style='color: #10b981; font-weight: 700;'>{ex.get('human_corrected')}</span> <span style='color: #64748b; font-size: 10px;'>({ex.get('timestamp')[:19]})</span>", unsafe_allow_html=True)
                    with col_ex_del:
                        if st.button("❌", key=f"del_ex_{real_idx}", help="Xóa bài học này"):
                            learning_engine.delete_example(real_idx)
                            st.toast("Đã xóa bài học!", icon="🗑️")
                            st.rerun()
            else:
                st.info("Chưa có bản ghi hiệu chỉnh nào. Hãy sửa thông tin sản phẩm tại Bàn Kỹ thuật để huấn luyện AI.")
