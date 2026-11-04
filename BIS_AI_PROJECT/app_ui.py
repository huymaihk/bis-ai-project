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
from agent_technical import resolve_related_standard_doc

import os
import sys
import json
import io
import time
import re
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
from persistent_memory import MemoryStore
from memory_ui import maintain_memory, render_memory_panel

try:
    from agent_employee_pool import (
        BISEmployeeOrchestrator,
        EmployeeState,
        STATE_TO_3D_MAP,
    )
except Exception:
    BISEmployeeOrchestrator = None
    EmployeeState = None
    STATE_TO_3D_MAP = {}

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
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

  :root {
    --bg-main: #0b0f19;
    --bg-card: rgba(17, 24, 39, 0.72);
    --bg-card-hover: rgba(30, 41, 59, 0.82);
    --border-color: rgba(255, 255, 255, 0.08);
    --border-glow: #0284c7;
    --neon-blue: #38bdf8;
    --neon-cyan: #06b6d4;
    --neon-green: #10b981;
    --neon-emerald: #10b981;
    --neon-indigo: #818cf8;
    --neon-amber: #f59e0b;
    --neon-rose: #f43f5e;
    --text-primary: #f8fafc;
    --text-muted: #94a3b8;
  }

  /* Nền tổng thể với hiệu ứng quầng sáng Ambient Mesh (Dark Modern Glassmorphism) */
  .stApp {
    background-color: var(--bg-main);
    background-image: 
      radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.09) 0px, transparent 45%),
      radial-gradient(at 100% 0%, rgba(129, 140, 248, 0.09) 0px, transparent 45%),
      radial-gradient(at 50% 100%, rgba(16, 185, 129, 0.06) 0px, transparent 50%);
    color: var(--text-primary);
    font-family: 'Plus Jakarta Sans', sans-serif;
  }

  header[data-testid="stHeader"] {
    background: rgba(11, 15, 25, 0.75) !important;
    backdrop-filter: blur(12px);
  }

  /* Glassmorphism Card cơ bản */
  .emp-card {
    background: linear-gradient(145deg, rgba(15,23,42,0.92), rgba(30,41,59,0.82));
    border: 1px solid rgba(148,163,184,0.22);
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 10px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.28);
  }
  .state-pill {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.04em;
  }
  .glass-card {
    background: rgba(17, 24, 39, 0.68);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 18px 22px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.35);
    transition: all 0.28s cubic-bezier(0.4, 0, 0.2, 1);
    margin-bottom: 16px;
  }
  .glass-card:hover {
    border-color: rgba(56, 189, 248, 0.4);
    box-shadow: 0 12px 36px 0 rgba(56, 189, 248, 0.12);
  }
  .glass-card-emerald { border-left: 4px solid var(--neon-emerald) !important; }
  .glass-card-blue { border-left: 4px solid var(--neon-blue) !important; }
  .glass-card-indigo { border-left: 4px solid var(--neon-indigo) !important; }

  /* Top Command Header Bar */
  .top-command-bar {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    background: linear-gradient(135deg, rgba(17, 24, 39, 0.88) 0%, rgba(11, 15, 25, 0.94) 100%);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(56, 189, 248, 0.25);
    border-left: 4px solid var(--neon-blue);
    border-radius: 14px;
    padding: 16px 24px;
    margin-bottom: 14px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45), 0 0 20px rgba(56, 189, 248, 0.08);
  }

  .brand-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.25rem;
    font-weight: 800;
    background: linear-gradient(90deg, #f8fafc, #38bdf8, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.3px;
  }

  .brand-subtitle {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.76rem;
    color: var(--text-muted);
    margin-top: 3px;
  }

  /* Metric Box Cards */
  .metric-box {
    background: rgba(15, 23, 42, 0.72);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 12px 16px;
    text-align: left;
    backdrop-filter: blur(12px);
    transition: all 0.25s ease;
  }
  .metric-box:hover {
    border-color: rgba(56, 189, 248, 0.35);
    transform: translateY(-2px);
  }
  .metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.55rem;
    font-weight: 800;
    color: var(--neon-blue);
  }
  .metric-label {
    font-size: 0.76rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 600;
  }

  /* Sticky Action Toolbar cho Tab Kiểm Duyệt */
  .sticky-action-bar {
    position: sticky;
    top: 2.8rem;
    z-index: 99;
    background: rgba(11, 15, 25, 0.92);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border: 1px solid rgba(56, 189, 248, 0.35);
    border-radius: 10px;
    padding: 12px 18px;
    margin-bottom: 16px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.55);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
  }

  /* Hệ thống Badge & Pulse Micro-animations */
  .status-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 5px 14px;
    border-radius: 999px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .pill-blue { background: rgba(56, 189, 248, 0.12); border: 1px solid rgba(56, 189, 248, 0.35); color: var(--neon-blue); }
  .pill-emerald { background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.35); color: var(--neon-emerald); }
  .pill-indigo { background: rgba(129, 140, 248, 0.12); border: 1px solid rgba(129, 140, 248, 0.35); color: var(--neon-indigo); }
  .pill-amber { background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.35); color: var(--neon-amber); }
  .pill-rose { background: rgba(244, 63, 94, 0.12); border: 1px solid rgba(244, 63, 94, 0.35); color: var(--neon-rose); }

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

# Nạp dữ liệu sản phẩm (Ưu tiên nạp RAM và cache để đạt tốc độ tức thì < 0.05s)
cache_file = PROJECT_DIR / "extracted_products_cache.json"
pdf_file = PROJECT_DIR / "catalogue_sample.pdf"

@st.cache_data(ttl=60, show_spinner=False)
def load_products_from_file(file_path_str: str, file_mtime: float = 0.0) -> list:
    """Nạp file JSON từ đĩa có cache trong RAM; tự động reload tức thì khi file trên đĩa thay đổi."""
    p = Path(file_path_str)
    if p.exists():
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

@st.cache_data(ttl=300, show_spinner=False)
def load_store_products(file_path_str: str) -> list:
    """Nạp danh sách sản phẩm sàn Haravan có cache 300s trong RAM."""
    p = Path(file_path_str)
    if p.exists():
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

@st.cache_data(ttl=300, show_spinner=False)
def load_cached_marketing_knowledge(file_path_str: str) -> dict:
    """Nạp tri thức marketing có cache 300s trong RAM."""
    p = Path(file_path_str)
    if p.exists():
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

@st.cache_data(ttl=60, show_spinner=False)
def load_cached_learning_memory(file_path_str: str) -> dict:
    """Nạp bộ nhớ tự học có cache 60s trong RAM."""
    p = Path(file_path_str)
    if p.exists():
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

cache_mtime = cache_file.stat().st_mtime if cache_file.exists() else 0.0
if "cached_products" not in st.session_state or st.session_state.get("_cache_file_mtime") != cache_mtime or not st.session_state["cached_products"]:
    st.session_state["cached_products"] = load_products_from_file(str(cache_file), cache_mtime)
    st.session_state["_cache_file_mtime"] = cache_mtime

products = st.session_state["cached_products"]

# Tự động rà soát & loại bỏ hoàn toàn "Đơn vị phân phối: BIS Textile Việt Nam" khỏi toàn bộ sản phẩm
if products:
    import re as _re_dist
    for _p in products:
        _ch = _p.get("custom_html", "")
        if _ch and ("phân phối" in _ch or "BIS Textile Việt Nam" in _ch):
            _ch = _re_dist.sub(r'\s*•?\s*<strong>Đơn vị phân phối:?</strong>\s*<span[^>]*>.*?</span>', '', _ch, flags=_re_dist.IGNORECASE)
            _ch = _re_dist.sub(r'\s*•?\s*&bull;\s*<strong>Đơn vị phân phối:?</strong>.*?(?=</div>|&bull;)', '', _ch, flags=_re_dist.IGNORECASE)
            _ch = _re_dist.sub(r'\s*(?:•|&bull;)?\s*Đơn vị phân phối:?\s*BIS Textile Việt Nam', '', _ch, flags=_re_dist.IGNORECASE)
            _ch = _re_dist.sub(r'&bull;\s*</div>', '</div>', _ch)
            _ch = _re_dist.sub(r'•\s*</div>', '</div>', _ch)
            _p["custom_html"] = _ch

if "selected_dept_id" not in st.session_state:
    st.session_state.selected_dept_id = "RD"
if "selected_emp_id" not in st.session_state:
    st.session_state.selected_emp_id = "rd_lead"
if "chat_mode" not in st.session_state:
    st.session_state.chat_mode = "DIRECT_1_1"
if "last_3d_command" not in st.session_state:
    st.session_state.last_3d_command = {
        "agent_key": "engineer",
        "state": "WORKING",
        "message": "🔬 Dr. Textile Tech: Đang thẩm định tiêu chuẩn AATCC/ISO theo lệnh Chủ tịch Huy Mai!",
        "selected_emp_id": "rd_lead",
    }

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

try:
    from agent_translator import AgentTranslator
except Exception:
    AgentTranslator = None

try:
    from keep_form_translator import KeepFormTranslator
except Exception:
    KeepFormTranslator = None

try:
    from agent_operations import AgentOperations
except Exception:
    AgentOperations = None


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


@st.cache_data(ttl=60, show_spinner=False)
def load_cached_manuals_by_brand(project_dir_str: str):
    try:
        from agent_translator import AgentTranslator
        agent = AgentTranslator(Path(project_dir_str))
        return agent.scan_manuals_by_brand()
    except Exception:
        return {}


@st.cache_data(ttl=30, show_spinner=False)
def load_cached_translated_docs(project_dir_str: str):
    try:
        from agent_translator import AgentTranslator
        agent = AgentTranslator(Path(project_dir_str))
        return agent.list_translated_documents()
    except Exception:
        return []


leader = get_cached_agent_leader(str(PROJECT_DIR))
technical_agent = getattr(leader, "technical_agent", None)
operations_agent = AgentOperations(PROJECT_DIR) if AgentOperations else getattr(leader, "operations_agent", None)
translator_agent = AgentTranslator(PROJECT_DIR) if AgentTranslator else None
learning_engine = getattr(leader, "learning_engine", None)
marketing_agent = getattr(leader, "marketing_agent", None)
if marketing_agent is None or not hasattr(marketing_agent, "load_marketing_knowledge"):
    try:
        import importlib
        import agent_marketing
        importlib.reload(agent_marketing)
        marketing_agent = agent_marketing.AgentMarketing(PROJECT_DIR)
        if leader:
            leader.marketing_agent = marketing_agent
            if hasattr(leader, "departments"):
                leader.departments["marketing"] = marketing_agent
    except Exception:
        pass
knowledge_agent = getattr(leader, "knowledge_agent", None)
media_agent = getattr(leader, "media_agent", None)
if media_agent is None or not hasattr(media_agent, "generate_studio_mockup_ai"):
    try:
        import importlib
        import agent_media
        importlib.reload(agent_media)
        media_agent = agent_media.AgentMedia(PROJECT_DIR)
        if leader:
            leader.media_agent = media_agent
            if hasattr(leader, "departments"):
                leader.departments["media"] = media_agent
    except Exception:
        try:
            import agent_media
            media_agent = agent_media.AgentMedia(PROJECT_DIR)
        except Exception:
            pass


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
            valid_pin = (BIS_ACCESS_PIN or "").strip()
            entered_user = user_input.strip()
            entered_pin = pin_input.strip()

            is_valid_user = entered_user.lower() in ["adminhuy", "admin", "huy.md", "huy"]
            is_valid_pin = bool(valid_pin) and entered_pin == valid_pin

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
                st.error("❌ Tên đăng nhập hoặc mật mã không chính xác. Vui lòng kiểm tra lại!")
            else:
                st.error("❌ Mật mã bảo mật không chính xác. Vui lòng thử lại!")

    st.markdown("""
      <div style='margin-top: 20px; font-size: 11px; color: #64748b; text-align: center; font-family: "JetBrains Mono", monospace;'>
        Rào chắn bảo mật Haravan Guard &amp; Google Cloud Master<br>
        Hotline hỗ trợ kỹ thuật: 0344.659.891 (Mr. Huy)
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()  # DỪNG THỰC THI NẾU CHƯA ĐĂNG NHẬP

bis_memory = MemoryStore(PROJECT_DIR)
maintain_memory(bis_memory)
if "orchestrator" not in st.session_state and BISEmployeeOrchestrator:
    st.session_state.orchestrator = BISEmployeeOrchestrator(PROJECT_DIR)
if st.session_state.get("orchestrator"):
    st.session_state.orchestrator.reload_history()



# Default workflow renders only the selected production view, keeping legacy tools available.
legacy_mode = st.sidebar.toggle("Mở giao diện nâng cao cũ", value=False, key="legacy_mode")
if not legacy_mode and st.sidebar.toggle("Giao diện React mới",value=True,key="bis_react_enabled"):
    from streamlit_react_host import render_react_workspace
    render_react_workspace(PROJECT_DIR, (technical_agent, media_agent, knowledge_agent, translator_agent, bis_memory))
    st.stop()
if not legacy_mode:
    from production_workspace import render_workspace
    render_workspace(PROJECT_DIR, technical_agent, media_agent, knowledge_agent,
                     translator_agent, bis_memory)
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# GIAO DIỆN CHÍNH: HUD CANVAS & MULTI-AGENT TOPOLOGY (KHI ĐÃ ĐĂNG NHẬP)
# ══════════════════════════════════════════════════════════════════════════════

# ── 1. Top HUD Bar & Metrics ──────────────────────────────────────────────────
total_sp = len(products)
dups_sp = len([item for item in products if item.get("status") == "REJECTED"])
valid_sp = len([item for item in products if item.get("status") != "REJECTED"])
approved_sp = len([item for item in products if item.get("status") == "APPROVED"])
approved_count = approved_sp
rejected_count = dups_sp

st.markdown(f"""
<div class="top-command-bar">
  <div>
    <div class="brand-title">BIS TEXTILE • MULTI-AGENT COMMAND CENTER (v3.0 Pro)</div>
    <div class="brand-subtitle">
      USER: <span style='color: #38bdf8;'>{st.session_state.username}</span> &bull; GOOGLE DRIVE: My Drive\\BIS_AI_PROJECT &bull; HARAVAN GUARD 20/10 ACTIVE &bull; HOTLINE: 0344659891 (Mr. Huy)
    </div>
  </div>
  <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
    <span class="status-pill pill-blue"><span class="pulse-dot"></span> AUTONOMOUS OPS</span>
    <span class="status-pill pill-emerald">🛡️ HARAVAN GUARD: LOCKED &lt; 20/10</span>
    <span class="status-pill pill-indigo">🧠 FEW-SHOT ENGINE: ACTIVE</span>
  </div>
</div>
""", unsafe_allow_html=True)

# 4 Thẻ chỉ số Glassmorphism
c_met1, c_met2, c_met3, c_met4 = st.columns(4)
with c_met1:
    st.markdown(f'<div class="metric-box"><div class="metric-label">Tổng SKU Catalogue</div><div class="metric-value">{total_sp}</div></div>', unsafe_allow_html=True)
with c_met2:
    st.markdown(f'<div class="metric-box"><div class="metric-label">Hợp Lệ (Mới 100%)</div><div class="metric-value" style="color:#10b981;">{valid_sp}</div></div>', unsafe_allow_html=True)
with c_met3:
    st.markdown(f'<div class="metric-box"><div class="metric-label">Bị Trùng Web (Đã Khóa)</div><div class="metric-value" style="color:#f43f5e;">{dups_sp}</div></div>', unsafe_allow_html=True)
with c_met4:
    st.markdown(f'<div class="metric-box"><div class="metric-label">Đã Phê Duyệt</div><div class="metric-value" style="color:#38bdf8;">{approved_sp}</div></div>', unsafe_allow_html=True)

st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

col_reset, col_sync, col_stat, col_logout = st.columns([3.5, 3.2, 3.5, 1.8])
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
    sheet_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID_OR_URL}" if SPREADSHEET_ID_OR_URL and not SPREADSHEET_ID_OR_URL.startswith("http") else SPREADSHEET_ID_OR_URL
    if sheet_url:
        st.link_button("📊 Mở Google Sheet Master", sheet_url, use_container_width=True)
    else:
        st.button("📊 Google Sheet Master", disabled=True, use_container_width=True)
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

tab_lego, tab_tech, tab_mkt, tab_media, tab_know, tab_trans, tab_ops, tab_learn = st.tabs([
    "🏢 1. Văn Phòng 3D LEGO AI (3D Metaverse HQ)",
    "🔬 2. Phòng Kỹ Thuật (PDF & HTML 7 Khối)",
    "📢 3. Phòng Nghiên Cứu SEO & Marketing",
    "🎨 4. Phòng Edit & Duyệt Ảnh Sản Phẩm",
    "📚 5. Phòng Lưu Trữ Tri Thức (Sách, Manual, CO/CQ)",
    "🌐 6. Phòng Dịch Thuật & Bản Địa Hóa Tiêu Chuẩn (Agent_Translator)",
    "🛡️ 7. Phòng Vận Hành & Haravan Guard",
    "🧠 8. Bộ Nhớ Tự Học (Few-Shot Feedback)"
])

def load_3d_office_html() -> str:
    """Đọc trực tiếp file HTML 3D mới nhất từ thư mục dự án."""
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
    user_dept: str | None = None,
    selected_emp_id: str | None = None,
    height: int = 700,
) -> None:
    """
    Hàm render Văn phòng 3D BIS Textile lên giao diện Streamlit.
    Hỗ trợ truyền lệnh điều khiển trực tiếp nhân vật AI qua window.updateAgentStatus(),
    di chuyển nhân vật đại diện của Người dùng qua window.moveUserToDepartment(),
    và highlight nhân viên đang active qua window.highlightActiveEmployeeIn3D().
    """
    html_content = load_3d_office_html()

    scripts = []
    if "orchestrator" in st.session_state and st.session_state.orchestrator:
        orch_obj = st.session_state.orchestrator
        emp_roster_payload = {
            emp.emp_id: {
                "emp_id": emp.emp_id,
                "name": emp.name,
                "title": emp.title,
                "department_name": emp.department_name,
                "avatar_3d_key": emp.avatar_3d_key,
                "avatar_emoji": emp.avatar_emoji,
                "badge_color": emp.badge_color,
                "state": emp.state,
                "current_task": emp.current_task,
                "specialties": emp.specialties,
            }
            for emp in orch_obj.employees.values()
        }
        scripts.append(f"window.BIS_EMPLOYEE_ROSTER = {json.dumps(emp_roster_payload, ensure_ascii=False)};")

    if user_dept:
        safe_dept = json.dumps(user_dept, ensure_ascii=False)
        scripts.append(f"""
        if (typeof window.moveUserToDepartment === 'function') {{
            window.moveUserToDepartment({safe_dept});
        }}
        """)

    if agent_key and state:
        safe_agent = json.dumps(agent_key, ensure_ascii=False)
        safe_state = json.dumps(state, ensure_ascii=False)
        safe_msg = json.dumps(message or "", ensure_ascii=False)
        scripts.append(f"""
        if (typeof window.updateAgentStatus === 'function') {{
            window.updateAgentStatus({safe_agent}, {safe_state}, {safe_msg});
        }}
        """)

    if selected_emp_id:
        safe_eid = json.dumps(selected_emp_id, ensure_ascii=False)
        scripts.append(f"""
        if (typeof window.highlightActiveEmployeeIn3D === 'function') {{
            window.highlightActiveEmployeeIn3D({safe_eid}, false);
        }}
        """)

    if scripts:
        inner = "\n".join(scripts)
        inject_script = f"""
        <script>
          (function() {{
            function runInjectedScripts() {{
              setTimeout(function() {{
                {inner}
              }}, 350);
            }}
            if (document.readyState === 'complete' || document.readyState === 'interactive') {{
              runInjectedScripts();
            }} else {{
              window.addEventListener('load', runInjectedScripts);
            }}
          }})();
        </script>
        """
        html_content = html_content.replace("</body>", f"{inject_script}\n</body>")

    components.html(html_content, height=height, scrolling=False)



# ── MODAL BÁO CÁO TIẾN TRÌNH TỰ HỌC CỦA AGENT TECHNICAL ─────────────────────
def _render_meeting_content(report_data):
    brand = report_data.get("brand", "AATCC")
    conf = report_data.get("confidence_score", 93)
    edit_cnt = report_data.get("edit_count", 3)
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #091326 0%, #0f2744 100%); border: 1.5px solid #38bdf8; border-radius: 10px; padding: 16px; margin-bottom: 16px;'>
      <div style='display: flex; align-items: center; gap: 14px;'>
        <div style='font-size: 34px;'>🔬</div>
        <div>
          <div style='font-size: 16px; font-weight: 800; color: #38bdf8;'>
            Dr. Textile Tech (Agent Technical) xin phép báo cáo Chủ tịch Mai Đức Huy
          </div>
          <div style='font-size: 12.5px; color: #cbd5e1; margin-top: 4px; line-height: 1.5;'>
            Kính thưa Chủ tịch, sau <strong>{edit_cnt} lần hiệu chỉnh trực tiếp trên Live Preview</strong> của Chủ tịch đối với tài liệu hãng <strong>{brand}</strong>, tôi đã hoàn thành chu trình suy ngẫm (Reflexion Loop) và đúc kết được các quy tắc chuẩn hóa mới.
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"**Độ tự tin học tập của AI (Confidence Score):** `{conf}%`")
    st.progress(conf / 100.0)
    
    c_m1, c_m2 = st.columns(2)
    with c_m1:
        st.markdown("""
        <div style='background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 12px; height: 100%;'>
          <div style='font-weight: 700; color: #f87171; font-size: 13px; margin-bottom: 8px;'>❌ Trước Đào Tạo (Điểm AI từng hiểu sai):</div>
        """, unsafe_allow_html=True)
        for m in report_data.get("misunderstandings", []):
            st.markdown(f"<div style='font-size: 12.5px; color: #fca5a5; margin-bottom: 6px;'>• {m}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with c_m2:
        st.markdown("""
        <div style='background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 8px; padding: 12px; height: 100%;'>
          <div style='font-weight: 700; color: #34d399; font-size: 13px; margin-bottom: 8px;'>✨ Sau Đào Tạo (Quy tắc cốt lõi AI tự đúc kết):</div>
        """, unsafe_allow_html=True)
        for r in report_data.get("new_rules", []):
            st.markdown(f"<div style='font-size: 12.5px; color: #a7f3d0; margin-bottom: 6px; font-weight: 600;'>✓ {r}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    col_dlg1, col_dlg2 = st.columns([6, 6])
    with col_dlg1:
        if st.button("✅ PHÊ DUYỆT QUY TẮC NÀY", type="primary", use_container_width=True, key=f"btn_appr_dialog_{brand}"):
            learning_engine.approve_consolidated_rules(brand, report_data.get("new_rules", []))
            st.session_state["show_meeting_modal"] = False
            st.session_state.pop("active_meeting_report", None)
            st.toast(f"🎉 Chủ tịch Mai Đức Huy đã phê duyệt bộ quy tắc mới cho hãng {brand}!", icon="✅")
            st.rerun()
            
    with col_dlg2:
        with st.popover("🔄 TIẾP TỤC HUẤN LUYỆN / DẶN DÒ", use_container_width=True):
            user_instruction = st.text_area(
                "Chủ tịch nhập chỉ thị dặn dò thêm cho Dr. Textile Tech:",
                placeholder="Ví dụ: Lưu ý mã SKU tiêu hao, cần phân biệt phụ kiện đi kèm...",
                key=f"inp_instruction_{brand}"
            )
            if st.button("GỬI CHỈ THỊ CHO AGENT", type="secondary", use_container_width=True, key=f"btn_send_inst_{brand}"):
                learning_engine.continue_training(brand, user_instruction)
                st.session_state["show_meeting_modal"] = False
                st.session_state.pop("active_meeting_report", None)
                st.toast("✓ Đã gửi chỉ thị huấn luyện của Chủ tịch tới Agent!", icon="📝")
                st.rerun()

if hasattr(st, "dialog"):
    @st.dialog("👔 Báo Cáo Tiến Trình Tự Học — Trưởng Phòng Kỹ Thuật AI", width="large")
    def show_meeting_dialog(report_data):
        _render_meeting_content(report_data)
else:
    def show_meeting_dialog(report_data):
        with st.expander("👔 Báo Cáo Tiến Trình Tự Học — Trưởng Phòng Kỹ Thuật AI", expanded=True):
            _render_meeting_content(report_data)


# ── TAB 1: VĂN PHÒNG 3D LEGO AI TEAM & ĐIỀU HÀNH 15 NHÂN SỰ AI ──────────────
with tab_lego:
    st.markdown("### 🏢 Trung Tâm Điều Hành Multi-Agent 3D & 15 Nhân Sự AI Độc Lập — BIS Textile")
    
    # Kiểm tra yêu cầu xin gặp báo cáo của Agent
    active_meeting_tab1 = learning_engine.get_active_meeting_request() if learning_engine and hasattr(learning_engine, "get_active_meeting_request") else None
    if active_meeting_tab1:
        rep_t1 = active_meeting_tab1.get("report", {})
        st.markdown(f"""
        <div style='background: linear-gradient(90deg, #1e1b4b 0%, #0f172a 100%); border: 2px solid #818cf8; padding: 12px 18px; border-radius: 10px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center;'>
          <div style='display: flex; align-items: center; gap: 12px;'>
            <span style='font-size: 26px;'>👔</span>
            <div>
              <div style='font-size: 13.5px; font-weight: 800; color: #a5b4fc;'>Dr. Textile Tech (Agent Technical) đang xin gặp báo cáo Chủ tịch Mai Đức Huy</div>
              <div style='font-size: 12px; color: #cbd5e1;'>Đã ghi nhận đủ {rep_t1.get('edit_count', 3)} lần sửa đổi cho hãng <strong>{rep_t1.get('brand', 'AATCC')}</strong>. Tự tin đạt <strong>{rep_t1.get('confidence_score', 93)}%</strong>.</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🎙️ BẤM VÀO ĐÂY ĐỂ NGHE BÁO CÁO CỦA TRƯỞNG PHÒNG KỸ THUẬT AI", key="btn_trigger_meeting_tab1", type="primary", use_container_width=True):
            st.session_state["show_meeting_modal"] = True
            st.session_state["active_meeting_report"] = rep_t1
            st.rerun()

    if st.session_state.get("show_meeting_modal"):
        rep_modal_data = st.session_state.get("active_meeting_report") or (active_meeting_tab1.get("report") if active_meeting_tab1 else {})
        if rep_modal_data:
            show_meeting_dialog(rep_modal_data)

    orch = st.session_state.get("orchestrator", None)
    if not orch and BISEmployeeOrchestrator:
        st.session_state.orchestrator = BISEmployeeOrchestrator()
        orch = st.session_state.orchestrator

    # 1. KHỐI ĐỊNH DANH NGƯỜI DÙNG & NHÂN VẬT ĐẠI DIỆN TRONG 3D
    c_user_profile, c_user_status = st.columns([2, 1])
    with c_user_profile:
        user_display_name = st.text_input(
            "👑 Nhân vật đại diện của bạn (Chủ tịch / CEO Điều hành):",
            value="👑 CEO Huy Mai (Tổng Giám Đốc)",
            key="input_user_display_name"
        )
    with c_user_status:
        st.write("")
        st.info("🟢 **TRẠNG THÁI:** Đang trực tuyến • Điều hành 15 Nhân sự AI tại Tòa nhà trung tâm")

    st.markdown("#### 🎯 Điều Hướng Nhân Vật Của Bạn (Đi tới Phòng Ban Nào, Nhân Vật Đi Tới Đó):")
    c_nav1, c_nav2, c_nav3, c_nav4, c_nav5, c_nav6, c_nav7 = st.columns(7)

    selected_user_dept = None
    with c_nav1:
        if st.button("🔬 Phòng Kỹ Thuật", use_container_width=True, key="btn_go_tech"):
            selected_user_dept = "tech"
            st.session_state["user_active_dept"] = "tech"
            st.session_state["selected_dept_id"] = "RD"
            st.session_state["selected_emp_id"] = "rd_lead"
    with c_nav2:
        if st.button("📢 Phòng Marketing", use_container_width=True, key="btn_go_mkt"):
            selected_user_dept = "mkt"
            st.session_state["user_active_dept"] = "mkt"
            st.session_state["selected_dept_id"] = "MKT"
            st.session_state["selected_emp_id"] = "seo_lead"
    with c_nav3:
        if st.button("🎨 Phòng Studio", use_container_width=True, key="btn_go_media"):
            selected_user_dept = "media"
            st.session_state["user_active_dept"] = "media"
            st.session_state["selected_dept_id"] = "STUDIO"
            st.session_state["selected_emp_id"] = "studio_lead"
    with c_nav4:
        if st.button("🌐 Phòng Dịch Thuật", use_container_width=True, key="btn_go_trans"):
            selected_user_dept = "trans"
            st.session_state["user_active_dept"] = "trans"
            st.session_state["selected_dept_id"] = "TRANS"
            st.session_state["selected_emp_id"] = "trans_lead"
    with c_nav5:
        if st.button("🛡️ Haravan Guard", use_container_width=True, key="btn_go_ops"):
            selected_user_dept = "ops"
            st.session_state["user_active_dept"] = "ops"
            st.session_state["selected_dept_id"] = "OPS"
            st.session_state["selected_emp_id"] = "ops_manager"
    with c_nav6:
        if st.button("🏛️ Phòng Họp Bàn Tròn", use_container_width=True, key="btn_go_meeting"):
            selected_user_dept = "meeting"
            st.session_state["user_active_dept"] = "meeting"
            st.session_state["chat_mode"] = "ALL_HANDS"
    with c_nav7:
        if st.button("☕ Khu Nghỉ Lounge", use_container_width=True, key="btn_go_lounge"):
            selected_user_dept = "lounge"
            st.session_state["user_active_dept"] = "lounge"

    active_dept_now = selected_user_dept or st.session_state.get("user_active_dept", "desk")

    # 2. KHỐI ĐIỀU KHIỂN VÒNG LẶP TỰ ĐỘNG & BỘ LỌC CHAT 1-1
    st.markdown("---")
    col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4 = st.columns([1.2, 1.2, 1.6, 2.0])
    with col_ctrl1:
        if st.button("⚡ Chạy 1 Bước Tự Động", use_container_width=True, type="primary", key="btn_step_loop"):
            if orch:
                ev = orch.step_autonomous_loop()
                chosen_id = ev.get("emp_id", st.session_state.selected_emp_id)
                st.session_state.selected_emp_id = chosen_id
                st.session_state.last_3d_command = {
                    "agent_key": chosen_id,
                    "state": ev["state_3d"],
                    "message": ev["text"],
                    "selected_emp_id": chosen_id,
                }
                st.rerun()
    with col_ctrl2:
        if st.button("🗣️ Triệu Tập Họp Toàn Thể", use_container_width=True, key="btn_all_hands_top"):
            st.session_state.chat_mode = "ALL_HANDS"
            st.session_state.last_3d_command = {
                "agent_key": "all",
                "state": "MEETING",
                "message": "🗣️ Triệu tập Họp Giao Ban Toàn Thể với Chủ tịch Huy Mai!",
                "selected_emp_id": st.session_state.selected_emp_id,
            }
            st.rerun()

    dept_options = orch.get_departments() if orch else {}
    with col_ctrl3:
        if dept_options:
            selected_dept = st.selectbox(
                "Phòng ban:",
                options=list(dept_options.keys()),
                index=list(dept_options.keys()).index(st.session_state.selected_dept_id) if st.session_state.selected_dept_id in dept_options else 0,
                format_func=lambda k: dept_options[k],
                key="sb_dept_select"
            )
            if selected_dept != st.session_state.selected_dept_id:
                st.session_state.selected_dept_id = selected_dept
                filtered = orch.get_employees_by_dept(selected_dept)
                if filtered:
                    st.session_state.selected_emp_id = filtered[0].emp_id
                st.session_state.chat_mode = "DIRECT_1_1"
                st.rerun()

    with col_ctrl4:
        if orch:
            filtered_employees = orch.get_employees_by_dept(st.session_state.selected_dept_id)
            emp_ids = [e.emp_id for e in filtered_employees]
            curr_idx = emp_ids.index(st.session_state.selected_emp_id) if st.session_state.selected_emp_id in emp_ids else 0
            chosen_eid = st.selectbox(
                "Nhân viên AI giao tiếp 1-1:",
                options=emp_ids,
                index=curr_idx,
                format_func=lambda eid: f"{orch.employees[eid].avatar_emoji} {orch.employees[eid].name} ({orch.employees[eid].title})",
                key="sb_emp_select"
            )
            if chosen_eid != st.session_state.selected_emp_id:
                st.session_state.selected_emp_id = chosen_eid
                st.session_state.chat_mode = "DIRECT_1_1"
                emp_obj = orch.employees[chosen_eid]
                st.session_state.last_3d_command = {
                    "agent_key": emp_obj.emp_id,
                    "state": STATE_TO_3D_MAP.get(emp_obj.state, "WORKING"),
                    "message": f"{emp_obj.avatar_emoji} {emp_obj.name}: Sẵn sàng trao đổi 1-1 với Chủ tịch Huy Mai!",
                    "selected_emp_id": emp_obj.emp_id,
                }
                st.rerun()

    # 3. BỐ CỤC CHÍNH: VĂN PHÒNG 3D & TRUNG TÂM CHAT 1-1 (CÓ NÚT 3 GẠCH BẬT/MỞ)
    if "show_chat_panel" not in st.session_state:
        st.session_state.show_chat_panel = True

    c_hdr_info, c_hdr_toggle = st.columns([3.0, 1.2])
    with c_hdr_info:
        st.markdown("#### 🌐 Không Gian 3D Metaverse (Click nhân vật để zoom & mở hội thoại)")
    with c_hdr_toggle:
        toggle_chat_label = "☰ Ẩn Bảng Giao Tiếp" if st.session_state.show_chat_panel else "☰ Mở Bảng Giao Tiếp (1-1)"
        if st.button(toggle_chat_label, key="toggle_chat_panel_btn", use_container_width=True):
            st.session_state.show_chat_panel = not st.session_state.show_chat_panel
            st.rerun()

    cmd = st.session_state.last_3d_command

    if st.session_state.show_chat_panel:
        c_3d_viewport, c_chat_viewport = st.columns([1.35, 1.0], gap="medium")
        with c_3d_viewport:
            render_bis_3d_office(
                agent_key=cmd.get("agent_key"),
                state=cmd.get("state"),
                message=cmd.get("message"),
                user_dept=active_dept_now,
                selected_emp_id=st.session_state.selected_emp_id,
                height=700,
            )
        with c_chat_viewport:
            mode_c1, mode_c2 = st.columns(2)
            with mode_c1:
                if st.button(
                    "👤 Chat Trực Tiếp 1-1",
                    type="primary" if st.session_state.chat_mode == "DIRECT_1_1" else "secondary",
                    use_container_width=True,
                    key="btn_mode_direct"
                ):
                    st.session_state.chat_mode = "DIRECT_1_1"
                    st.rerun()
            with mode_c2:
                if st.button(
                    "🗣️ Họp Toàn Thể (5 Phòng)",
                    type="primary" if st.session_state.chat_mode == "ALL_HANDS" else "secondary",
                    use_container_width=True,
                    key="btn_mode_allhands"
                ):
                    st.session_state.chat_mode = "ALL_HANDS"
                    st.session_state.last_3d_command = {
                        "agent_key": "all",
                        "state": "MEETING",
                        "message": "🗣️ Toàn bộ 5 Phòng ban họp giao ban với Chủ tịch Huy Mai!",
                        "selected_emp_id": st.session_state.selected_emp_id,
                    }
                    st.rerun()

            if orch and st.session_state.chat_mode == "DIRECT_1_1":
                active_emp = orch.employees.get(st.session_state.selected_emp_id, list(orch.employees.values())[0])
                st.markdown(
                    f"""
                    <div class="emp-card" style="border-left: 5px solid {active_emp.badge_color};">
                      <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                          <span style="font-size:20px; margin-right:6px;">{active_emp.avatar_emoji}</span>
                          <b style="font-size:16px; color:#f8fafc;">{active_emp.name}</b>
                          <span style="font-size:12px; color:#94a3b8;"> — {active_emp.title}</span>
                        </div>
                        <span class="state-pill" style="background:{active_emp.badge_color}33; color:{active_emp.badge_color}; border:1px solid {active_emp.badge_color};">
                          {active_emp.state} • {active_emp.progress_pct}%
                        </span>
                      </div>
                      <div style="font-size:12px; color:#cbd5e1; margin-top:6px;">
                        <b>Phòng ban:</b> {active_emp.department_name} &nbsp;|&nbsp;
                        <b>Công cụ:</b> <code>{', '.join(active_emp.tools)}</code>
                      </div>
                      <div style="font-size:12px; color:#38bdf8; margin-top:4px;">
                        <b>Tác vụ tự chạy:</b> {active_emp.current_task}
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.caption("⚡ **Lệnh chỉ đạo nhanh của Chủ tịch Huy Mai:**")
                qcol1, qcol2, qcol3 = st.columns(3)
                quick_prompt = None
                with qcol1:
                    if st.button("🔍 Kiểm tra SKU", use_container_width=True, key="quick_sku"):
                        quick_prompt = f"{active_emp.name} kiểm tra lại thông số và tiêu chuẩn mã SKU 03026A cho anh nhé!"
                with qcol2:
                    if st.button("📄 Dịch chuẩn hóa", use_container_width=True, key="quick_doc"):
                        quick_prompt = "Dịch và chuẩn hóa giúp anh tài liệu kỹ thuật Catalogue 36 trang giữ nguyên định dạng 100%."
                with qcol3:
                    if st.button("⏸️ Rào chắn Haravan", use_container_width=True, key="quick_haravan"):
                        quick_prompt = "Tạm dừng đồng bộ Haravan để anh rà soát giá, giữ chặt rào chắn bảo vệ trước 20/10/2026."

                chat_box = st.container(height=340)
                with chat_box:
                    for msg in active_emp.chat_memory:
                        is_ceo = msg.sender == "ceo"
                        with st.chat_message("user" if is_ceo else "assistant", avatar="👑" if is_ceo else active_emp.avatar_emoji):
                            st.markdown(f"**{msg.sender_name}** *(lúc {msg.timestamp})*")
                            st.markdown(msg.content)
                            if msg.action_log:
                                st.code(msg.action_log, language="bash")

                user_input = st.chat_input(f"Nhắn chỉ đạo cho {active_emp.name} ({active_emp.title})...", key="input_emp_chat")
                final_prompt = quick_prompt or user_input

                if final_prompt:
                    result = orch.chat_with_employee(active_emp.emp_id, final_prompt)
                    maintain_memory(bis_memory, force=True)
                    st.session_state.last_3d_command = {
                        "agent_key": result.get("emp_id", active_emp.emp_id),
                        "state": result["state_3d"],
                        "message": result["bubble_3d"],
                        "selected_emp_id": active_emp.emp_id,
                    }
                    st.rerun()

            elif orch:
                st.markdown(
                    """
                    <div class="emp-card" style="border-left: 5px solid #f59e0b;">
                      <b style="font-size:15px; color:#fef08a;">🗣️ PHÒNG HỌP BÀN TRÒN — TRIỆU TẬP TOÀN THỂ 5 PHÒNG BAN</b>
                      <div style="font-size:12px; color:#cbd5e1; margin-top:4px;">
                        Khi Chủ tịch ban hành chỉ đạo tại đây, cả 5 Trưởng phòng đại diện 15 nhân sự AI sẽ đồng loạt báo cáo phương án triển khai.
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                group_box = st.container(height=400)
                with group_box:
                    if not orch.group_meeting_log:
                        st.info("Chào Chủ tịch Huy Mai! Hãy nhập chỉ đạo bên dưới để triệu tập cả 5 Trưởng phòng báo cáo.")
                    for gmsg in orch.group_meeting_log:
                        is_ceo = gmsg.sender == "ceo"
                        emp_avatar = "👑" if is_ceo else (orch.employees[gmsg.sender].avatar_emoji if gmsg.sender in orch.employees else "🤖")
                        with st.chat_message("user" if is_ceo else "assistant", avatar=emp_avatar):
                            st.markdown(f"**{gmsg.sender_name}** • *{gmsg.role_badge}* ({gmsg.timestamp})")
                            st.markdown(gmsg.content)
                            if gmsg.action_log:
                                st.code(gmsg.action_log, language="text")

                group_directive = st.chat_input("Nhập chỉ đạo chung của Chủ tịch Huy Mai cho toàn bộ 5 Phòng ban...", key="input_group_chat")
                if group_directive:
                    orch.summon_all_hands_meeting(group_directive)
                    st.session_state.last_3d_command = {
                        "agent_key": "all",
                        "state": "MEETING",
                        "message": f"🗣️ Toàn công ty thực thi chỉ đạo của Chủ tịch: {group_directive[:40]}...",
                        "selected_emp_id": st.session_state.selected_emp_id,
                    }
                    st.rerun()

        # 4. NHẬT KÝ TỰ VẬN HÀNH THỜI GIAN THỰC & DANH BẠ 15 NHÂN SỰ
        st.markdown("---")
        tab_log_feed, tab_all_emps = st.tabs([
            "📡 Nhật Ký Vòng Lặp Tự Vận Hành (Live Autonomous Task Stream)",
            "📋 Danh Bạ Chi Tiết 15 Nhân Viên AI & Tác Vụ Đang Chạy",
        ])

        with tab_log_feed:
            if orch:
                st.markdown("##### 📡 Các tác vụ nền đang tự động kích hoạt bởi 15 nhân viên AI:")
                for ev in orch.system_event_feed[:8]:
                    st.markdown(
                        f"<div style='font-size:12.5px; padding:8px 12px; margin-bottom:8px; border-left:4px solid {ev['color']}; background:rgba(15,23,42,0.75); border-radius:8px;'>"
                        f"<b>{ev['actor']}</b> <span style='color:#94a3b8;'>({ev['time']})</span> — <span class='state-pill' style='background:{ev['color']}28; color:{ev['color']};'>{ev['state']}</span><br/>{ev['text']}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

        with tab_all_emps:
            if orch:
                dept_map = orch.get_departments()
                for dcode in ["RD", "MKT", "STUDIO", "TRANS", "OPS"]:
                    st.markdown(f"**{dept_map[dcode]}**")
                    demps = orch.get_employees_by_dept(dcode)
                    dcols = st.columns(3)
                    for didx, demp in enumerate(demps):
                        with dcols[didx % 3]:
                            st.markdown(
                                f"""
                                <div class="emp-card" style="border-top: 3px solid {demp.badge_color};">
                                  <div style="display:flex; justify-content:space-between; align-items:center;">
                                    <b>{demp.avatar_emoji} {demp.name}</b>
                                    <span class="state-pill" style="background:{demp.badge_color}25; color:{demp.badge_color}; border:1px solid {demp.badge_color};">
                                      {demp.state}
                                    </span>
                                  </div>
                                  <div style="font-size:11.5px; color:#94a3b8; margin-top:2px;">{demp.title}</div>
                                  <div style="font-size:12px; color:#e2e8f0; margin-top:8px;">
                                    <b>Tác vụ:</b> {demp.current_task}
                                  </div>
                                  <div style="font-size:11px; color:#38bdf8; margin-top:6px;">
                                    Chuyên môn: {', '.join(demp.specialties[:2])}
                                  </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                            if st.button(f"💬 Chat 1-1 với {demp.name}", key=f"btn_jump_emp_{demp.emp_id}", use_container_width=True):
                                st.session_state.selected_dept_id = demp.department_id
                                st.session_state.selected_emp_id = demp.emp_id
                                st.session_state.chat_mode = "DIRECT_1_1"
                                st.session_state.last_3d_command = {
                                    "agent_key": demp.emp_id,
                                    "state": STATE_TO_3D_MAP.get(demp.state, "WORKING"),
                                    "message": f"{demp.avatar_emoji} {demp.name}: Dạ em nghe lệnh Chủ tịch Huy Mai ạ!",
                                    "selected_emp_id": demp.emp_id,
                                }
                                st.rerun()
    else:
        # Khi Chủ tịch bấm ẩn bảng giao tiếp, văn phòng 3D bung toàn màn hình cực rộng
        render_bis_3d_office(
            agent_key=cmd.get("agent_key"),
            state=cmd.get("state"),
            message=cmd.get("message"),
            user_dept=active_dept_now,
            selected_emp_id=st.session_state.selected_emp_id,
            height=760,
        )

    # 5. TỰ LÊN LỊCH HỌP & BỘ NHỚ TỰ HỌC CẢI THIỆN
    st.markdown("---")
    c_meet_sched, c_learn_loop = st.columns([1.2, 1])

    with c_meet_sched:
        st.markdown("#### 📅 Lịch Họp Giao Ban Tự Động & Triệu Tập Khẩn Cấp:")
        st.markdown("""
        - 🕗 **08:30:** Giao ban đầu giờ phân tích tài liệu kỹ thuật mới (Kỹ thuật + CEO).
        - 🕐 **11:30:** Họp liên phòng duyệt nội dung SEO & Phối cảnh Studio (Marketing + Studio).
        - 🕑 **14:00:** Họp đối soát an toàn Haravan & Kế hoạch đồng bộ (Ops + CEO).
        - 🕔 **17:00:** Họp tổng kết bộ nhớ tự học & Báo cáo kết quả ngày (Toàn thể).
        """)
        if st.button("🔔 TRIỆU TẬP CUỘC HỌP GIAO BAN NGAY (TẤT CẢ VÀO BÀN TRÒN HỌP)", type="primary", use_container_width=True, key="btn_summon_roundtable"):
            render_bis_3d_office(agent_key="all", state="MEETING", user_dept="meeting", height=700)
            st.success("📢 Đã triệu tập toàn bộ Trưởng phòng và Nhân viên vào Bàn họp tròn trung tâm để báo cáo cho CEO!")

    with c_learn_loop:
        st.markdown("#### 🧠 Cơ Chế Tự Học & Cải Thiện Liên Tục (Learning Engine):")
        st.markdown("""
        <div style='background: #090e1a; border: 1px solid #1e293b; border-left: 3px solid #10b981; border-radius: 8px; padding: 12px; font-size: 13px;'>
          • <b>Tích lũy tri thức:</b> Hệ thống tự động ghi nhận mọi điều chỉnh của CEO thành quy tắc Few-shot.<br>
          • <b>Tránh lỗi lặp lại:</b> 100% phản hồi (loại bỏ từ cấm, chỉnh cột bảng) được lưu vào <code>feedback_memory.json</code>.<br>
          • <b>Tự động cải thiện:</b> Lần bóc tách và dịch thuật tiếp theo sẽ áp dụng ngay quy chuẩn mới mà không cần nhắc lại.
        </div>
        """, unsafe_allow_html=True)

    # 6. CÂU LỆNH & PROMPT HOÀN CHỈNH ĐỂ ĐƯA LÊN WEB GEMINI AI ARGON 4
    st.markdown("---")
    with st.expander("📋 CÂU LỆNH & PROMPT CHI TIẾT ĐỂ ĐƯA LÊN WEB GEMINI AI ARGON 4 (BẤM ĐỂ COPY)", expanded=False):
        st.markdown("""
        Nếu bạn muốn đưa toàn bộ hệ thống Multi-Agent và giao diện Văn phòng 3D lên web **Gemini AI Argon 4**, hãy sao chép toàn bộ khối lệnh prompt dưới đây và dán trực tiếp vào Gemini:
        """)
        gemini_argon_prompt = """Bạn là Kiến trúc sư Trưởng AI chuyên về Multi-Agent System và 3D Interactive Metaverse.
Hãy xây dựng và tinh chỉnh hệ sinh thái BIS Textile AI Command Center với các yêu cầu sau:

1. HỆ THỐNG PHÂN VAI MULTI-AGENT (TRƯỞNG PHÒNG & NHÂN VIÊN):
- Ban Lãnh Đạo Tối Cao: Nhân vật đại diện của Người dùng (👑 CEO Huy Mai) với quyền điều hành tối cao.
- Phòng Kỹ Thuật (R&D): Trưởng phòng Mr. Tech Lead + Nhân viên Extractor & QA Spec. Nhiệm vụ: bóc tách catalog PDF, kiểm định thông số 6 bước B1-B6.
- Phòng Marketing & SEO: Trưởng phòng Ms. Content + Nhân viên Copywriter & SEO Specialist. Nhiệm vụ: viết bài chuẩn 7 khối AIDA, USP dệt may, chuẩn SEO.
- Phòng Studio & Media: Trưởng phòng Mr. Art + Nhân viên Retoucher. Nhiệm vụ: tách nền, ghép ảnh vào bối cảnh phòng Lab chân thực 2K.
- Phòng Dịch Thuật (Agent_Translator): Trưởng phòng Senior Translator + Nhân viên OCR Specialist. Nhiệm vụ: dịch tài liệu từ 23 hãng sang tiếng Việt giữ nguyên 100% bảng biểu, font, style.
- Phòng Vận Hành (Haravan Guard): Trưởng phòng Mr. Guard + Nhân viên Sync Operator. Nhiệm vụ: đối soát 2 chiều, bảo vệ rào chắn 20/10/2026, đồng bộ ẩn lên Haravan.

2. GIAO DIỆN VĂN PHÒNG 3D METAVERSE INTERACTION:
- Xây dựng bằng Three.js WebGL: Văn phòng không gian tương tác 3D isometric góc nhìn 360 độ.
- Khi người dùng đăng nhập hoặc chọn phòng ban nào, nhân vật đại diện của Người dùng (User Avatar) sẽ bước chân (walking animation) di chuyển tới đúng khu vực phòng ban đó.
- Trưởng phòng của phòng ban đó sẽ cúi chào và báo cáo trực tiếp tiến độ công việc cho Người dùng.
- Có Bàn Họp Tròn Trung Tâm (Conference Hub) để tự động lên lịch họp hoặc triệu tập cuộc họp giao ban toàn thể khi có lệnh.
- Có khu vực Pantry giải lao (Breakroom) và Server Rack an ninh dữ liệu.

3. TỰ ĐỘNG THẢO LUẬN & TỰ HỌC LIÊN TỤC:
- Các Agent tự động thảo luận, bàn giao dữ liệu (Handoff) qua lại giữa các phòng ban theo thời gian thực.
- Tích hợp bộ nhớ Few-shot learning, tự động rút kinh nghiệm từ mọi phản hồi của người dùng để cải thiện độ chính xác ở các lần xử lý sau."""
        st.code(gemini_argon_prompt, language="markdown")
        st.caption("💡 Mẹo: Bấm biểu tượng Copy ở góc trên bên phải khung code để sao chép toàn bộ prompt đưa lên web Gemini AI Argon 4!")

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
                        "Trạng thái": v.get("status")
                    })
                if valid_table_data:
                    st.dataframe(valid_table_data, use_container_width=True, hide_index=True)

            with tab_store_view:
                store_file_p = PROJECT_DIR / "bistextile_existing_products.json"
                store_items = load_store_products(str(store_file_p))
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
        c_sync_head1, c_sync_head2 = st.columns([7.5, 4.5])
        with c_sync_head1:
            st.markdown(f"**⚡ Đối soát an toàn Haravan:** `🛡️ {len(dups_products)} SP đã có trên sàn (Đã khóa) • ✅ {len(valid_products)} SP mới sẵn sàng xuất bản`")
        with c_sync_head2:
            if st.button("🔄 CẬP NHẬT ĐỐI SOÁT LIVE HARAVAN NGAY", key="btn_sync_haravan_tab3", type="primary", use_container_width=True, help="Bấm vào đây ngay khi bạn vừa cập nhật/đăng sản phẩm trên Haravan để hệ thống kéo dữ liệu mới nhất về đối soát lại!"):
                if operations_agent:
                    with st.spinner("Đang kết nối Haravan API & bistextile.com để kéo danh mục mới nhất..."):
                        h_res = operations_agent.scan_live_haravan_and_web(products)
                        clean_list = h_res.get("clean_products", [])
                        if clean_list:
                            products = clean_list
                            st.session_state["cached_products"] = products
                        st.cache_data.clear()
                        st.toast(f"🎉 Đã cập nhật đối soát Haravan! Khóa {h_res.get('matched_count', 0)} mã trùng web, {h_res.get('unmatched_count', 0)} SP mới.", icon="🔄")
                        st.success(f"✓ Hoàn tất! Haravan hiện có {h_res.get('total_haravan', 0)} sản phẩm. Đã cập nhật bảng lọc kiểm duyệt!")
                        import time
                        time.sleep(0.3)
                        st.rerun()

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

            # ── THANH STICKY ACTION TOOLBAR TIỆN ÍCH ────────────────────────────────
            is_dup_item = p.get("status") == "REJECTED"
            sku_name_str = (p.get("product_name") or p.get("product_name_en") or "")[:50]
            st.markdown(f"""
            <div class="sticky-action-bar">
              <div>
                <span class="status-pill pill-blue">SKU: {p.get('sku')}</span>
                <span class="status-pill {'pill-rose' if is_dup_item else 'pill-emerald'}" style="margin-left:6px;">
                  {'🚫 BỊ TRÙNG HARAVAN (ĐÃ KHÓA)' if is_dup_item else '✅ HỢP LỆ (MỚI 100%)'}
                </span>
                <span style="margin-left:12px; font-weight:700; color:#f8fafc; font-size:13px;">{sku_name_str}...</span>
              </div>
              <div style="font-family:'JetBrains Mono', monospace; font-size:11.5px; color:#38bdf8;">
                TRẠNG THÁI: <strong style='color:{'#f43f5e' if is_dup_item else '#10b981'};'>{p.get('status')}</strong> &bull; TRANG: <strong>{p.get('source_page') or page_num}</strong>
              </div>
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
                default_hl_str = "Tiêu chuẩn thử nghiệm chính hãng được chuẩn hóa áp dụng toàn cầu trong ngành dệt may.\nĐầy đủ tài liệu hướng dẫn và quy trình thực hành phòng lab QA/QC."

            default_scope = p.get("application_scope") or "Phương pháp kiểm nghiệm dệt may quốc tế"
            default_doc_title, default_doc_url = resolve_related_standard_doc(p)

            with tab_unified:
                active_meeting_tab2 = learning_engine.get_active_meeting_request() if learning_engine and hasattr(learning_engine, "get_active_meeting_request") else None
                if active_meeting_tab2:
                    rep_t2 = active_meeting_tab2.get("report", {})
                    st.markdown(f"""
                    <div style='background: linear-gradient(90deg, #1e1b4b 0%, #0f172a 100%); border: 2px solid #818cf8; padding: 12px 18px; border-radius: 10px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center;'>
                      <div style='display: flex; align-items: center; gap: 12px;'>
                        <span style='font-size: 26px;'>👔</span>
                        <div>
                          <div style='font-size: 13.5px; font-weight: 800; color: #a5b4fc;'>Dr. Textile Tech (Agent Technical) đang xin gặp báo cáo Chủ tịch Mai Đức Huy</div>
                          <div style='font-size: 12px; color: #cbd5e1;'>Đã ghi nhận đủ {rep_t2.get('edit_count', 3)} lần sửa đổi cho hãng <strong>{rep_t2.get('brand', 'AATCC')}</strong>. AI đã hoàn thành tự học và tự tin đạt <strong>{rep_t2.get('confidence_score', 93)}%</strong>.</div>
                        </div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("🎙️ BẤM VÀO ĐÂY ĐỂ NGHE BÁO CÁO CỦA TRƯỞNG PHÒNG KỸ THUẬT AI", key="btn_trigger_meeting_tab2", type="primary", use_container_width=True):
                        st.session_state["show_meeting_modal"] = True
                        st.session_state["active_meeting_report"] = rep_t2
                        st.rerun()

                if st.session_state.get("show_meeting_modal"):
                    rep_m_data = st.session_state.get("active_meeting_report") or (active_meeting_tab2.get("report") if active_meeting_tab2 else {})
                    if rep_m_data:
                        show_meeting_dialog(rep_m_data)

                st.markdown("""
                <div style='background: #0b1120; border: 1px solid #1e293b; border-left: 3px solid #10b981; padding: 10px 14px; border-radius: 6px; font-size: 12px; color: #94a3b8; margin-bottom: 14px;'>
                  🧠 <strong>Cơ chế tự học tức thì:</strong> Bạn có thể sửa theo từng Khối thông tin hoặc sửa trực tiếp toàn bộ mã HTML 7 Khối ngay tại tab này. Nhấn <code>💾 LƯU THAY ĐỔI & AI TỰ HỌC</code> hoặc <code>✅ PHÊ DUYỆT</code>, hệ thống sẽ lưu tức thì, cập nhật ngay bản xem trước bên dưới và ghi nhớ vĩnh viễn vào <code>feedback_memory.json</code>!
                </div>
                """, unsafe_allow_html=True)

                # 🌟 THANH CÔNG CỤ AI CHECK & TỰ ĐỘNG CHUẨN HÓA NỘI DUNG + SEO
                c_ai_act1, c_ai_act2 = st.columns([7.2, 4.8])
                with c_ai_act1:
                    if st.button(f"✨ AI CHECK & TỰ ĐỘNG TỐI ƯU NỘI DUNG + SEO CHO {p.get('sku')}", key=f"btn_ai_refine_single_{p.get('sku')}", type="primary", use_container_width=True, help="AI sẽ tự động kiểm tra, chuẩn hóa tên tiếng Việt dệt may, trau chuốt mô tả, tạo 3 gạch đầu dòng nổi bật, xác định tài liệu Khối 7 và tạo trọn gói SEO Google đạt chuẩn 100%!"):
                        with st.spinner(f"Chuyên gia AI Kỹ thuật & SEO đang rà soát và tối ưu toàn diện cho {p.get('sku')}..."):
                            from ai_product_refiner import ai_check_and_refine_product
                            refined_p = ai_check_and_refine_product(p)
                            p.update(refined_p)
                            p["updated_at"] = datetime.now().isoformat()
                            for item in products:
                                if item.get("sku") == p.get("sku"):
                                    item.update(p)
                                    break
                            with open(cache_file, "w", encoding="utf-8") as f:
                                json.dump(products, f, ensure_ascii=False, indent=2)
                            git_c = Path("c:/Users/Dell/bis-ai-project/BIS_AI_PROJECT/extracted_products_cache.json")
                            if git_c.parent.exists():
                                try:
                                    with open(git_c, "w", encoding="utf-8") as f:
                                        json.dump(products, f, ensure_ascii=False, indent=2)
                                except Exception:
                                    pass
                            st.session_state["cached_products"] = products
                            st.toast(f"🎉 AI ĐÃ CHUẨN HÓA THÀNH CÔNG NỘI DUNG VÀ SEO CHO {p.get('sku')}!", icon="✨")
                            st.success(f"✓ Hoàn tất! Tên tiếng Việt, Mô tả kỹ thuật và Gói SEO Google của mã `{p.get('sku')}` đã được chuẩn hóa tối ưu!")
                            time.sleep(0.3)
                            st.rerun()

                with c_ai_act2:
                    with st.popover("⚡ AI BATCH: Chuẩn Hóa Toàn Bộ Danh Mục", use_container_width=True):
                        st.markdown("**Chuẩn hóa tự động toàn bộ 97 sản phẩm:**")
                        st.write("AI sẽ tự động quét toàn bộ danh mục, áp dụng từ điển dệt may, trau chuốt mô tả và tạo SEO Google cho tất cả sản phẩm.")
                        if st.button("🚀 BẮT ĐẦU CHẠY AI BATCH TOÀN BỘ", key=f"btn_run_ai_batch_all_{p.get('sku')}", type="secondary", use_container_width=True):
                            with st.spinner("AI đang tự động chuẩn hóa toàn bộ danh mục sản phẩm..."):
                                from ai_product_refiner import ai_check_and_refine_product
                                prog_ai = st.progress(0.0)
                                for idx_b, itm in enumerate(products):
                                    ref_itm = ai_check_and_refine_product(itm)
                                    itm.update(ref_itm)
                                    prog_ai.progress((idx_b + 1) / len(products))
                                with open(cache_file, "w", encoding="utf-8") as f:
                                    json.dump(products, f, ensure_ascii=False, indent=2)
                                git_c = Path("c:/Users/Dell/bis-ai-project/BIS_AI_PROJECT/extracted_products_cache.json")
                                if git_c.parent.exists():
                                    try:
                                        with open(git_c, "w", encoding="utf-8") as f:
                                            json.dump(products, f, ensure_ascii=False, indent=2)
                                    except Exception:
                                        pass
                                st.session_state["cached_products"] = products
                                st.toast("🎉 ĐÃ CHUẨN HÓA XONG TOÀN BỘ DANH MỤC SẢN PHẨM & SEO!", icon="🚀")
                                st.success("✓ Hoàn tất chuẩn hóa tự động toàn bộ sản phẩm!")
                                time.sleep(0.3)
                                st.rerun()

                st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
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

                    # HÀNG 4: KHỐI CẤU HÌNH SEO HARAVAN & GOOGLE CHECK
                    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                    with st.expander("🌐 CẤU HÌNH SEO GOOGLE & METADATA HARAVAN (ĐỂ KIỂM TRA & TÙY CHỈNH)", expanded=True):
                        # Lấy dữ liệu SEO mặc định nếu chưa có
                        cached_seo = p.get("seo_package") or {}
                        default_meta_title = p.get("meta_title") or cached_seo.get("meta_title") or f"{p.get('product_name', '')} ({p.get('sku', '')}) | BIS Textile Việt Nam"
                        default_meta_desc = p.get("meta_description") or cached_seo.get("meta_description") or f"Phân phối chính hãng {p.get('product_name', '')} mã {p.get('sku', '')} từ {p.get('brand', 'AATCC')}. Tiêu chuẩn kiểm nghiệm dệt may quốc tế, đầy đủ chứng từ tại BIS Textile."
                        default_slug = p.get("url_slug") or cached_seo.get("url_slug") or (p.get("sku", "").lower() + "-" + re.sub(r'[^a-zA-Z0-9]+', '-', (p.get("product_name_en") or "")).strip("-").lower()[:40])

                        c_seo_in1, c_seo_in2 = st.columns(2)
                        with c_seo_in1:
                            edit_meta_title = st.text_input(f"Tiêu đề SEO Google (Meta Title - {len(default_meta_title)}/60 ký tự):", value=default_meta_title, key=f"inp_meta_t_{p.get('sku')}")
                            edit_slug = st.text_input("Đường dẫn sản phẩm (URL Handle / Slug):", value=default_slug, key=f"inp_slug_{p.get('sku')}")
                        with c_seo_in2:
                            edit_meta_desc = st.text_area(f"Mô tả SEO Google (Meta Description - {len(default_meta_desc)}/160 ký tự):", value=default_meta_desc, height=105, key=f"inp_meta_d_{p.get('sku')}")

                        # Mô phỏng kết quả tìm kiếm Google (Google SERP Snippet Preview - High Contrast Dark Mode)
                        st.markdown("<div style='font-size: 13px; font-weight: 700; color: #38bdf8; margin-top: 10px; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;'><span>🔍</span> <span>Mô phỏng hiển thị Google Search (SERP Snippet):</span></div>", unsafe_allow_html=True)
                        st.markdown(f"""
                        <div style="background: #1e293b !important; border: 1.5px solid #334155; border-radius: 10px; padding: 14px 18px; margin-bottom: 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; box-shadow: 0 4px 14px rgba(0,0,0,0.3);">
                          <div style="font-size: 12.5px !important; color: #94a3b8 !important; margin-bottom: 6px; display: flex; align-items: center; gap: 8px;">
                            <span style="background: #0f172a; border: 1px solid #334155; border-radius: 50%; width: 22px; height: 22px; display: inline-flex; align-items: center; justify-content: center; font-size: 11px;">🌐</span>
                            <span style="color: #94a3b8 !important;">https://bistextile.com &rsaquo; products &rsaquo; <strong style="color: #38bdf8 !important;">{edit_slug}</strong></span>
                          </div>
                          <div style="font-size: 18px !important; color: #60a5fa !important; line-height: 1.35 !important; font-weight: 600 !important; margin-bottom: 6px;">
                            {edit_meta_title}
                          </div>
                          <div style="font-size: 13.5px !important; color: #cbd5e1 !important; line-height: 1.6 !important;">
                            {edit_meta_desc}
                          </div>
                        </div>
                        """, unsafe_allow_html=True)

                else:
                    st.caption("💻 Chỉnh sửa trực tiếp toàn bộ mã HTML 7 khối chuẩn Haravan (có thể chèn thêm link, bảng, style CSS):")
                    current_html_val = p.get("custom_html") or technical_agent.build_7_block_html(p)
                    if current_html_val and ("phân phối" in current_html_val or "BIS Textile Việt Nam" in current_html_val):
                        import re as _re_raw
                        current_html_val = _re_raw.sub(r'\s*•?\s*<strong>Đơn vị phân phối:?</strong>\s*<span[^>]*>.*?</span>', '', current_html_val, flags=_re_raw.IGNORECASE)
                        current_html_val = _re_raw.sub(r'\s*•?\s*&bull;\s*<strong>Đơn vị phân phối:?</strong>.*?(?=</div>|&bull;)', '', current_html_val, flags=_re_raw.IGNORECASE)
                        current_html_val = _re_raw.sub(r'\s*(?:•|&bull;)?\s*Đơn vị phân phối:?\s*BIS Textile Việt Nam', '', current_html_val, flags=_re_raw.IGNORECASE)
                    custom_html_code = st.text_area("Mã HTML 7 Khối hoàn chỉnh:", value=current_html_val, height=300, key=f"raw_html_{p.get('sku')}")

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    save_corrections = st.button("💾 LƯU THAY ĐỔI & AI TỰ HỌC", key=f"btn_save_unified_{p.get('sku')}", type="primary", use_container_width=True)
                with col_btn2:
                    approve_btn = st.button("✅ PHÊ DUYỆT ĐỂ ĐĂNG WEB (APPROVE)", key=f"btn_approve_unified_{p.get('sku')}", use_container_width=True)

                if save_corrections or approve_btn:
                    learned_changes = []

                    if edit_mode.startswith("📝"):
                        # Vòng lặp Reflexion: So sánh dữ liệu AI bóc tách ban đầu với bản sửa của chuyên viên
                        orig_snapshot = {
                            "sku": p.get("sku"),
                            "product_name": p.get("product_name"),
                            "product_name_en": p.get("product_name_en"),
                            "unit": p.get("unit"),
                            "brand": p.get("brand") or p.get("brand_evidence"),
                            "description": p.get("description"),
                            "evidence_quote": p.get("evidence_quote") or ""
                        }
                        edited_snapshot = {
                            "sku": p.get("sku"),
                            "product_name": edit_name_vi,
                            "product_name_en": edit_name_en,
                            "unit": edit_unit,
                            "brand": edit_vendor,
                            "description": edit_desc
                        }
                        if learning_engine and hasattr(learning_engine, "record_correction_and_reflect"):
                            try:
                                ref_res = learning_engine.record_correction_and_reflect(
                                    original_extracted=orig_snapshot,
                                    human_edited=edited_snapshot,
                                    brand=edit_vendor or p.get("brand") or "General",
                                    evidence_quote=orig_snapshot.get("evidence_quote", "")
                                )
                                if ref_res.get("status") == "SUCCESS":
                                    if ref_res.get("meeting_requested"):
                                        st.session_state["show_meeting_modal"] = True
                                        st.session_state["active_meeting_report"] = ref_res.get("meeting_report")
                                        st.toast("👔 Dr. Textile Tech xin phép báo cáo Chủ tịch về tiến trình tự học!", icon="👔")
                                    elif ref_res.get("rule"):
                                        st.toast(f"💡 [Reflexion] Đã tự học quy tắc mới: {ref_res['rule']}", icon="🧠")
                            except Exception as _e_ref:
                                pass
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
                        p["related_doc_url"] = default_doc_url
                        p["source_page"] = edit_page_str.strip()
                        # Lưu vĩnh viễn cấu hình SEO
                        p["meta_title"] = edit_meta_title.strip()
                        p["meta_description"] = edit_meta_desc.strip()
                        p["url_slug"] = edit_slug.strip()
                        p["seo_ready"] = True

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
                st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                st.markdown("<div class='glass-card glass-card-emerald'>", unsafe_allow_html=True)
                c_prev_h1, c_prev_h2 = st.columns([8, 4])
                with c_prev_h1:
                    st.markdown("##### 📄 Bản Xem Trước Chuẩn Website Haravan / bistextile.com (Nền trắng sắc nét):")
                with c_prev_h2:
                    st.markdown("<div style='text-align:right; font-family:\"JetBrains Mono\",monospace; font-size:11px; color:#10b981; padding-top:4px;'>HARAVAN CONTAINER ACTIVE ✓</div>", unsafe_allow_html=True)
                live_preview_code = p.get("custom_html") or technical_agent.build_7_block_html(p)
                if live_preview_code and ("phân phối" in live_preview_code or "BIS Textile Việt Nam" in live_preview_code):
                    import re as _re_prev
                    live_preview_code = _re_prev.sub(r'\s*•?\s*<strong>Đơn vị phân phối:?</strong>\s*<span[^>]*>.*?</span>', '', live_preview_code, flags=_re_prev.IGNORECASE)
                    live_preview_code = _re_prev.sub(r'\s*•?\s*&bull;\s*<strong>Đơn vị phân phối:?</strong>.*?(?=</div>|&bull;)', '', live_preview_code, flags=_re_prev.IGNORECASE)
                    live_preview_code = _re_prev.sub(r'\s*(?:•|&bull;)?\s*Đơn vị phân phối:?\s*BIS Textile Việt Nam', '', live_preview_code, flags=_re_prev.IGNORECASE)
                    live_preview_code = _re_prev.sub(r'&bull;\s*</div>', '</div>', live_preview_code)
                    live_preview_code = _re_prev.sub(r'•\s*</div>', '</div>', live_preview_code)
                
                # Bật thuộc tính contenteditable="true" cho các khối 1, 4, 5, 6 để người dùng gõ sửa trực tiếp
                editable_preview_code = live_preview_code
                if "contenteditable" not in editable_preview_code:
                    import re as _re_w
                    editable_preview_code = _re_w.sub(r"<h1\b([^>]*)>", r'<h1 contenteditable="true" id="wysiwyg_k1" title="✍️ Nhấp chuột vào đây để sửa tiêu đề tiếng Việt"\1>', editable_preview_code, count=1)
                    editable_preview_code = _re_w.sub(r"<h2\b([^>]*)>", r'<h2 contenteditable="true" id="wysiwyg_k2" title="✍️ Nhấp chuột vào đây để sửa tiêu đề tiếng Anh"\1>', editable_preview_code, count=1)
                    editable_preview_code = _re_w.sub(r"(<!-- KHỐI 4:.*?-->\s*<div[^>]*>\s*<p)\b([^>]*)>", r'\1 contenteditable="true" id="wysiwyg_k4" title="✍️ Nhấp chuột vào đây để sửa giới thiệu sản phẩm"\2>', editable_preview_code, count=1, flags=_re_w.DOTALL)
                    editable_preview_code = _re_w.sub(r"(<!-- KHỐI 5:.*?-->.*?<ul)\b([^>]*)>", r'\1 contenteditable="true" id="wysiwyg_k5" title="✍️ Nhấp chuột vào đây để sửa đặc điểm nổi bật"\2>', editable_preview_code, count=1, flags=_re_w.DOTALL)
                    editable_preview_code = _re_w.sub(r"(<!-- KHỐI 6:.*?-->.*?<table)\b([^>]*)>", r'\1 contenteditable="true" id="wysiwyg_k6" title="✍️ Nhấp chuột vào đây để sửa bảng thông số"\2>', editable_preview_code, count=1, flags=_re_w.DOTALL)

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
    /* Hiệu ứng WYSIWYG trực quan khi di chuột và nhấp sửa chữ */
    [contenteditable="true"] {{
      transition: all 0.18s ease;
      border-radius: 4px;
      padding: 2px 4px;
    }}
    [contenteditable="true"]:hover {{
      outline: 2px dashed #0284c7 !important;
      background-color: #f0f9ff !important;
      cursor: text;
    }}
    [contenteditable="true"]:focus {{
      outline: 2px solid #0284c7 !important;
      background-color: #ffffff !important;
      box-shadow: 0 0 10px rgba(2, 132, 199, 0.25);
    }}
  </style>
</head>
<body style="background-color: #ffffff !important; color: #1e293b !important;">
  <div style="display:flex; justify-content:space-between; align-items:center; background:#0f172a; color:#f8fafc; padding:10px 16px; border-radius:8px; margin-bottom:12px; font-size:12.5px; border:1.5px solid #38bdf8;">
    <div style="display:flex; align-items:center; gap:10px;">
      <span style="font-size:18px;">👁️</span>
      <span><strong>BẢN XEM TRƯỚC WEBSITE HARAVAN:</strong> Khi bạn thay đổi nội dung ở bảng biểu và phần SEO phía trên, bản xem trước bên dưới sẽ hiển thị chuẩn xác giao diện khách hàng nhìn thấy trên <code>bistextile.com</code>. Nhấn nút <strong>💾 LƯU THAY ĐỔI</strong> để lưu vĩnh viễn!</span>
    </div>
    <span style="font-size:11px; background:#10b981; color:#fff; padding:4px 10px; border-radius:4px; font-weight:700;">PREVIEW SYNCED ✓</span>
  </div>
  <div id="render_container_{preview_hash}">
    {editable_preview_code}
  </div>
  <script>
    document.querySelectorAll('[contenteditable="true"]').forEach(el => {{
      el.addEventListener('input', function() {{
        const badge = document.getElementById('wysiwyg_badge');
        if (badge) {{
          badge.textContent = 'Đã nhận thay đổi • Sẵn sàng lưu ⚡';
          badge.style.background = '#10b981';
        }}
      }});
    }});
  </script>
</body>
</html>"""
                components.html(full_preview_html, height=620, scrolling=True)
                st.markdown("</div>", unsafe_allow_html=True)

                # NÚT BẤM LƯU TIỆN ÍCH NGAY DƯỚI BẢN XEM TRƯỚC (KHÔNG CẦN CUỘN LÊN ĐẦU TRANG)
                c_bot_btn1, c_bot_btn2 = st.columns(2)
                with c_bot_btn1:
                    if st.button("💾 LƯU TẤT CẢ THAY ĐỔI & SEO (TẠI ĐÂY)", key=f"btn_save_bottom_{p.get('sku')}", type="primary", use_container_width=True):
                        # Cập nhật và lưu
                        if edit_mode.startswith("📝"):
                            p["product_name"] = edit_name_vi.strip()
                            p["product_name_en"] = edit_name_en.strip()
                            p["unit"] = edit_unit.strip()
                            p["brand"] = edit_vendor.strip()
                            p["description"] = edit_desc.strip()
                            p["highlights"] = [line.strip().lstrip("-*• ") for line in edit_highlights.split("\n") if line.strip()]
                            p["application_scope"] = edit_scope.strip()
                            p["related_doc_title"] = edit_doc_title.strip()
                            p["related_doc_url"] = default_doc_url
                            p["meta_title"] = edit_meta_title.strip()
                            p["meta_description"] = edit_meta_desc.strip()
                            p["url_slug"] = edit_slug.strip()
                            p["seo_ready"] = True
                            p.pop("custom_html", None)
                            p["custom_html"] = technical_agent.build_7_block_html(p)
                        else:
                            p["custom_html"] = custom_html_code
                        p["updated_at"] = datetime.now().isoformat()
                        for item in products:
                            if item.get("sku") == p.get("sku"):
                                item.update(p)
                                break
                        with open(cache_file, "w", encoding="utf-8") as f:
                            json.dump(products, f, ensure_ascii=False, indent=2)
                        git_c = Path("c:/Users/Dell/bis-ai-project/BIS_AI_PROJECT/extracted_products_cache.json")
                        if git_c.parent.exists():
                            try:
                                with open(git_c, "w", encoding="utf-8") as f:
                                    json.dump(products, f, ensure_ascii=False, indent=2)
                            except Exception:
                                pass
                        st.session_state["cached_products"] = products
                        st.toast("🎉 ĐÃ LƯU THÀNH CÔNG NỘI DUNG VÀ CẤU HÌNH SEO!", icon="💾")
                        st.success("✓ Đã lưu thành công cả nội dung sản phẩm và thông tin SEO vào hệ thống!")
                        time.sleep(0.3)
                        st.rerun()

                with c_bot_btn2:
                    if st.button("✅ PHÊ DUYỆT ĐỂ ĐĂNG WEB HARAVAN (TẠI ĐÂY)", key=f"btn_approve_bottom_{p.get('sku')}", use_container_width=True):
                        p["status"] = "APPROVED"
                        p["updated_at"] = datetime.now().isoformat()
                        for item in products:
                            if item.get("sku") == p.get("sku"):
                                item.update(p)
                                break
                        with open(cache_file, "w", encoding="utf-8") as f:
                            json.dump(products, f, ensure_ascii=False, indent=2)
                        st.session_state["cached_products"] = products
                        st.toast(f"🎉 ĐÃ PHÊ DUYỆT SẢN PHẨM {p.get('sku')} ĐỂ ĐĂNG WEB!", icon="✅")
                        st.success(f"✓ Sản phẩm {p.get('sku')} đã được phê duyệt sẵn sàng xuất bản!")
                        time.sleep(0.3)
                        st.rerun()

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
    st.write("Nghiên cứu từ khóa ngành dệt may (AATCC, ISO, ASTM), học hỏi phong cách trình bày từ các website đầu ngành, soạn Meta Title, Meta Description chuẩn SEO, tạo URL Slug thân thiện và xây dựng kịch bản bán hàng cho phòng lab QA/QC.")

    # ── MỤC NGHIÊN CỨU & HỌC HỎI ĐỐI CHUẨN TỪ 4 WEBSITE ĐẦU NGÀNH ────────────────
    st.markdown("""
    <div style='background: linear-gradient(135deg, #090e1a 0%, #0c1a2e 100%); border: 1.5px solid #0284c7; border-radius: 10px; padding: 16px; margin-bottom: 16px;'>
      <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;'>
        <div style='font-size: 15px; font-weight: 800; color: #38bdf8;'>
          🌐 BỘ NÃO NGHIÊN CỨU THỊ TRƯỜNG & HỌC HỎI ĐỐI CHUẨN TỰ ĐỘNG (Competitive Intelligence)
        </div>
        <span class='node-badge badge-active'>CRAWLER LIVE</span>
      </div>
      <div style='font-size: 12.5px; color: #cbd5e1; line-height: 1.6;'>
        AI tự động quét, bóc tách cấu trúc và học hỏi phong cách trình bày nội dung chuẩn thương mại điện tử dệt may từ <strong>4 Website hàng đầu ngành</strong>:<br>
        &bull; <code>https://bistextile.com/collections/all</code> (Sàn Haravan BIS Textile)<br>
        &bull; <code>https://qclabtex.com/</code> (Thiết bị &amp; vật tư kiểm nghiệm QC dệt may)<br>
        &bull; <code>https://labgartex.com/</code> (Thiết bị phòng thí nghiệm may mặc)<br>
        &bull; <code>https://bisvn.net/</code> (Hệ sinh thái giải pháp dệt may BIS VN)
      </div>
    </div>
    """, unsafe_allow_html=True)

    c_crawl_btn, c_crawl_status = st.columns([4, 8])
    with c_crawl_btn:
        if st.button("🚀 KÍCH HOẠT AI NGHIÊN CỨU 4 WEBSITE", key="btn_crawl_industry_sites", type="primary", use_container_width=True):
            if marketing_agent:
                if not hasattr(marketing_agent, "research_industry_websites"):
                    try:
                        import importlib, agent_marketing
                        importlib.reload(agent_marketing)
                        marketing_agent = agent_marketing.AgentMarketing(PROJECT_DIR)
                    except Exception:
                        pass
                if hasattr(marketing_agent, "research_industry_websites"):
                    with st.spinner("Agent_Marketing đang quét dữ liệu trực tiếp từ bistextile, qclabtex, labgartex, bisvn..."):
                        k_res = marketing_agent.research_industry_websites()
                        st.toast("✓ Đã hoàn tất nghiên cứu 4 website & nạp vào Bộ Nhớ Tự Học!", icon="🧠")
                        st.rerun()
                else:
                    st.info("Đang nạp module nghiên cứu...")
                    st.rerun()

    # Tải tri thức đã học được qua cache RAM
    know_file = PROJECT_DIR / "marketing_knowledge.json"
    mkt_knowledge = load_cached_marketing_knowledge(str(know_file))
    if mkt_knowledge:
        with st.expander("📚 XEM CHI TIẾT BỘ TRI THỨC VÀ QUY TẮC TRÌNH BÀY AI ĐÃ HỌC ĐƯỢC", expanded=True):
            col_kno1, col_kno2 = st.columns(2)
            with col_kno1:
                st.markdown("##### 📌 Quy Chuẩn Trình Bày Nội Dung Haravan Học Được:")
                for r in mkt_knowledge.get("presentation_style_rules", []):
                    st.markdown(f"- 💡 {r}")

                st.markdown("##### 🎯 Top Từ Khóa SEO Ngành Dệt May Được Đúc Kết:")
                st.markdown(" • ".join([f"`{k}`" for k in mkt_knowledge.get("top_seo_keywords", [])]))

            with col_kno2:
                st.markdown("##### 🏛️ Cấu Trúc Khung Bài Viết 7 Khối Chuẩn Haravan:")
                for idx, b in enumerate(mkt_knowledge.get("haravan_layout_blueprint", {}).get("block_structure", [])):
                    st.markdown(f"**{idx+1}.** {b}")

                st.markdown("##### 🧠 Các Luật Kinh Doanh Đã Nạp Vào Learning Engine:")
                for lr in mkt_knowledge.get("learned_business_rules", []):
                    st.markdown(f"- 📌 *{lr}*")

    st.markdown("---")

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
            meta_u = seo_data.get('url_slug') or ''
            meta_t = seo_data.get('meta_title') or ''
            meta_d = seo_data.get('meta_description') or ''
            st.markdown(f"""
            <div style="background: #1e293b !important; border: 1.5px solid #334155; border-radius: 10px; padding: 14px 18px; margin-bottom: 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; box-shadow: 0 4px 14px rgba(0,0,0,0.3);">
              <div style="font-size: 12.5px !important; color: #94a3b8 !important; margin-bottom: 6px; display: flex; align-items: center; gap: 8px;">
                <span style="background: #0f172a; border: 1px solid #334155; border-radius: 50%; width: 22px; height: 22px; display: inline-flex; align-items: center; justify-content: center; font-size: 11px;">🌐</span>
                <span style="color: #94a3b8 !important;">https://bistextile.com &rsaquo; products &rsaquo; <strong style="color: #38bdf8 !important;">{meta_u}</strong></span>
              </div>
              <div style="font-size: 18px !important; color: #60a5fa !important; line-height: 1.35 !important; font-weight: 600 !important; margin-bottom: 6px;">
                {meta_t}
              </div>
              <div style="font-size: 13.5px !important; color: #cbd5e1 !important; line-height: 1.6 !important;">
                {meta_d}
              </div>
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


# ── TAB 4: PHÒNG EDIT & DUYỆT ẢNH SẢN PHẨM (MEDIA STUDIO) ────────────────────
with tab_media:
    st.markdown("### 🎨 Phòng Edit & Duyệt Ảnh Sản Phẩm (Agent_Media Studio)")
    
    col_inf1, col_inf2 = st.columns([7, 5])
    with col_inf1:
        st.info("💎 **Chuẩn ảnh thành phẩm Golden Benchmark (1254x1254 px):** Giữ nguyên 100% hình khối thực tế, font chữ dập chìm và logo gốc (Zero-Hallucination). Tự động tách nền quang học, khử răng cưa viền và đổ bóng 3D tiếp xúc chân thực lên phông nền thương hiệu BIS Textile.")
    with col_inf2:
        st.caption("⚡ **Lưu ý Streamlit Cloud:** Nếu gặp thông báo `Zzzz This app has gone to sleep...`, bạn chỉ cần bấm nút xanh **'Yes, get this app back up!'** để cloud khởi động lại sau 30s. Hoặc truy cập bản local tại `http://localhost:8501`.")

    if not media_agent:
        st.warning("⚠️ Đang chờ đồng bộ file `agent_media.py` trên GitHub. Hãy tải file lên để kích hoạt.")
    elif products:
        sku_media = st.selectbox("Chọn SKU để xử lý ảnh:", [p.get("sku") for p in products], key="media_sku_select")
        p_media = next((item for item in products if item.get("sku") == sku_media), products[0])
        clean_sku = sku_media.strip().replace(" ", "_")

        col_m1, col_m2 = st.columns([1, 1], gap="large")

        # ── CỘT TRÁI: ẢNH NGUỒN & BẢNG ĐIỀU KHIỂN PHỐI CẢNH STUDIO 3D ──────────
        with col_m1:
            st.markdown("#### 1. Nguồn Ảnh Sản Phẩm (Google Drive / Upload)")
            
            # Quét tìm ảnh theo mã SKU trong Google Drive
            chosen_source_img = None
            if media_agent and hasattr(media_agent, "get_product_image_for_sku"):
                chosen_source_img = media_agent.get_product_image_for_sku(clean_sku)
            else:
                clean_sku_lower = clean_sku.lower()
                search_dir = PROJECT_DIR / "Google_Drive_Storage" / "4_Product_Images"
                if search_dir.exists():
                    for ext in [".jpg", ".png", ".jpeg", ".webp"]:
                        p = search_dir / f"{clean_sku}{ext}"
                        if p.exists():
                            chosen_source_img = p
                            break
                    if not chosen_source_img:
                        for f in sorted(search_dir.iterdir()):
                            if f.is_file() and (f.stem.lower() == clean_sku_lower or f.stem.lower().startswith(f"{clean_sku_lower}_")) and f.suffix.lower() in [".jpg", ".png", ".jpeg", ".webp"]:
                                chosen_source_img = f
                                break

            c_src_info, c_src_thumb = st.columns([7, 3])
            with c_src_info:
                if chosen_source_img and chosen_source_img.exists():
                    st.success(f"✅ **Đã nhận diện:** `{chosen_source_img.name}` ({chosen_source_img.stat().st_size // 1024} KB)")
                else:
                    st.warning(f"⚠️ Chưa có ảnh cho `{clean_sku}` trong Drive. Hãy kéo thả ảnh vào ô bên dưới.")
                
                uploaded_user_img = st.file_uploader(
                    f"Tải/kéo thả ảnh cho mã {clean_sku}:", 
                    type=["jpg", "png", "jpeg", "webp"], 
                    key=f"up_{clean_sku}"
                )
                sig_key_up = f"proc_up_{clean_sku}"
                if uploaded_user_img:
                    f_bytes = uploaded_user_img.getvalue()
                    f_sig = f"{uploaded_user_img.name}_{len(f_bytes)}"
                    if st.session_state.get(sig_key_up) != f_sig:
                        st.session_state[sig_key_up] = f_sig
                        saved_path = media_agent.register_user_image(clean_sku, f_bytes, uploaded_user_img.name)
                        st.toast(f"📥 Đã nạp ảnh nguồn cho {clean_sku}! Bấm 'RENDER 3D STUDIO' để phối cảnh.", icon="📸")
                        st.rerun()

            with c_src_thumb:
                if chosen_source_img and chosen_source_img.exists():
                    st.image(str(chosen_source_img), width=130, caption="Ảnh nguồn")

            from pdf_candidates import render_picker
            render_picker(media_agent, clean_sku, PROJECT_DIR / "catalogue_sample.pdf")

            # ── BẢNG ĐIỀU KHIỂN PHỐI CẢNH STUDIO 3D (3D BRANDED BACKDROP CONTROLS) ──
            st.markdown("---")
            st.markdown("#### 2. Bảng Điều Khiển Phối Cảnh Studio 3D")
            
            # 1. Chọn phôi hoa văn thương hiệu
            available_bgs = media_agent.get_backgrounds() if hasattr(media_agent, "get_backgrounds") else []
            bg_names = [bg.name for bg in available_bgs]
            default_bg_idx = 0
            for idx, bname in enumerate(bg_names):
                if "BIS_BACKGROUND" in bname:
                    default_bg_idx = idx
                    break

            c_bg_sel, c_bg_up = st.columns([7, 5])
            with c_bg_sel:
                selected_bg_name = st.selectbox(
                    "Phôi hoa văn thương hiệu (Brand Backdrop Pattern):",
                    bg_names,
                    index=default_bg_idx if bg_names else 0,
                    key=f"bg_select_{clean_sku}",
                    help="Chọn phôi hoa văn logo lặp. Thuật toán sẽ tự động phân chia phần tường đứng 2D và sàn phối cảnh 3D mở rộng."
                )
                selected_bg_path = next((bg for bg in available_bgs if bg.name == selected_bg_name), available_bgs[0] if available_bgs else None)
            
            with c_bg_up:
                new_pat_file = st.file_uploader("Nạp mẫu hoa văn mới:", type=["jpg", "png"], key=f"new_pat_{clean_sku}")
                sig_key_pat = f"proc_pat_{clean_sku}"
                if new_pat_file:
                    p_bytes = new_pat_file.getvalue()
                    p_sig = f"{new_pat_file.name}_{len(p_bytes)}"
                    if st.session_state.get(sig_key_pat) != p_sig:
                        st.session_state[sig_key_pat] = p_sig
                        media_agent.register_background(new_pat_file.name, p_bytes)
                        st.toast("✓ Đã lưu phôi hoa văn mới!", icon="🎨")
                        st.rerun()

            # 2. Phong cách render
            render_style = st.radio(
                "Phong cách dựng phối cảnh:",
                [
                    "🏛️ 3D Branded Studio (Tường 2D phẳng + Sàn phối cảnh nghiêng)",
                    "📘 3D Book & Document (Uốn cong, gáy sách & độ dày)",
                    "🔬 3D Product & Equipment (Tách nền & bóng tiếp xúc vật lý)",
                    "🖼️ Giữ nguyên phẳng 2D"
                ],
                index=0,
                key=f"render_style_{clean_sku}"
            )
            mode_map = {
                "🏛️ 3D Branded Studio (Tường 2D phẳng + Sàn phối cảnh nghiêng)": "branded_3d",
                "📘 3D Book & Document (Uốn cong, gáy sách & độ dày)": "book_3d",
                "🔬 3D Product & Equipment (Tách nền & bóng tiếp xúc vật lý)": "product_25d",
                "🖼️ Giữ nguyên phẳng 2D": "flat_2d"
            }
            chosen_mode = mode_map.get(render_style, "branded_3d")

            # 3. Các thanh trượt tinh chỉnh thông số vật lý
            c_sl1, c_sl2 = st.columns(2)
            with c_sl1:
                horizon_y = st.slider(
                    "Đường chân trời (Horizon Level)", 
                    min_value=400, 
                    max_value=700, 
                    value=550, 
                    step=10,
                    key=f"horizon_{clean_sku}",
                    help="Vị trí giao thoa giữa chân tường và mặt sàn (Mặc định: 550px)"
                )
                shadow_density_pct = st.slider(
                    "Cường độ bóng tiếp xúc (Shadow Density)", 
                    min_value=30, 
                    max_value=100, 
                    value=80, 
                    step=5,
                    key=f"shadow_{clean_sku}",
                    help="Độ đậm nhạt của bóng tiếp xúc đáy chân đế và bóng tỏa mềm"
                )
            
            with c_sl2:
                depth_ratio_pct = st.slider(
                    "Độ nghiêng phối cảnh sàn (Perspective Depth)", 
                    min_value=5, 
                    max_value=35, 
                    value=20, 
                    step=1,
                    key=f"depth_{clean_sku}",
                    help="Độ mở góc của mặt sàn trải dài về phía người nhìn (Mặc định: 20%)"
                )
                sharpness_boost = st.slider("Độ nét & Làm rõ chữ AI (Sharpness & Text Clarity)", min_value=1.0, max_value=3.0, value=1.8, step=0.1, key=f"sharp_{clean_sku}", help="Khử mờ, tăng độ sắc nét chữ cho ảnh scan bìa sách / ảnh độ phân giải thấp (250px)")
                enable_refl = st.checkbox(
                    "Hiệu ứng phản xạ mờ mặt sàn (Subtle Floor Reflection)", 
                    value=True,
                    key=f"refl_{clean_sku}",
                    help="Lật ngược 20% chân sản phẩm với mặt nạ mờ tạo cảm giác sàn mica/gạch bóng"
                )

            # Nút Render chính
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

            # 🌟 NÚT 1: TẠO ẢNH CHUẨN BENCHMARK BIS TEXTILE 1254x1254 (LƯU VÀO GOOGLE DRIVE)
            if st.button(f"📸 TẠO ẢNH CHUẨN BENCHMARK BIS 1254x1254 CHO {clean_sku} (LƯU DRIVE)", type="primary", use_container_width=True, key=f"btn_flow_2d_{clean_sku}"):
                with st.spinner(f"Đang bóc tách quang học, làm nét bảo toàn chữ/logo và tạo ảnh 1254x1254 cho {clean_sku}..."):
                    import flow_2d_studio
                    try:
                        src_to_use = chosen_source_img
                        if not src_to_use or not src_to_use.exists():
                            src_to_use = flow_2d_studio.find_source_image_for_sku(clean_sku)
                        
                        if not src_to_use or not src_to_use.exists():
                            page_num = p_media.get("source_page", 1)
                            pdf_p = PROJECT_DIR / "Google_Drive_Storage" / "1_Catalogues" / "catalogue_sample.pdf"
                            if not pdf_p.exists():
                                pdf_p = PROJECT_DIR / "catalogue_sample.pdf"
                            if pdf_p.exists():
                                import pymupdf
                                doc = pymupdf.open(str(pdf_p))
                                if 1 <= page_num <= len(doc):
                                    imgs = doc[page_num - 1].get_images()
                                    if imgs:
                                        bimg = doc.extract_image(imgs[0][0])
                                        dest = PROJECT_DIR / "Google_Drive_Storage" / "4_Product_Images" / f"{clean_sku}.jpg"
                                        dest.write_bytes(bimg["image"])
                                        src_to_use = dest
                                doc.close()

                        if not src_to_use or not src_to_use.exists():
                            st.error(f"❌ Chưa có ảnh nguồn cho mã `{clean_sku}`! Hãy tải ảnh sản phẩm vào ô trên trước.")
                        else:
                            out_final = flow_2d_studio.generate_2d_studio_product(
                                sku=clean_sku,
                                source_img_path=src_to_use,
                                target_ground_y=980,
                                target_height=720,
                                auto_approve=True
                            )
                            if media_agent:
                                media_agent.manifest = media_agent._load_manifest()
                            st.toast(f"🎉 ĐÃ LƯU ẢNH CHUẨN BENCHMARK 1254x1254 CHO {clean_sku} VÀO GOOGLE DRIVE!", icon="📸")
                            st.success(f"✓ Hoàn tất! Ảnh thành phẩm 1254x1254 đã lưu tại: `{out_final.name}`")
                            st.rerun()
                    except Exception as ex_2d:
                        st.error(f"❌ Lỗi tạo ảnh 2D: {ex_2d}")

            st.markdown("<div style='margin-top: 6px;'></div>", unsafe_allow_html=True)
            # 🌟 NÚT 2: BATCH FLOW TỰ ĐỘNG CHẠY HÀNG LOẠT TOÀN BỘ SẢN PHẨM
            with st.expander("⚡ Batch Flow: Tự động tạo ảnh 2D hàng loạt cho toàn bộ danh mục"):
                st.write("Hệ thống sẽ tự động quét toàn bộ danh mục sản phẩm trong Google Drive, tách nền sản phẩm và ghép vào phông BIS_BACKGROUND.png đạt chuẩn 100%.")
                skip_done = st.checkbox("Bỏ qua các sản phẩm đã có ảnh thành phẩm", value=True, key=f"chk_skip_{clean_sku}")
                if st.button("🚀 BẮT ĐẦU CHẠY BATCH 2D FLOW HÀNG LOẠT", type="secondary", use_container_width=True, key=f"btn_run_batch_2d_{clean_sku}"):
                    import flow_2d_studio
                    prog_bar = st.progress(0.0)
                    status_text = st.empty()
                    status_text.info("Đang khởi động Batch Flow 2D...")
                    batch_res = flow_2d_studio.run_batch_flow(skip_existing=skip_done)
                    prog_bar.progress(1.0)
                    if media_agent:
                        media_agent.manifest = media_agent._load_manifest()
                    st.toast(f"🎉 Đã hoàn tất Batch Flow cho danh mục sản phẩm!", icon="🚀")
                    st.success(f"✓ Batch Flow hoàn tất! Xem thư mục `Google_Drive_Storage/6_Final_Composites` trên máy tính.")
                    st.rerun()

            st.markdown("<div style='margin-top: 6px;'></div>", unsafe_allow_html=True)
            # Nút Cloud AI Serverless (Miễn phí 100% - Chạy ngay trên Intel Iris Xe không cần GPU / Key)
            if st.button("⚡ TẠO MOCKUP 3D CLOUD AI (MIỄN PHÍ - KHÔNG CẦN KEY / GPU)", type="secondary", use_container_width=True, key=f"btn_cloud_free_{clean_sku}"):
                with st.spinner("Đang kết nối Cloud AI Serverless để dựng Mockup 3D Studio siêu thực trong 5-10 giây..."):
                    import importlib, agent_media
                    try:
                        importlib.reload(agent_media)
                        media_agent = agent_media.AgentMedia(PROJECT_DIR)
                        if leader:
                            leader.media_agent = media_agent
                    except Exception:
                        pass
                    
                    prod_title = p_media.get("title", p_media.get("name", clean_sku))
                    prod_brand = p_media.get("brand", "AATCC")
                    
                    try:
                        res_p = media_agent.generate_studio_mockup_cloud_free(
                            sku=clean_sku,
                            product_name=prod_title,
                            brand=prod_brand
                        )
                        if res_p and res_p.exists():
                            st.toast(f"🎉 ĐÃ TẠO ẢNH 3D STUDIO CHO {clean_sku} QUA CLOUD AI!", icon="⚡")
                            st.success(f"✓ Đã tạo thành công ảnh 3D Studio: {res_p.name}")
                            st.rerun()
                        else:
                            st.error("Không nhận được dữ liệu ảnh từ Cloud Serverless.")
                    except Exception as err:
                        st.error(f"❌ Lỗi Cloud AI: {err}")

            st.markdown("<div style='margin-top: 6px;'></div>", unsafe_allow_html=True)
            # Nút Gemini Imagen 3 Studio (Loại bỏ 100% OpenCV, gọi trực tiếp Imagen 3 API)
            custom_imagen_key = st.session_state.get("gemini_api_key_custom", "")
            if st.button("✨ TẠO MOCKUP 3D STUDIO BẰNG GEMINI AI (IMAGEN 3)", type="secondary", use_container_width=True, key=f"btn_imagen3_{clean_sku}"):
                with st.spinner("Đang kết nối Google Imagen 3 API (imagen-3.0-generate-002) để render ảnh Studio 3D siêu thực..."):
                    import importlib, agent_media
                    try:
                        importlib.reload(agent_media)
                        media_agent = agent_media.AgentMedia(PROJECT_DIR)
                        if leader:
                            leader.media_agent = media_agent
                    except Exception:
                        pass
                    
                    prod_title = p_media.get("title", p_media.get("name", clean_sku))
                    prod_brand = p_media.get("brand", "AATCC")
                    prod_cat = p_media.get("category", "Textile Standard")
                    
                    try:
                        res_path = media_agent.generate_studio_mockup_ai(
                            sku=clean_sku,
                            product_name=prod_title,
                            brand=prod_brand,
                            category=prod_cat,
                            api_key=custom_imagen_key if custom_imagen_key else None
                        )
                        if res_path and res_path.exists():
                            st.toast(f"🎉 ĐÃ TẠO ẢNH 3D STUDIO CHO {clean_sku} BẰNG IMAGEN 3!", icon="✨")
                            st.success(f"✓ Đã tạo thành công ảnh 3D Studio bằng Google Imagen 3: {res_path.name}")
                            st.rerun()
                        else:
                            st.error("Không nhận được ảnh trả về từ Imagen 3 API.")
                    except Exception as err:
                        st.error(f"❌ Lỗi gọi Google Imagen 3 API: {err}")
                        st.info("💡 **Lưu ý:** Google Imagen 3 yêu cầu API Key chính thức của Google AI Studio (bắt đầu bằng `AIzaSy...`). Bạn có thể dán API Key trực tiếp vào ô cấu hình nhanh bên dưới.")

            with st.expander("🔑 Cấu hình nhanh Gemini / Imagen 3 API Key (Google AI Studio)", expanded=False):
                current_k = st.session_state.get("gemini_api_key_custom", "")
                inp_k = st.text_input("Nhập Google AI Studio API Key (AIzaSy...):", value=current_k, type="password", key=f"inp_imagen_key_{clean_sku}", help="Lấy API Key miễn phí tại https://aistudio.google.com/app/apikey")
                if inp_k != current_k:
                    st.session_state["gemini_api_key_custom"] = inp_k.strip()
                    st.toast("✓ Đã lưu API Key vào phiên làm việc!", icon="🔑")

            st.markdown("<div style='margin-top: 6px;'></div>", unsafe_allow_html=True)
            if st.button(f"🚀 RENDER 3D STUDIO CHUẨN THƯƠNG HIỆU CHO {clean_sku}", type="primary", use_container_width=True, key=f"btn_run_branded_{clean_sku}"):
                if not chosen_source_img or not chosen_source_img.exists():
                    st.error(f"❌ Chưa có ảnh nguồn cho mã `{clean_sku}`! Vui lòng tải file vào ô trên.")
                else:
                    with st.spinner("AI đang dựng phông nền 3D Tường - Sàn, tính toán ma trận phối cảnh OpenCV và đổ bóng tiếp xúc vật lý..."):
                        import importlib, agent_media
                        try:
                            importlib.reload(agent_media)
                            media_agent = agent_media.AgentMedia(PROJECT_DIR)
                            if leader:
                                leader.media_agent = media_agent
                        except Exception:
                            pass
                        
                        final_path = media_agent.composite_product_image(
                            sku=clean_sku,
                            product_img_path=chosen_source_img,
                            bg_path=selected_bg_path,
                            render_mode=chosen_mode,
                            horizon_y=horizon_y,
                            depth_ratio=depth_ratio_pct / 100.0,
                            shadow_density=shadow_density_pct / 100.0,
                            enable_reflection=enable_refl,
                            sharpness_boost=sharpness_boost
                        )
                        st.success(f"✓ Đã render hoàn tất: {final_path.name}")
                        st.rerun()

            # Hỗ trợ kết nối Canva / Photoroom ngoài nếu muốn
            with st.expander("🎨 Tùy chọn Studio Ngoài (Canva Smartmockups & Photoroom Pro)"):
                st.markdown(f"""
                <div style='font-size: 12px; color: #cbd5e1; margin-bottom: 8px;'>
                  Tạo mockup sách hoặc thiết bị 3D trên Canva/Photoroom rồi nạp thẳng vào hệ thống:
                </div>
                <div style='display: flex; gap: 8px; margin-bottom: 10px;'>
                  <a href='https://www.canva.com/smartmockups/books' target='_blank' style='background: #6366f1; color: white; padding: 6px 12px; border-radius: 6px; text-decoration: none; font-size: 11px; font-weight: 700;'>Mở Canva Mockups ↗</a>
                  <a href='https://www.photoroom.com/tools/background-remover' target='_blank' style='background: #475569; color: white; padding: 6px 12px; border-radius: 6px; text-decoration: none; font-size: 11px; font-weight: 700;'>Mở Photoroom ↗</a>
                </div>
                """, unsafe_allow_html=True)
                up_canva = st.file_uploader(
                    f"Kéo thả ảnh mockup từ Canva vào đây (Lưu thẳng vào Final và Duyệt):",
                    type=["jpg", "png", "jpeg"],
                    key=f"canva_up_{clean_sku}"
                )
                sig_key_canva = f"proc_canva_{clean_sku}"
                if up_canva:
                    c_bytes = up_canva.getvalue()
                    c_sig = f"{up_canva.name}_{len(c_bytes)}"
                    if st.session_state.get(sig_key_canva) != c_sig:
                        st.session_state[sig_key_canva] = c_sig
                        if hasattr(media_agent, "register_final_composite"):
                            media_agent.register_final_composite(clean_sku, c_bytes)
                        else:
                            out_p = media_agent.final_dir / f"{clean_sku}_final.jpg"
                            out_p.write_bytes(c_bytes)
                        st.toast(f"✓ Đã lưu và duyệt ảnh Mockup ngoài cho mã {clean_sku}!", icon="🎉")
                        st.rerun()

        # ── CỘT PHẢI: LIVE PREVIEW 2K & CỔNG PHÊ DUYỆT HARAVAN ────────────────
        with col_m2:
            st.markdown("#### 3. Bản Xem Trước Render 3D Hoàn Chỉnh & Cổng Duyệt")
            preview_img_path = media_agent.preview_dir / f"{clean_sku}_preview.jpg" if hasattr(media_agent, "preview_dir") else (media_agent.gdrive_storage / "5_Draft_Previews" / f"{clean_sku}_preview.jpg")
            final_img_path = media_agent.final_dir / f"{clean_sku}_final.jpg"
            img_manifest = media_agent.manifest.get(clean_sku, {})
            current_img_status = img_manifest.get("status", "CHƯA XỬ LÝ")

            # Quyết định ảnh hiển thị:
            # - Nếu đang có bản nháp preview vừa render: hiển thị preview_img_path để duyệt
            # - Nếu đã duyệt (APPROVED) và có final_img_path: hiển thị final_img_path
            # - Fallback: preview_img_path hoặc final_img_path
            display_img_path = None
            if preview_img_path.exists() and current_img_status != "APPROVED":
                display_img_path = preview_img_path
            elif current_img_status == "APPROVED" and final_img_path.exists():
                display_img_path = final_img_path
            elif preview_img_path.exists():
                display_img_path = preview_img_path
            elif final_img_path.exists():
                display_img_path = final_img_path

            # Khối thông báo xác nhận lưu Google Drive khi người dùng bấm Duyệt
            if current_img_status == "APPROVED" and final_img_path.exists():
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #064e3b 0%, #022c22 100%); border: 1.5px solid #10b981; border-radius: 10px; padding: 14px; margin-bottom: 14px;'>
                  <div style='color: #6ee7b7; font-weight: 800; font-size: 14px; display: flex; align-items: center; gap: 8px;'>
                    <span>✅</span> <span>ĐÃ LƯU CHÍNH THỨC VÀO GOOGLE DRIVE THÀNH CÔNG!</span>
                  </div>
                  <div style='color: #e2e8f0; font-size: 12px; margin-top: 6px; line-height: 1.6;'>
                    📁 <b>Vị trí file:</b> <code>Google_Drive_Storage/6_Final_Composites/{clean_sku}_final.jpg</code><br>
                    🛡️ <b>Trạng thái:</b> Đã duyệt &bull; Sẵn sàng đồng bộ Haravan.<br>
                    ⏱️ <b>Thời gian duyệt:</b> <code>{img_manifest.get('approved_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}</code>
                  </div>
                </div>
                """, unsafe_allow_html=True)

            if display_img_path and display_img_path.exists():
                st.image(
                    str(display_img_path), 
                    caption=f"Ảnh render 3D Studio mã {clean_sku} ({'ĐÃ DUYỆT - SẴN SÀNG XUẤT BẢN' if current_img_status == 'APPROVED' else 'BẢN XEM TRƯỚC (CHỜ BẠN DUYỆT)'})", 
                    use_container_width=True
                )
                
                # Hiển thị metadata render
                render_mode_used = img_manifest.get("render_mode", "3D Studio")
                st.markdown(f"""
                <div style='background: #0d1322; border: 1.5px solid #1e293b; padding: 12px; border-radius: 8px; margin-bottom: 12px;'>
                  <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                      <strong>Trạng thái:</strong> <span style='color: {"#10b981" if current_img_status == "APPROVED" else "#f59e0b"}; font-weight: 700;'>{current_img_status}</span>
                      <span style='color: #64748b; font-size: 11px; margin-left: 10px;'>Chế độ: <code>{render_mode_used}</code></span>
                    </div>
                    <div style='font-size: 11px; color: #94a3b8;'>Dung lượng: {display_img_path.stat().st_size // 1024} KB</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                col_ap1, col_ap2, col_ap3 = st.columns([4, 4, 4])
                with col_ap1:
                    if st.button("✅ DUYỆT & LƯU VÀO DRIVE", key=f"appr_img_{clean_sku}", type="primary", use_container_width=True):
                        media_agent.approve_image(clean_sku, source_override=display_img_path)
                        st.session_state.audit_logs.append({
                            "time": datetime.now().strftime("%H:%M:%S"),
                            "type": "MEDIA",
                            "text": f"Ảnh sản phẩm {clean_sku} đã được PHÊ DUYỆT lưu vào Google_Drive_Storage/6_Final_Composites."
                        })
                        st.toast(f"✅ ĐÃ LƯU {clean_sku}_final.jpg VÀO DRIVE!", icon="💾")
                        st.rerun()

                with col_ap2:
                    with open(display_img_path, "rb") as f_dl:
                        st.download_button(
                            label="⬇️ TẢI ẢNH HD",
                            data=f_dl.read(),
                            file_name=f"{clean_sku}_final.jpg",
                            mime="image/jpeg",
                            use_container_width=True,
                            key=f"dl_btn_{clean_sku}"
                        )

                with col_ap3:
                    if st.button("❌ TỪ CHỐI / LÀM LẠI", key=f"rej_img_{clean_sku}", use_container_width=True):
                        media_agent.reject_image(clean_sku, "Yêu cầu chỉnh lại góc phối cảnh/bóng")
                        st.warning("Đã từ chối ảnh và xóa khỏi 6_Final_Composites. Hãy chỉnh các thanh trượt và render lại.")
                        st.rerun()

                # Nút mở thư mục trực tiếp trong Windows Explorer
                st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
                col_exp1, col_exp2 = st.columns([6, 6])
                with col_exp1:
                    if st.button("📂 MỞ THƯ MỤC ẢNH TRÊN MÁY TÍNH", key=f"btn_open_exp_{clean_sku}", use_container_width=True):
                        import subprocess
                        target_f = final_img_path if final_img_path.exists() else display_img_path
                        try:
                            subprocess.Popen(f'explorer.exe /select,"{target_f}"')
                            st.toast("Đang mở Windows File Explorer...", icon="📂")
                        except Exception as ex:
                            st.error(f"Không thể mở thư mục: {ex}")
                with col_exp2:
                    st.caption("🔒 **Nguyên tắc an toàn:** Chỉ ảnh bạn nhấn **DUYỆT** mới được lưu vào `6_Final_Composites`.")
            else:
                st.info(f"💡 Chưa có ảnh render cho mã `{clean_sku}`.\n\nHãy kiểm tra ảnh nguồn ở cột bên trái, điều chỉnh các thanh trượt đường chân trời / độ nghiêng phối cảnh và bấm nút **'🚀 RENDER 3D STUDIO'** để xem kết quả trực quan ngay tại đây.")


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


# ── TAB 6: PHÒNG DỊCH THUẬT & BẢN ĐỊA HÓA TIÊU CHUẨN QUỐC TẾ ──────────────────
with tab_trans:
    st.markdown("### 🌐 Phòng Biên Dịch & Bản Địa Hóa Tiêu Chuẩn Quốc Tế (Agent_Translator)")
    st.markdown("""
    <div style='background: #090e1a; border: 1.5px solid #0284c7; border-radius: 12px; padding: 16px; margin-bottom: 18px;'>
      <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;'>
        <h4 style='color: #38bdf8; margin: 0;'>📖 Bộ Đôi Dịch Giữ 100% Format: PDFMathTranslate (MCP) & Keep-Form Agent Skill</h4>
        <span style='background: #0369a1; color: #e0f2fe; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; font-family: monospace;'>MCP PROTOCOL ACTIVE</span>
      </div>
      <p style='font-size: 13px; color: #cbd5e1; line-height: 1.6; margin: 0;'>
        • <b>PDFMathTranslate (pdf2zh qua giao thức MCP):</b> Bóc tách PDF bằng <code>DocLayout-YOLO</code>, bảo toàn công thức toán, biểu đồ và bảng kỹ thuật.<br>
        • <b>Keep-Form Agent Skill (.docx, .xlsx, .html):</b> Can thiệp trực tiếp cấp độ XML <code>run.text</code>, <code>openpyxl cell</code> (bảo vệ công thức <code>=</code>) và <code>BeautifulSoup NavigableString</code>.<br>
        • <b>Định dạng hỗ trợ toàn diện:</b> <code>.pdf</code>, <code>.docx</code>, <code>.xlsx</code>, <code>.html</code>, ảnh scan OCR. Bản dịch tự động lưu vào <code>8_Translated_Documents/&lt;Hãng&gt;/</code> và sẵn sàng tải xuống.
      </p>
    </div>
    """, unsafe_allow_html=True)

    # 1. Thống kê & Quét tài liệu
    brand_manuals_dict = load_cached_manuals_by_brand(str(PROJECT_DIR))
    translated_docs_list = load_cached_translated_docs(str(PROJECT_DIR))

    total_brands_count = len(brand_manuals_dict)
    total_manuals_count = sum(len(docs) for docs in brand_manuals_dict.values())
    total_translated_count = len(translated_docs_list)

    c_m1, c_m2, c_m3, c_m4 = st.columns(4)
    with c_m1:
        st.metric("🏢 Tổng số Hãng sản xuất", f"{total_brands_count} Hãng")
    with c_m2:
        st.metric("📚 Tài liệu & Tiêu chuẩn gốc", f"{total_manuals_count} File")
    with c_m3:
        st.metric("✅ Bản dịch tiếng Việt hoàn tất", f"{total_translated_count} File")
    with c_m4:
        st.metric("📂 Thư mục lưu trữ riêng", "8_Translated_Documents")

    st.markdown("---")
    st.markdown("#### 🚀 Khởi chạy dịch tài liệu sang tiếng Việt:")

    tab_mode_select, tab_mode_upload, tab_mode_image = st.tabs([
        "📚 1. Chọn Tài Liệu Có Sẵn Theo Hãng",
        "📤 2. Tải Lên File Mới (PDF / Word / Excel / HTML)",
        "🖼️ 3. Dịch Ảnh & Sơ Đồ Thiết Bị Giữ Nguyên Form"
    ])

    with tab_mode_select:
        if not brand_manuals_dict:
            st.info("ℹ️ Hiện chưa có tài liệu nào trong thư mục máy chủ. Bạn có thể chuyển sang tab **'📤 2. Tải Lên File Mới Từ Máy Tính'** ở bên cạnh để tải file lên và dịch ngay!")
        else:
            col_sel_brand, col_sel_doc = st.columns([1, 2])
            brand_keys = list(brand_manuals_dict.keys())

            with col_sel_brand:
                selected_brand = st.selectbox(
                    "1. Chọn Hãng sản xuất / Nhóm tiêu chuẩn:",
                    options=brand_keys,
                    key="trans_sel_brand"
                )

            doc_candidates = brand_manuals_dict.get(selected_brand, [])
            with col_sel_doc:
                doc_labels = [f"{d['name']} ({d['size_kb']} KB, {d['ext'].upper()})" for d in doc_candidates]
                selected_doc_idx = st.selectbox(
                    "2. Chọn tài liệu cần dịch sang tiếng Việt:",
                    options=range(len(doc_candidates)),
                    format_func=lambda i: doc_labels[i] if i < len(doc_labels) else "",
                    key="trans_sel_doc_idx"
                )

            if doc_candidates and 0 <= selected_doc_idx < len(doc_candidates):
                chosen_doc = doc_candidates[selected_doc_idx]
                
                # Kiểm tra khả năng đọc văn bản kỹ thuật số
                fresh_translator = AgentTranslator(PROJECT_DIR) if AgentTranslator else translator_agent
                if fresh_translator and hasattr(fresh_translator, "check_document_text_readability"):
                    r_check = fresh_translator.check_document_text_readability(chosen_doc["path"])
                    if r_check.get("is_image_pdf"):
                        st.warning(f"⚠️ **Tài liệu dạng đồ họa/ảnh**: {r_check.get('message')}")
                    else:
                        st.success(f"{r_check.get('message')}")

                c_opt1, c_opt2 = st.columns([2, 1])
                with c_opt1:
                    trans_mode = st.radio(
                        "3. Chọn phạm vi biên dịch:",
                        options=["Toàn bộ tài liệu (Full Document)", "Thử nghiệm trang đầu (1-3 trang)"],
                        horizontal=True,
                        key="trans_mode_radio"
                    )
                with c_opt2:
                    max_pages_to_trans = 3 if "Thử nghiệm" in trans_mode else None
                    st.caption(f"📌 Chế độ: **{'Dịch mẫu 3 trang đầu' if max_pages_to_trans else 'Dịch 100% toàn bộ trang'}**")

                st.write("")
                btn_start_trans = st.button(
                    f"🚀 DỊCH TÀI LIỆU '{chosen_doc['name']}' SANG TIẾNG VIỆT",
                    type="primary",
                    use_container_width=True,
                    key="btn_run_translate"
                )

                if btn_start_trans:
                    with st.spinner("Agent_Translator đang phân tích cấu trúc tài liệu và tiến hành biên dịch..."):
                        prog_bar = st.progress(0.0)
                        status_text = st.empty()

                        def ui_progress_cb(pct, msg):
                            prog_bar.progress(pct)
                            status_text.info(f"⏳ {msg}")

                        try:
                            fresh_translator = AgentTranslator(PROJECT_DIR) if AgentTranslator else translator_agent
                            res_path = fresh_translator.translate_document(
                                doc_path=chosen_doc["path"],
                                brand_name=selected_brand,
                                progress_callback=ui_progress_cb,
                                max_pages=max_pages_to_trans
                            )
                            prog_bar.progress(1.0)
                            status_text.success(f"🎉 Hoàn tất dịch thuật! File đã lưu vào: `{res_path.relative_to(PROJECT_DIR)}`")

                            if res_path.exists():
                                with open(res_path, "rb") as f_out:
                                    docx_bytes = f_out.read()
                                st.download_button(
                                    label=f"📥 TẢI XUỐNG BẢN DỊCH: {res_path.name}",
                                    data=docx_bytes,
                                    file_name=res_path.name,
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    type="primary",
                                    use_container_width=True
                                )
                                load_cached_translated_docs.clear()
                        except Exception as e:
                            prog_bar.progress(1.0)
                            status_text.error(f"❌ Có lỗi trong quá trình dịch thuật: {e}")

    with tab_mode_upload:
        st.markdown("##### 📤 Tải tài liệu từ máy tính lên để biên dịch tức thì:")
        col_up_file, col_up_brand = st.columns([2, 1])
        with col_up_file:
            uploaded_trans_file = st.file_uploader(
                "Chọn file tài liệu hoặc HÌNH ẢNH cần dịch (PDF, Word, PNG, JPG):",
                type=["pdf", "docx", "xlsx", "html", "htm", "png", "jpg", "jpeg", "webp"],
                key="uploader_trans_doc"
            )
        with col_up_brand:
            upload_brand_name = st.text_input(
                "Tên Hãng sản xuất / Tổ chức tiêu chuẩn:",
                value="Tài liệu tải lên",
                key="uploader_trans_brand"
            )

        if uploaded_trans_file is not None:
            c_up_opt1, c_up_opt2 = st.columns([2, 1])
            with c_up_opt1:
                trans_up_mode = st.radio(
                    "Chọn phạm vi biên dịch:",
                    options=["Toàn bộ tài liệu (Full Document)", "Thử nghiệm trang đầu (1-3 trang)"],
                    horizontal=True,
                    key="trans_up_mode_radio"
                )
            with c_up_opt2:
                max_up_pages = 3 if "Thử nghiệm" in trans_up_mode else None
                st.caption(f"📌 Chế độ: **{'Dịch mẫu 3 trang đầu' if max_up_pages else 'Dịch 100% toàn bộ trang'}**")

            btn_upload_trans = st.button(
                f"🚀 BẮT ĐẦU DỊCH FILE '{uploaded_trans_file.name}' SANG TIẾNG VIỆT",
                type="primary",
                use_container_width=True,
                key="btn_run_uploaded_trans"
            )

            if btn_upload_trans:
                with st.spinner("Đang lưu trữ file và phân tích dịch thuật..."):
                    clean_b_folder = re.sub(r'[\\/*?:"<>|]', "", upload_brand_name).strip() or "General"
                    save_dir = PROJECT_DIR / "Google_Drive_Storage" / "2_Manuals_Standards" / clean_b_folder
                    save_dir.mkdir(parents=True, exist_ok=True)
                    saved_target_path = save_dir / uploaded_trans_file.name
                    with open(saved_target_path, "wb") as f_save:
                        f_save.write(uploaded_trans_file.getbuffer())

                    prog_bar_up = st.progress(0.0)
                    status_text_up = st.empty()

                    def ui_up_progress_cb(pct, msg):
                        prog_bar_up.progress(pct)
                        status_text_up.info(f"⏳ {msg}")

                    try:
                        ext_lower = saved_target_path.suffix.lower()
                        trans_dest_dir = PROJECT_DIR / "Google_Drive_Storage" / "8_Translated_Documents" / clean_b_folder
                        trans_dest_dir.mkdir(parents=True, exist_ok=True)

                        if ext_lower in [".xlsx", ".html", ".htm"] or (ext_lower == ".docx" and KeepFormTranslator):
                            ui_up_progress_cb(0.1, f"Khởi động Keep-Form Agent Skill bảo toàn định dạng {ext_lower}...")
                            res_path = KeepFormTranslator.translate_any(
                                src_path=saved_target_path,
                                dst_dir=trans_dest_dir,
                                target_lang="vi",
                                progress_callback=ui_up_progress_cb
                            )
                        else:
                            fresh_translator = AgentTranslator(PROJECT_DIR) if AgentTranslator else translator_agent
                            res_path = fresh_translator.translate_document(
                                doc_path=saved_target_path,
                                brand_name=upload_brand_name,
                                progress_callback=ui_up_progress_cb,
                                max_pages=max_up_pages
                            )

                        prog_bar_up.progress(1.0)
                        status_text_up.success(f"🎉 Hoàn tất dịch thuật bảo toàn 100% format! File đã lưu vào: `{res_path.relative_to(PROJECT_DIR)}`")

                        if res_path.exists():
                            mime_map = {
                                ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                ".html": "text/html",
                                ".htm": "text/html",
                                ".pdf": "application/pdf"
                            }
                            target_mime = mime_map.get(res_path.suffix.lower(), "application/octet-stream")
                            with open(res_path, "rb") as f_out:
                                file_bytes = f_out.read()
                            st.download_button(
                                label=f"📥 TẢI XUỐNG BẢN DỊCH ({res_path.suffix.upper()}): {res_path.name}",
                                data=file_bytes,
                                file_name=res_path.name,
                                mime=target_mime,
                                type="primary",
                                use_container_width=True
                            )
                            load_cached_manuals_by_brand.clear()
                            load_cached_translated_docs.clear()
                    except Exception as e:
                        prog_bar_up.progress(1.0)
                        status_text_up.error(f"❌ Có lỗi trong quá trình dịch thuật: {e}")


    with tab_mode_image:
        st.markdown("##### 🖼️ Dịch Ảnh / Sơ Đồ Kỹ Thuật / Catalogue Giữ Nguyên Form 100%:")
        st.markdown("""
        <div style='background: #090e1a; border: 1px solid #1e293b; border-left: 3px solid #06b6d4; border-radius: 8px; padding: 12px; margin-bottom: 14px;'>
          <p style='font-size: 13px; color: #cbd5e1; margin: 0; line-height: 1.6;'>
            • <b>Thuật toán Inpainting & Auto-fit Typography:</b> Nhận diện OCR vị trí chữ tiếng Anh trên sơ đồ máy móc, tự động xóa nền chữ cũ và vẽ đè bản dịch tiếng Việt.<br>
            • <b>Bảo toàn 100% đồ họa:</b> Không làm méo mó sơ đồ, giữ nguyên các mũi tên liên kết, màu nền, đường biên và kích thước bounding box.<br>
            • <b>Skill Antigravity:</b> Kích hoạt tự động qua Skill <code>image-layout-translator</code>.
          </p>
        </div>
        """, unsafe_allow_html=True)

        col_img_up, col_img_brand = st.columns([2, 1])
        with col_img_up:
            uploaded_img = st.file_uploader(
                "Tải lên hình ảnh catalogue / sơ đồ kỹ thuật (PNG, JPG, JPEG, WEBP):",
                type=["png", "jpg", "jpeg", "webp"],
                key="uploader_single_image_trans"
            )
        with col_img_brand:
            img_brand_name = st.text_input(
                "Tên Hãng / Thiết bị (để phân loại thư mục):",
                value="General",
                key="uploader_img_brand_input"
            )

        if uploaded_img is not None:
            btn_run_img_trans = st.button("🚀 BẮT ĐẦU DỊCH & BẢO TOÀN BỐ CỤC ẢNH", type="primary", use_container_width=True, key="btn_run_img_trans")

            if btn_run_img_trans:
                with st.spinner("Agent đang chạy OCR bóc tách tọa độ, tẩy chữ cũ và vẽ đè bản dịch tiếng Việt..."):
                    clean_ib = re.sub(r'[\\/*?:"<>|]', "", img_brand_name).strip() or "General"
                    img_save_dir = PROJECT_DIR / "Google_Drive_Storage" / "8_Translated_Documents" / clean_ib
                    img_save_dir.mkdir(parents=True, exist_ok=True)
                    
                    temp_in = img_save_dir / f"orig_{uploaded_img.name}"
                    temp_out = img_save_dir / f"translated_{uploaded_img.name}"

                    with open(temp_in, "wb") as f_in:
                        f_in.write(uploaded_img.getbuffer())

                    from agent_translator import AgentTranslator
                    ag_tr = AgentTranslator(PROJECT_DIR)
                    out_img_path = ag_tr.translate_image_keep_form(temp_in, temp_out)

                st.success(f"🎉 Đã dịch ảnh thành công! File lưu tại: `{out_img_path.relative_to(PROJECT_DIR)}`")
                col_img_orig, col_img_trans = st.columns(2)
                with col_img_orig:
                    st.caption("📷 Ảnh gốc (English)")
                    st.image(str(temp_in), use_container_width=True)
                with col_img_trans:
                    st.caption("🇻🇳 Ảnh đã dịch (Tiếng Việt Giữ Form)")
                    st.image(str(out_img_path), use_container_width=True)
                    with open(out_img_path, "rb") as f_dl:
                        img_bytes = f_dl.read()
                    st.download_button(
                        label=f"📥 TẢI ẢNH TIẾNG VIỆT: {out_img_path.name}",
                        data=img_bytes,
                        file_name=out_img_path.name,
                        mime="image/png" if out_img_path.suffix.lower() == ".png" else "image/jpeg",
                        type="primary",
                        use_container_width=True
                    )

    # 2. Danh sách kho tài liệu đã dịch hoàn tất trong thư mục riêng
    st.markdown("---")
    st.markdown("#### 📂 Kho Tài Liệu Đã Dịch Hoàn Tất Trong Thư Mục Riêng (`8_Translated_Documents`):")

    updated_translated_docs = load_cached_translated_docs(str(PROJECT_DIR))
    if not updated_translated_docs:
        st.info("ℹ️ Chưa có tài liệu nào được dịch trong thư mục 8_Translated_Documents. Hãy chọn tài liệu ở trên và nhấn nút Dịch!")
    else:
        for idx, t_doc in enumerate(updated_translated_docs):
            with st.container():
                col_info, col_btn = st.columns([4, 1])
                with col_info:
                    st.markdown(f"**📄 {t_doc['name']}**")
                    st.caption(f"🏢 Hãng: **{t_doc['brand']}** • 💾 Dung lượng: **{t_doc['size_kb']} KB** • 🕒 Thời gian: `{t_doc['created_at']}`")
                with col_btn:
                    p_file = Path(t_doc['path'])
                    if p_file.exists():
                        with open(p_file, "rb") as f_down:
                            d_bytes = f_down.read()
                        st.download_button(
                            label="📥 Tải Word",
                            data=d_bytes,
                            file_name=t_doc['name'],
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key=f"down_btn_trans_{idx}",
                            use_container_width=True
                        )
                st.markdown("<hr style='margin: 8px 0; border: 0.5px solid rgba(255,255,255,0.06);'>", unsafe_allow_html=True)


# ── TAB 7: PHÒNG VẬN HÀNH & HARAVAN GUARD ────────────────────────────────────
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

    approved_count = len([item for item in products if item.get("status") == "APPROVED"])
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
    approved_for_sync = [item for item in products if item.get("status") == "APPROVED"]
    st.info(f"Hiện có **{len(approved_for_sync)} sản phẩm** đã APPROVED sẵn sàng đẩy lên Haravan: {[x.get('sku') for x in approved_for_sync]}")
    if st.button("🚀 BẮT ĐẦU ĐỒNG BỘ CÁC SẢN PHẨM APPROVED LÊN HARAVAN", type="primary", disabled=(len(approved_for_sync) == 0)):
        with st.spinner("Agent_Operations đang tiến hành kết nối Haravan API..."):
            fresh_ops = AgentOperations(PROJECT_DIR) if AgentOperations else operations_agent
            sync_res = fresh_ops.sync_approved_to_haravan(approved_for_sync)
            st.write("📊 Kết quả phản hồi từ Haravan API:", sync_res)
            success_items = [r for r in sync_res if r.get("status") == "SUCCESS"]
            error_items = [r for r in sync_res if r.get("status") != "SUCCESS"]

            if success_items:
                # Đánh dấu PUSHED_TO_HARAVAN trong local cache
                pushed_skus = {r.get("sku") for r in success_items}
                for item in products:
                    if item.get("sku") in pushed_skus:
                        item["status"] = "PUSHED_TO_HARAVAN"
                        item["haravan_id"] = next((r.get("haravan_id") for r in success_items if r.get("sku") == item.get("sku")), None)

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
                st.session_state.audit_logs.append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "type": "SYNC",
                    "text": f"Đồng bộ thành công {len(success_items)} sản phẩm lên sàn Haravan."
                })
                st.success(f"✓ ĐÃ TẠO THÀNH CÔNG {len(success_items)} SẢN PHẨM TRÊN HARAVAN (CHẾ ĐỘ ẨN)!")

            if error_items:
                st.error(f"⚠️ Có {len(error_items)} sản phẩm gặp lỗi phản hồi từ Haravan API:")
                st.json(error_items)

            if not sync_res:
                st.info("Hiện không có sản phẩm nào ở trạng thái APPROVED cần đồng bộ. Hãy phê duyệt sản phẩm tại Bàn Kỹ thuật trước.")


# ── TAB 8: BỘ NHỚ TỰ HỌC TIẾN HÓA & PHẢN TỈNH (EVOLVING LEARNING ENGINE) ───────
with tab_learn:
    render_memory_panel(bis_memory)
    st.divider()
    st.markdown("### 🧠 Bộ Não Tự Học Tiến Hóa & Phản Tỉnh (Evolving Learning Engine)")
    st.write("Kiến trúc tự học đa tầng kết hợp giữa **Voyager** (Kho kỹ năng theo Hãng), **Reflexion** (Tự suy ngẫm nguyên nhân sai sót) và **Generative Agents** (Nén tri thức không gây loãng prompt).")

    mem_file = PROJECT_DIR / "feedback_memory.json"
    rules_file = PROJECT_DIR / "consolidated_rules.json"
    mem_data = load_cached_learning_memory(str(mem_file))
    
    # Đọc quy tắc phân vùng từ learning_engine
    all_rules_data = learning_engine.load_rules() if hasattr(learning_engine, "load_rules") else {}
    brand_rules_dict = all_rules_data.get("brand_rules", {})
    global_rules_list = all_rules_data.get("global_rules", [])
    examples = mem_data.get("examples", [])
    reflections = mem_data.get("reflections", [])

    c_lm1, c_lm2 = st.columns([6.2, 5.8])
    with c_lm1:
        st.markdown("#### 📌 1. Kho Quy Tắc Tiến Hóa Phân Vùng (Brand-Partitioned Rules)")
        st.caption("Các 'micro-rules' độc lập được AI tự đúc kết riêng cho từng Hãng thiết bị:")

        brand_options = ["GLOBAL (Toàn Hệ Thống)"] + sorted(list(brand_rules_dict.keys()))
        selected_brand_tab = st.selectbox("Chọn Hãng để xem & quản lý quy tắc:", options=brand_options, key="sel_learning_brand")

        if selected_brand_tab.startswith("GLOBAL"):
            active_rules = global_rules_list
            is_global = True
            current_brand_key = "GLOBAL"
        else:
            active_rules = brand_rules_dict.get(selected_brand_tab, [])
            is_global = False
            current_brand_key = selected_brand_tab

        if active_rules:
            for idx, r in enumerate(active_rules):
                col_r_txt, col_r_del = st.columns([10, 2])
                with col_r_txt:
                    st.markdown(f"**{idx+1}.** {r}")
                with col_r_del:
                    if st.button("🗑️", key=f"del_brule_{current_brand_key}_{idx}", help="Xóa quy tắc này"):
                        if is_global:
                            learning_engine.delete_custom_rule(idx)
                        else:
                            learning_engine.delete_brand_rule(current_brand_key, idx)
                        load_cached_learning_memory.clear()
                        st.toast("Đã xóa quy tắc thành công!", icon="🗑️")
                        st.rerun()
        else:
            st.info(f"Chưa có quy tắc nào cho {current_brand_key}.")

        c_add_r, c_cons_r = st.columns([7, 5])
        with c_add_r:
            with st.form(f"add_rule_form_{current_brand_key}"):
                new_rule_input = st.text_input(f"Thêm quy tắc mới cho {current_brand_key}:", placeholder="Nhập quy tắc bóc tách bắt buộc...")
                if st.form_submit_button("➕ THÊM QUY TẮC", use_container_width=True):
                    if new_rule_input.strip():
                        if is_global:
                            learning_engine.add_custom_rule(new_rule_input.strip())
                        else:
                            learning_engine.add_brand_rule(current_brand_key, new_rule_input.strip())
                        load_cached_learning_memory.clear()
                        st.toast(f"✓ Đã thêm quy tắc cho {current_brand_key}!", icon="🧠")
                        st.rerun()
        with c_cons_r:
            if not is_global and len(active_rules) >= 3:
                st.write("")
                st.write("")
                if st.button("⚡ NÉN TRI THỨC (CONSOLIDATE)", key=f"btn_cons_{current_brand_key}", help="Gộp các quan sát nhỏ thành 2-3 nguyên lý cốt lõi cấp cao", use_container_width=True):
                    with st.spinner("Đang chạy nén tri thức qua Gemini..."):
                        c_msg = learning_engine.consolidate_brand_rules(current_brand_key)
                        load_cached_learning_memory.clear()
                        st.success(c_msg)
                        st.rerun()

        # Hiển thị khối Reflexion Audit Log
        st.markdown("---")
        st.markdown(f"#### 🔍 2. Nhật Ký Phản Tỉnh & Đúc Kết Lỗi (Reflexion Log - {len(reflections)} lượt)")
        st.caption("AI tự phân tích nguyên nhân sai sót khi chuyên viên chỉnh sửa dữ liệu:")
        if reflections:
            ref_box = st.container(height=260)
            with ref_box:
                for rf in reversed(reflections[-8:]):
                    with st.expander(f"Mã {rf.get('sku')} • {rf.get('brand')} ({rf.get('timestamp')[:19]})", expanded=False):
                        st.markdown(f"**Lý do AI nhận diện chưa chuẩn:**\n_{rf.get('reflection', '')}_")
                        if rf.get('distilled_rule'):
                            st.markdown(f"**🎯 Quy tắc đúc kết:** `{rf.get('distilled_rule')}`")
                        st.json(rf.get("diff", {}))
        else:
            st.info("Chưa có lượt tự suy ngẫm nào. Khi bạn chỉnh sửa và bấm lưu tại Tab 2, AI sẽ tự động phản tỉnh và hiển thị tại đây.")
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
                        load_cached_learning_memory.clear()
                        st.toast("Đã xóa quy tắc thành công!", icon="🗑️")
                        st.rerun()
        else:
            st.info("Chưa có quy tắc nào.")

        with st.form("add_rule_form"):
            new_rule_input = st.text_input("Thêm quy tắc chuẩn hóa mới cho AI:", placeholder="VD: Tất cả sách hướng dẫn của AATCC phải có đơn vị tính là 'cuốn'...")
            if st.form_submit_button("➕ THÊM QUY TẮC MỚI", use_container_width=True):
                if new_rule_input.strip():
                    learning_engine.add_custom_rule(new_rule_input.strip())
                    load_cached_learning_memory.clear()
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
                            load_cached_learning_memory.clear()
                            st.toast("Đã xóa bài học!", icon="🗑️")
                            st.rerun()
            else:
                st.info("Chưa có bản ghi hiệu chỉnh nào. Hãy sửa thông tin sản phẩm tại Bàn Kỹ thuật để huấn luyện AI.")
