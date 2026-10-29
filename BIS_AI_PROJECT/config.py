"""
BIS Textile Pipeline - Configuration
"""
import os
from datetime import date

# ── API Keys & Cloud Secrets ───────────────────────────────────────────────────
# Tự động đọc từ Streamlit Secrets hoặc Biến môi trường khi đưa lên Cloud 24/7
try:
    import streamlit as st
    _secrets = dict(st.secrets) if hasattr(st, "secrets") else {}
except Exception:
    _secrets = {}

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or _secrets.get("GEMINI_API_KEY") or "AQ.Ab8RN6IuMDc_qMv15Kx6fgW3Fc4-yXdmbV6uIN2sYC9Ve2GrMw"
HARAVAN_TOKEN  = os.environ.get("HARAVAN_TOKEN") or _secrets.get("HARAVAN_TOKEN") or "8651987CA6839C2F9131175200D9542DD046AF86EF211FF46AA34E54377B691D"
HARAVAN_SHOP   = os.environ.get("HARAVAN_SHOP") or _secrets.get("HARAVAN_SHOP") or "BIS TEXTILE N8N PRODUCT SYNC"
BIS_ACCESS_PIN = os.environ.get("BIS_ACCESS_PIN") or _secrets.get("BIS_ACCESS_PIN") or "1133"

# ── Google Sheets ─────────────────────────────────────────────────────────────
SPREADSHEET_NAME      = "BIS_Textile_Product_Master"
SPREADSHEET_ID_OR_URL = "https://docs.google.com/spreadsheets/d/1AK4zau1LlfNPl2r4V_0RULwMXwUQ3F5_SKEoVHrZJFM/edit"
SHEET_PRODUCTS        = "PRODUCTS"
SERVICE_ACCOUNT_FILE  = "service_account.json"  # same dir as main_pipeline.py

# ── Haravan Guard Rail ────────────────────────────────────────────────────────
# Pipeline WILL NOT push to Haravan automatically.
# Push only happens when user explicitly calls push_to_haravan()
# after reviewing APPROVED products in Google Sheets.
HARAVAN_PUSH_ENABLED = False   # set True only when user manually enables

# ── Google Gemini Model ───────────────────────────────────────────────────────
# gemini-3.8-flash: multimodal, fast, high free quota — confirmed working
GEMINI_MODEL         = "gemini-3.8-flash"
GEMINI_MODEL_PRO     = "gemini-3.1-pro-preview"   # higher quality, lower quota
MAX_WORKERS          = 5                          # Concurrent extraction threads

# ── Status constants ──────────────────────────────────────────────────────────
STATUS_EXTRACTED   = "EXTRACTED_UNVERIFIED"
STATUS_APPROVED    = "APPROVED"
STATUS_PUSHED      = "PUSHED_TO_HARAVAN"
STATUS_REJECTED    = "REJECTED"

# ── Column layout for PRODUCTS sheet ─────────────────────────────────────────
PRODUCT_COLUMNS = [
    "product_id",           # auto-generated UUID
    "status",               # EXTRACTED_UNVERIFIED | APPROVED | REJECTED | PUSHED_TO_HARAVAN
    "source_page",          # PDF page number
    "product_name",
    "product_name_en",
    "sku",
    "category",
    "material",
    "color",
    "width_cm",
    "weight_gsm",
    "pattern",
    "finish",
    "description",
    "price_vnd",
    "price_usd",
    "min_order_qty",
    "unit",
    "image_urls",           # comma-separated
    "haravan_product_id",   # filled after push
    "created_at",
    "updated_at",
    "notes",
]

