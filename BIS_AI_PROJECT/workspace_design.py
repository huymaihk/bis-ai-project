"""Visual shell for the BIS workspace. Counts describe saved data, never API health."""
from html import escape
import streamlit as st


def apply_theme(light=False):
    palette = ("#f5f4f0", "#ffffff", "#eeede8", "#20242c", "#626978", "#deded8") if light else (
        "#101216", "#191c22", "#22262e", "#f0f1f3", "#a1a8b5", "#303640")
    bg, panel, field, text, muted, line = palette
    st.markdown(f"""<style>
    :root {{ --bis-bg:{bg}; --bis-panel:{panel}; --bis-field:{field}; --bis-text:{text}; --bis-muted:{muted}; --bis-line:{line}; --bis-accent:#ff7156; }}
    .stApp, [data-testid="stAppViewContainer"] {{background:var(--bis-bg)!important;background-image:none!important;color:var(--bis-text)!important;}}
    section[data-testid="stMain"] .block-container {{max-width:1320px;padding:2rem 2.4rem 4rem;}}
    [data-testid="stSidebar"] {{background:var(--bis-panel)!important;border-right:1px solid var(--bis-line);}}
    [data-testid="stHeader"] {{background:var(--bis-bg)!important;}}
    section[data-testid="stMain"] :is(p,label,h1,h2,h3,h4,li), [data-testid="stSidebar"] :is(p,label,h1,h2,h3) {{color:var(--bis-text)!important;}}
    [data-testid="stCaptionContainer"] p {{color:var(--bis-muted)!important;font-size:.82rem;}}
    [data-testid="stForm"], [data-testid="stExpander"] {{background:var(--bis-panel)!important;border:1px solid var(--bis-line)!important;border-radius:16px!important;}}
    [data-testid="stForm"] {{padding:1.3rem!important;}}
    [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea, [data-testid="stNumberInput"] input,
    [data-testid="stSelectbox"] [data-baseweb="select"]>div {{background:var(--bis-field)!important;color:var(--bis-text)!important;border-color:var(--bis-line)!important;border-radius:9px!important;}}
    [data-testid="stFileUploader"] section {{background:var(--bis-panel)!important;border:1px dashed var(--bis-line)!important;border-radius:14px;}}
    .stButton>button, .stDownloadButton>button, [data-testid="stFormSubmitButton"] button {{background:var(--bis-panel)!important;color:var(--bis-text)!important;border:1px solid var(--bis-line)!important;border-radius:9px!important;box-shadow:none!important;transition:border-color .15s;}}
    .stButton>button:hover, .stDownloadButton>button:hover {{border-color:var(--bis-accent)!important;}}
    [data-testid="stFormSubmitButton"] button {{background:#ff7156!important;color:#16181d!important;border-color:#ff7156!important;font-weight:700;}}
    button:disabled {{opacity:.45!important;}}
    [data-baseweb="tab-list"] {{gap:6px;background:var(--bis-panel);padding:7px;border:1px solid var(--bis-line);border-radius:13px;overflow-x:auto;}}
    button[data-baseweb="tab"] {{padding:10px 15px!important;border-radius:8px;color:var(--bis-muted)!important;white-space:nowrap;height:auto!important;}}
    button[data-baseweb="tab"][aria-selected="true"] {{background:var(--bis-field)!important;color:var(--bis-accent)!important;}}
    [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {{display:none;}}
    [data-testid="stTabs"] [data-baseweb="tab-panel"] {{padding-top:1.5rem;}}
    .bis-top {{display:flex;justify-content:space-between;align-items:center;color:var(--bis-muted);font-size:11px;letter-spacing:2px;padding-bottom:20px;border-bottom:1px solid var(--bis-line);}}
    .bis-top strong {{color:var(--bis-text);font-size:15px;letter-spacing:1px;}}
    .bis-top em {{font-style:normal;color:var(--bis-accent);}}
    .bis-hero {{display:grid;grid-template-columns:1.6fr 1fr;gap:35px;padding:32px 0 25px;align-items:center;}}
    .bis-eyebrow {{font-size:11px;letter-spacing:2px;color:var(--bis-muted);}}
    .bis-hero h1 {{font-size:clamp(32px,4vw,54px)!important;line-height:1.08!important;letter-spacing:-2px;font-weight:750;margin:10px 0!important;padding:0!important;}}
    .bis-hero h1 span {{color:var(--bis-accent);}}
    .bis-hero p {{font-size:14px;line-height:1.7;color:var(--bis-muted)!important;max-width:510px;}}
    .bis-orbit {{position:relative;border:1px solid var(--bis-line);border-radius:20px;padding:22px;background:radial-gradient(ellipse at top right,#ff715618,transparent 70%),var(--bis-panel);}}
    .bis-bot {{width:62px;height:49px;border:2px solid var(--bis-accent);border-radius:18px;display:flex;gap:12px;justify-content:center;align-items:center;margin-bottom:18px;box-shadow:0 0 35px #ff71561a;}}
    .bis-bot i {{width:7px;height:13px;background:var(--bis-accent);border-radius:4px;}}
    .bis-orbit strong {{display:block;font-size:17px;color:var(--bis-text);}}
    .bis-orbit small {{display:block;color:var(--bis-muted);line-height:1.6;margin-top:8px;}}
    .bis-stats {{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:24px;}}
    .bis-stat {{border:1px solid var(--bis-line);border-radius:12px;padding:16px 18px;background:var(--bis-panel);}}
    .bis-stat b {{display:block;font-size:27px;letter-spacing:-1px;color:var(--bis-text);}}
    .bis-stat span {{font-size:11px;color:var(--bis-muted);}}
    .bis-brand {{font-size:23px;font-weight:800;letter-spacing:-1px;margin:12px 0 4px;color:var(--bis-text);}}
    .bis-brand span {{color:var(--bis-accent);}}
    .bis-side-label {{font-size:10px;letter-spacing:2px;color:var(--bis-muted);margin:24px 0 12px;}}
    .bis-context {{display:flex;gap:10px;align-items:center;border-left:3px solid var(--bis-accent);padding:12px 15px;background:var(--bis-panel);border-radius:0 9px 9px 0;margin:0 0 20px;}}
    .bis-context strong {{color:var(--bis-text);font-size:14px;}}
    .bis-context span {{color:var(--bis-muted);font-size:12px;}}
    @media(max-width:760px) {{section[data-testid="stMain"] .block-container{{padding:1rem 1rem 3rem;}} .bis-hero{{grid-template-columns:1fr;gap:12px;padding-top:24px;}} .bis-orbit{{display:none;}} .bis-stats{{grid-template-columns:repeat(2,1fr);gap:8px;}} .bis-top{{letter-spacing:0;}} .bis-context{{flex-wrap:wrap;}}}}
    @media(prefers-reduced-motion:reduce) {{*{{transition:none!important;}}}}
    </style>""", unsafe_allow_html=True)


def render_overview(slot, products, sources, manifest):
    values=list(products.values())
    counts=[(len(values),"SẢN PHẨM TRONG KHO"), (len(sources),"TÀI LIỆU NGUỒN"),
            (sum(p.get("status")=="APPROVED" for p in values),"NỘI DUNG ĐÃ DUYỆT"),
            (sum(manifest.get(sku,{}).get("status")=="APPROVED" for sku in products),"ẢNH ĐÃ DUYỆT")]
    cards="".join(f'<div class="bis-stat"><b>{n:02d}</b><span>{label}</span></div>' for n,label in counts)
    slot.markdown('''<div class="bis-top"><strong>BIS<span style="color:#ff7156"> / </span>WORKSPACE</strong><span>TEXTILE INTELLIGENCE <em>↗</em></span></div>
    <div class="bis-hero"><div><div class="bis-eyebrow">YOUR TEAM. ONE WORKSPACE.</div><h1>Từ tài liệu gốc.<br>Đến <span>sản phẩm chuẩn.</span></h1><p>Không gian làm việc chung cho dữ liệu, nội dung và hình ảnh.<br>Chọn sản phẩm ở thanh bên, rồi tiếp tục từng bước bên dưới.</p></div>
    <div class="bis-orbit"><div class="bis-bot" aria-hidden="true"><i></i><i></i></div><strong>Cùng một nguồn. Cùng một mục tiêu.</strong><small>Technical → Marketing → Studio → Operations<br>Tri thức và lịch sử theo suốt quá trình làm việc.<br>Các tác vụ chạy khi bạn yêu cầu.</small></div></div>'''+f'<div class="bis-stats">{cards}</div>',unsafe_allow_html=True)


def product_context(product):
    if product:
        name=escape(str(product.get("product_name") or product.get("product_name_en") or "Chưa có tên"))
        sku=escape(str(product.get("sku") or ""))
        state={"APPROVED":"Nội dung đã duyệt","EXTRACTED_UNVERIFIED":"Cần kiểm tra","REJECTED":"Đã từ chối"}.get(product.get("status"),"Bản làm việc")
        st.markdown(f'<div class="bis-context"><strong>{sku}</strong><span> / </span><strong>{name}</strong><span>· {state}</span></div>',unsafe_allow_html=True)
