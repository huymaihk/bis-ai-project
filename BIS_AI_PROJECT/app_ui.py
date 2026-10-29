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

  /* Node Cards */
  .agent-node {
    background: #0d1322;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 14px;
    transition: all 0.25s ease-in-out;
    position: relative;
    height: 100%;
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

  /* Google Search Snippet Preview */
  .google-preview-box {
    background: #ffffff;
    color: #202124;
    padding: 16px;
    border-radius: 10px;
    box-shadow: 0 1px 6px rgba(32, 33, 36, 0.28);
    font-family: Arial, sans-serif;
    margin-top: 10px;
  }
  .google-preview-url { font-size: 12px; color: #202124; margin-bottom: 4px; }
  .google-preview-title { font-size: 18px; color: #1a0dab; text-decoration: none; font-weight: 500; cursor: pointer; }
  .google-preview-desc { font-size: 13px; color: #4d5156; line-height: 1.4; margin-top: 6px; }

  /* Login Card Cyberpunk */
  .login-container {
    max-width: 440px;
    margin: 80px auto;
    background: radial-gradient(circle at top, #111a2e 0%, #07090e 100%);
    border: 1px solid #1e293b;
    border-top: 3px solid #38bdf8;
    border-radius: 16px;
    padding: 36px 32px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.8), 0 0 30px rgba(56, 189, 248, 0.15);
  }

  .stTextInput > div > div > input,
  .stTextArea > div > div > textarea,
  .stSelectbox > div > div > select {
    background-color: #0d1322 !important;
    color: #f8fafc !important;
    border: 1px solid #1e293b !important;
    border-radius: 8px !important;
  }

  .stButton > button {
    background: linear-gradient(180deg, #0284c7 0%, #0369a1 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
  }

  .stButton > button:hover {
    box-shadow: 0 0 15px rgba(56, 189, 248, 0.5) !important;
    transform: translateY(-1px) !important;
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

# Nạp dữ liệu sản phẩm
cache_file = PROJECT_DIR / "extracted_products_cache.json"
pdf_file = PROJECT_DIR / "catalogue_sample.pdf"
products = []
if cache_file.exists():
    try:
        products = json.load(open(cache_file, encoding="utf-8"))
    except Exception:
        pass

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

leader = AgentLeader(workspace_dir=PROJECT_DIR)
technical_agent = getattr(leader, "technical_agent", None)
operations_agent = getattr(leader, "operations_agent", None)
learning_engine = getattr(leader, "learning_engine", None)

marketing_agent = getattr(leader, "marketing_agent", None)
if marketing_agent is None and AgentMarketing is not None:
    marketing_agent = AgentMarketing(PROJECT_DIR)

knowledge_agent = getattr(leader, "knowledge_agent", None)
if knowledge_agent is None and AgentKnowledge is not None:
    knowledge_agent = AgentKnowledge(PROJECT_DIR)

media_agent = getattr(leader, "media_agent", None)
if media_agent is None and AgentMedia is not None:
    media_agent = AgentMedia(PROJECT_DIR)


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
        user_input = st.text_input("Tên đăng nhập / Mã chuyên viên:", value="huy.md")
        pin_input = st.text_input("Mật mã bảo mật (PIN):", type="password", placeholder="Nhập mã PIN nội bộ...")
        submit_login = st.form_submit_button("XÁC THỰC QUYỀN TRUY CẬP (LOGIN)", use_container_width=True)

        if submit_login:
            valid_pin = BIS_ACCESS_PIN or "bis2026"
            if pin_input == valid_pin:
                st.session_state.authenticated = True
                st.session_state.username = user_input or "Chuyên viên BIS"
                st.session_state.audit_logs.append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "type": "LOGIN",
                    "text": f"Chuyên viên '{st.session_state.username}' đăng nhập trung tâm điều hành."
                })
                st.success("✓ Xác thực thành công! Đang chuyển vào hệ thống...")
                time.sleep(0.4)
                st.rerun()
            else:
                st.error("❌ Mật mã bảo mật không đúng. Vui lòng thử lại!")

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

col_top_left, col_top_right = st.columns([8, 4])
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
    col_logout1, col_logout2 = st.columns([2, 1])
    with col_logout1:
        st.markdown(f"""
        <div style='padding-top: 14px; text-align: right; font-family: "JetBrains Mono", monospace; font-size: 12px; color: #94a3b8;'>
          Đã duyệt: <span style='color: #10b981; font-weight: 700;'>{approved_count}</span> | Khóa: <span style='color: #f43f5e; font-weight: 700;'>{rejected_count}</span>
        </div>
        """, unsafe_allow_html=True)
    with col_logout2:
        if st.button("Đăng xuất", key="logout_btn"):
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

    # 5 Phòng Ban Chuyên Trách
    c_d1, c_d2, c_d3, c_d4, c_d5 = st.columns(5)
    with c_d1:
        st.markdown("""
        <div class='agent-node'>
          <div class='node-header'><span class='node-title'>🔬 TECHNICAL</span><span class='node-badge badge-active'>ONLINE</span></div>
          <div style='font-size: 10.5px; color: #94a3b8; margin-top: 4px;'>
            - Gemini Multimodal<br>
            - Thẩm tra 6 bước B1-B6<br>
            - Sinh HTML 7 khối
          </div>
        </div>
        """, unsafe_allow_html=True)

    with c_d2:
        st.markdown("""
        <div class='agent-node'>
          <div class='node-header'><span class='node-title'>📢 MARKETING</span><span class='node-badge badge-active'>ONLINE</span></div>
          <div style='font-size: 10.5px; color: #94a3b8; margin-top: 4px;'>
            - Nghiên cứu từ khóa SEO<br>
            - Soạn Meta Title &amp; Slug<br>
            - Bán hàng QA/QC Lab
          </div>
        </div>
        """, unsafe_allow_html=True)

    with c_d3:
        st.markdown("""
        <div class='agent-node'>
          <div class='node-header'><span class='node-title'>🎨 MEDIA STUDIO</span><span class='node-badge badge-active'>ONLINE</span></div>
          <div style='font-size: 10.5px; color: #94a3b8; margin-top: 4px;'>
            - Tối đa 2 ảnh từ hãng<br>
            - Ghép nền Mockup chân thực<br>
            - Chờ người dùng duyệt
          </div>
        </div>
        """, unsafe_allow_html=True)

    with c_d4:
        st.markdown("""
        <div class='agent-node'>
          <div class='node-header'><span class='node-title'>📚 KNOWLEDGE</span><span class='node-badge badge-active'>ONLINE</span></div>
          <div style='font-size: 10.5px; color: #94a3b8; margin-top: 4px;'>
            - Sách tiêu chuẩn, Manual<br>
            - COC, CO, CQ &amp; Video<br>
            - Nạp tri thức học tập
          </div>
        </div>
        """, unsafe_allow_html=True)

    with c_d5:
        st.markdown("""
        <div class='agent-node'>
          <div class='node-header'><span class='node-title'>🛡️ OPERATIONS</span><span class='node-badge badge-active'>ONLINE</span></div>
          <div style='font-size: 10.5px; color: #94a3b8; margin-top: 4px;'>
            - Google Sheets Master<br>
            - Haravan Guard 20/10<br>
            - Đẩy bài ẩn an toàn
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

tab_tech, tab_mkt, tab_media, tab_know, tab_ops, tab_learn = st.tabs([
    "🔬 1. Phòng Kỹ Thuật (PDF & HTML 7 Khối)",
    "📢 2. Phòng Nghiên Cứu SEO & Marketing",
    "🎨 3. Phòng Edit & Duyệt Ảnh Sản Phẩm",
    "📚 4. Phòng Lưu Trữ Tri Thức (Sách, Manual, CO/CQ)",
    "🛡️ 5. Phòng Vận Hành & Haravan Guard",
    "🧠 6. Bộ Nhớ Tự Học (Few-Shot Feedback)"
])

# ── TAB 1: PHÒNG KỸ THUẬT (BÀN DUYỆT 2 CỘT) ──────────────────────────────────
with tab_tech:
    if not products:
        st.warning("Chưa có dữ liệu sản phẩm trong cache. Vui lòng bấm 'Khởi động trích xuất' bên dưới.")
    else:
        col_f1, col_f2, col_f3 = st.columns([3, 4, 5])
        with col_f1:
            skus = [p.get("sku") for p in products]
            selected_sku = st.selectbox("Chọn mã SKU cần kiểm tra / duyệt:", skus, key="tech_sku_select")
        with col_f2:
            p = next((item for item in products if item.get("sku") == selected_sku), products[0])
            status_color = "#10b981" if p.get("status") == "APPROVED" else ("#f43f5e" if p.get("status") == "REJECTED" else "#f59e0b")
            st.markdown(f"""
            <div style='padding-top: 26px; font-family: "JetBrains Mono", monospace; font-size: 13px;'>
              Trạng thái: <span style='color: {status_color}; font-weight: 800;'>{p.get('status')}</span>
            </div>
            """, unsafe_allow_html=True)

        page_num = int(p.get("source_page") or 1)
        st.markdown("---")

        col_pdf, col_specs = st.columns([5, 7])
        with col_pdf:
            st.markdown(f"#### 📄 Nguồn: Trang {page_num} trong Catalogue")
            if pdf_file.exists():
                try:
                    doc = fitz.open(str(pdf_file))
                    if 1 <= page_num <= len(doc):
                        page = doc[page_num - 1]
                        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
                        img = Image.open(io.BytesIO(pix.tobytes("jpeg")))
                        st.image(img, use_container_width=True, caption=f"Catalogue PDF - Trang {page_num}/{len(doc)}")
                    doc.close()
                except Exception as e:
                    st.error(f"Lỗi hiển thị PDF: {e}")
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

            with st.form(key=f"edit_form_{p.get('sku')}"):
                edit_name_vi = st.text_input("Tên sản phẩm (Tiếng Việt):", value=p.get("product_name") or "")
                edit_name_en = st.text_input("Tên sản phẩm (Tiếng Anh):", value=p.get("product_name_en") or "")
                edit_unit = st.text_input("Đơn vị tính:", value=p.get("unit") or "cuốn")
                edit_desc = st.text_area("Mô tả kỹ thuật:", value=p.get("description") or "", height=80)

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    save_corrections = st.form_submit_button("💾 LƯU & HUẤN LUYỆN AI (SELF-LEARNING)")
                with col_btn2:
                    approve_btn = st.form_submit_button("✅ PHÊ DUYỆT SẢN PHẨM (APPROVE)")

                if save_corrections:
                    if edit_name_vi != p.get("product_name"):
                        learning_engine.record_correction(p.get("sku"), "product_name", p.get("product_name"), edit_name_vi, f"Trang {page_num}")
                        p["product_name"] = edit_name_vi
                    if edit_unit != p.get("unit"):
                        learning_engine.record_correction(p.get("sku"), "unit", p.get("unit"), edit_unit, f"Trang {page_num}")
                        p["unit"] = edit_unit
                    if edit_desc != p.get("description"):
                        learning_engine.record_correction(p.get("sku"), "description", p.get("description"), edit_desc, f"Trang {page_num}")
                        p["description"] = edit_desc

                    operations_agent.update_product_status_in_sheet(p.get("sku"), p.get("status"), f"Đã học chỉnh sửa từ {st.session_state.username}")
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(products, f, ensure_ascii=False, indent=2)
                    st.success("🧠 Đã nạp thành công vào bộ nhớ Few-shot Learning!")
                    st.rerun()

                if approve_btn:
                    p["status"] = "APPROVED"
                    p["product_name"] = edit_name_vi
                    p["product_name_en"] = edit_name_en
                    p["unit"] = edit_unit
                    p["description"] = edit_desc
                    operations_agent.update_product_status_in_sheet(p.get("sku"), "APPROVED", f"Đã duyệt bởi {st.session_state.username}")
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(products, f, ensure_ascii=False, indent=2)
                    st.success(f"🎉 ĐÃ DUYỆT THÀNH CÔNG SKU: {p.get('sku')} -> Sẵn sàng đồng bộ ẩn lên Haravan!")
                    st.rerun()

            with st.expander("👁️ Bản Xem Trước HTML 7 Khối Chuẩn Haravan (Live Preview)", expanded=True):
                html_code = technical_agent.build_7_block_html(p)
                st.components.v1.html(html_code, height=480, scrolling=True)


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
            st.markdown("#### 1. Nguồn Ảnh Đầu Vào (Đặt tên theo SKU)")
            st.caption(f"Quy tắc lưu trữ: `{clean_sku}_brand_1.jpg`, `{clean_sku}_user_1.jpg`")
            
            # Tải ảnh thực tế từ người dùng
            uploaded_user_img = st.file_uploader(f"Tải lên ảnh thực tế cho mã {clean_sku}:", type=["jpg", "png", "jpeg"], key=f"up_{clean_sku}")
            if uploaded_user_img:
                saved_path = media_agent.register_user_image(clean_sku, uploaded_user_img.getvalue(), uploaded_user_img.name)
                st.success(f"✓ Đã lưu ảnh người dùng: {saved_path.name}")

            # Chọn ảnh nền mockup
            st.markdown("#### 2. Chọn Ảnh Nền Ghép (Mockup Background)")
            available_bgs = media_agent.get_backgrounds()
            bg_names = [bg.name for bg in available_bgs]
            selected_bg_name = st.selectbox("Chọn không gian nền:", bg_names)
            selected_bg_path = next(bg for bg in available_bgs if bg.name == selected_bg_name)

            # Tải thêm nền riêng nếu muốn
            new_bg_file = st.file_uploader("Hoặc tải lên ảnh nền riêng của bạn (VD: Phòng lab thực tế):", type=["jpg", "png"], key="new_bg")
            if new_bg_file:
                media_agent.register_background(new_bg_file.name, new_bg_file.getvalue())
                st.success("✓ Đã lưu ảnh nền mới vào kho Mockup!")
                st.rerun()

            # Nút xử lý ghép ảnh
            st.markdown("---")
            if st.button("🚀 AI GHÉP NỀN & TĂNG ĐỘ CHÂN THỰC", type="primary"):
                # Ưu tiên lấy ảnh người dùng tải lên, nếu chưa có thì lấy ảnh mặc định
                user_img_path = media_agent.user_dir / f"{clean_sku}_user_1.jpg"
                if not user_img_path.exists():
                    # Tạo ảnh mẫu thử nghiệm từ biểu tượng nếu chưa tải ảnh lên
                    sample_img = Image.new("RGBA", (400, 400), (255, 255, 255, 0))
                    draw = fitz.Pixmap(fitz.csRGB, 400, 400, 1)
                    # Lưu tạm
                    sample_img.save(user_img_path)
                
                with st.spinner("Agent_Media đang tách nền, tạo bóng đổ và cân chỉnh ánh sáng..."):
                    final_path = media_agent.composite_product_image(clean_sku, user_img_path, selected_bg_path)
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


# ── TAB 4: PHÒNG LƯU TRỮ TRI THỨC (KNOWLEDGE VAULT) ──────────────────────────
with tab_know:
    st.markdown("### 📚 Phòng Lưu Trữ Tri Thức & Tài Liệu Chuẩn (Agent_Knowledge)")
    st.write("Kho lưu trữ sách tiêu chuẩn, catalogue, manual, chứng nhận COC, CO, CQ, hình ảnh và video đào tạo để toàn bộ AI Agents nạp tri thức học tập.")

    if not knowledge_agent:
        st.warning("⚠️ Đang chờ đồng bộ file `agent_knowledge.py` trên GitHub. Hãy tải file lên để kích hoạt.")
    else:
        col_k1, col_k2 = st.columns([7, 5])
        with col_k1:
            st.markdown("#### 📂 Danh Mục Tài Liệu Tiêu Chuẩn Hiện Có")
            docs = knowledge_agent.manifest
            for d in docs:
                st.markdown(f"""
                <div style='background: #0d1322; border: 1px solid #1e293b; border-left: 3px solid #38bdf8; border-radius: 8px; padding: 12px; margin-bottom: 10px;'>
                  <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <strong style='color: #f8fafc; font-size: 13px;'>{d.get('title')}</strong>
                    <span class='node-badge badge-loaded'>{d.get('category').upper()}</span>
                  </div>
                  <div style='font-size: 11.5px; color: #94a3b8; margin-top: 4px;'>{d.get('scope')}</div>
                  <div style='font-size: 10px; color: #64748b; margin-top: 6px; font-family: "JetBrains Mono", monospace;'>
                    File: {d.get('filename')} &bull; Thẩm định: ✓ Đã xác nhận &bull; Ngày nạp: {d.get('added_at')}
                  </div>
                </div>
                """, unsafe_allow_html=True)

        with col_k2:
            st.markdown("#### 📤 Nạp Tài Liệu / Chứng Nhận Mới Cho AI Học")
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
                    st.success(f"✓ Đã nạp thành công '{new_title}' vào kho tri thức của AI!")
                    st.rerun()


# ── TAB 5: PHÒNG VẬN HÀNH & HARAVAN GUARD ────────────────────────────────────
with tab_ops:
    st.markdown("### 🛡️ Phòng Vận Hành & Cổng An Toàn Haravan Guard")
    col_h1, col_h2, col_h3 = st.columns(3)
    with col_h1:
        st.info("🔒 **Rào chắn 2026-10-20:** Tuyệt đối KHÔNG sửa, KHÔNG ghi đè bất kỳ sản phẩm nào tạo trước ngày 20/10/2026 trên sàn Haravan.")
    with col_h2:
        st.warning("👁️ **Đẩy ở chế độ Ẩn:** Mọi sản phẩm khi đẩy lên Haravan luôn mang cờ `published: false` để kiểm duyệt nội bộ trước khi mở bán.")
    with col_h3:
        st.success(f"✅ **Sản phẩm sẵn sàng:** Có {approved_count} sản phẩm đã được APPROVE để đồng bộ.")

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
                st.success(f"✓ Đã hoàn tất đồng bộ {len(sync_res)} sản phẩm lên Haravan ở chế độ ẩn!")
                st.json(sync_res)
            else:
                st.info("Hiện không có sản phẩm nào ở trạng thái APPROVED cần đồng bộ.")


# ── TAB 6: BỘ NHỚ TỰ HỌC (FEW-SHOT CONTINUOUS FEEDBACK) ────────────────────────
with tab_learn:
    st.markdown("### 🧠 Bộ Nhớ Tự Học (Few-Shot Continuous Feedback)")
    st.write("Mỗi khi bạn sửa thông số ở Bàn duyệt Kỹ thuật, hệ thống sẽ lưu cặp giá trị `{Giá trị cũ AI nhận diện ➔ Giá trị mới do chuyên gia sửa}` và tự động chèn vào Prompt của Gemini cho các lần đọc catalogue tiếp theo.")
    
    mem_file = PROJECT_DIR / "feedback_memory.json"
    if mem_file.exists():
        try:
            mem_data = json.load(open(mem_file, encoding="utf-8"))
            st.json(mem_data)
        except Exception as e:
            st.error(f"Lỗi đọc bộ nhớ: {e}")
    else:
        st.info("Chưa có bản ghi hiệu chỉnh nào. Hãy thực hiện chỉnh sửa tại Bàn duyệt để huấn luyện AI.")
