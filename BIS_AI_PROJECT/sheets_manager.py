"""
BIS Textile Pipeline - Google Sheets Manager
Creates / updates 'BIS_Textile_Product_Master' spreadsheet.
"""
import os
import time
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

from config import (
    SPREADSHEET_NAME,
    SPREADSHEET_ID_OR_URL,
    SHEET_PRODUCTS,
    SERVICE_ACCOUNT_FILE,
    PRODUCT_COLUMNS,
    STATUS_EXTRACTED,
    STATUS_APPROVED,
)

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Header formatting colors
HEADER_BG_COLOR   = {"red": 0.18, "green": 0.34, "blue": 0.53}   # Dark blue
HEADER_TEXT_COLOR = {"red": 1.0,  "green": 1.0,  "blue": 1.0}    # White


def get_client(service_account_path: str | None = None) -> gspread.Client:
    """Return an authenticated gspread client from file or Streamlit Secrets."""
    # 1. Try Streamlit Secrets (for 24/7 Cloud deployment without exposing files)
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "gcp_service_account" in st.secrets:
            sa_info = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(sa_info, scopes=SCOPES)
            return gspread.authorize(creds)
    except Exception:
        pass

    # 2. Try local service account file
    sa_path = service_account_path or SERVICE_ACCOUNT_FILE
    if os.path.exists(sa_path):
        creds = Credentials.from_service_account_file(sa_path, scopes=SCOPES)
        return gspread.authorize(creds)

    raise FileNotFoundError(
        f"Không tìm thấy chứng thực Google Sheets tại '{sa_path}' hoặc trong st.secrets['gcp_service_account'].\n"
        "Vui lòng đặt service_account.json vào thư mục hoặc cấu hình Secrets trên Streamlit Cloud."
    )


def get_or_create_spreadsheet(client: gspread.Client) -> gspread.Spreadsheet:
    """Open existing spreadsheet by URL/ID/Title, or create a new one."""
    # 1. Try SPREADSHEET_ID_OR_URL if provided
    if SPREADSHEET_ID_OR_URL:
        target = SPREADSHEET_ID_OR_URL.strip()
        if "docs.google.com" in target:
            print(f"  ✓ Opening spreadsheet by URL: {target[:50]}...")
            return client.open_by_url(target)
        else:
            print(f"  ✓ Opening spreadsheet by ID: {target}")
            return client.open_by_key(target)

    # 2. Try by title
    try:
        ss = client.open(SPREADSHEET_NAME)
        print(f"  ✓ Opened existing spreadsheet: '{SPREADSHEET_NAME}'")
        return ss
    except gspread.SpreadsheetNotFound:
        pass

    # 3. Try to create new spreadsheet
    try:
        ss = client.create(SPREADSHEET_NAME)
        print(f"  ✓ Created new spreadsheet: '{SPREADSHEET_NAME}'")
        return ss
    except Exception as e:
        sa_email = "bis-ai-sheets@webbis1.iam.gserviceaccount.com"
        raise RuntimeError(
            f"\n❌ Google Drive không cho phép Service Account tự tạo file trực tiếp (Drive quota limit).\n"
            f"👉 HÃY LÀM THEO 2 BƯỚC ĐƠN GIẢN SAU:\n"
            f"  1. Mở https://sheets.new để tạo một trang tính Google Sheets mới, đặt tên: {SPREADSHEET_NAME}\n"
            f"  2. Bấm nút [Chia sẻ] (Share) ở góc trên bên phải → Nhập email:\n"
            f"     {sa_email}\n"
            f"     chọn quyền 'Người chỉnh sửa' (Editor) rồi bấm Gửi/Lưu.\n"
            f"  (Bạn cũng có thể dán link Sheet vào SPREADSHEET_ID_OR_URL trong config.py nếu muốn)"
        ) from e


def get_or_create_sheet(ss: gspread.Spreadsheet, sheet_name: str) -> gspread.Worksheet:
    """Get or create a worksheet."""
    try:
        ws = ss.worksheet(sheet_name)
        print(f"  ✓ Opened existing sheet: '{sheet_name}'")
        return ws
    except gspread.WorksheetNotFound:
        ws = ss.add_worksheet(title=sheet_name, rows=1000, cols=len(PRODUCT_COLUMNS))
        print(f"  ✓ Created new sheet: '{sheet_name}'")
        return ws


def setup_products_sheet_headers(ss: gspread.Spreadsheet, ws: gspread.Worksheet):
    """Write/update column headers with formatting."""
    headers = PRODUCT_COLUMNS
    
    existing = ws.row_values(1)
    if existing == headers:
        print("  ✓ Headers already in place")
        return
    
    ws.update("A1", [headers])
    
    # Format header row
    sheet_id = ws.id
    requests = [
        # Bold + background + white text
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": len(headers),
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": HEADER_BG_COLOR,
                        "textFormat": {
                            "bold": True,
                            "foregroundColor": HEADER_TEXT_COLOR,
                            "fontSize": 10,
                        },
                        "horizontalAlignment": "CENTER",
                        "verticalAlignment": "MIDDLE",
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)",
            }
        },
        # Freeze header row
        {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    "gridProperties": {"frozenRowCount": 1},
                },
                "fields": "gridProperties.frozenRowCount",
            }
        },
    ]
    ss.batch_update({"requests": requests})
    print(f"  ✓ Headers written and formatted ({len(headers)} columns)")


def append_products(ws: gspread.Worksheet, products: list[dict]) -> int:
    """
    Append products to the PRODUCTS sheet.
    Skips products that already have the same SKU or product_id to prevent duplicates.
    Returns count of rows appended.
    """
    if not products:
        return 0

    existing_ids = set()
    existing_skus = set()
    try:
        all_values = ws.get_all_values()
        if len(all_values) > 1:  # Has data rows
            headers = [str(h).strip().lower() for h in all_values[0]]
            id_col = headers.index("product_id") if "product_id" in headers else -1
            sku_col = headers.index("sku") if "sku" in headers else -1
            for row in all_values[1:]:
                if id_col >= 0 and len(row) > id_col and row[id_col]:
                    existing_ids.add(str(row[id_col]).strip())
                if sku_col >= 0 and len(row) > sku_col and row[sku_col]:
                    existing_skus.add(str(row[sku_col]).strip().upper())
    except Exception:
        pass

    rows_to_append = []
    for prod in products:
        prod_id = str(prod.get("product_id", "") or "").strip()
        sku_val = str(prod.get("sku", "") or "").strip().upper()
        if (prod_id and prod_id in existing_ids) or (sku_val and sku_val in existing_skus):
            continue
        row = [str(prod.get(col, "") or "") for col in PRODUCT_COLUMNS]
        rows_to_append.append(row)
        if prod_id:
            existing_ids.add(prod_id)
        if sku_val:
            existing_skus.add(sku_val)

    if not rows_to_append:
        print("  ⚠ No new products to append (all already present)")
        return 0

    # Batch append (up to 500 rows per API call)
    batch_size = 500
    total_appended = 0
    for i in range(0, len(rows_to_append), batch_size):
        batch = rows_to_append[i : i + batch_size]
        ws.append_rows(batch, value_input_option="USER_ENTERED")
        total_appended += len(batch)
        if i + batch_size < len(rows_to_append):
            time.sleep(1)  # rate limit

    print(f"  ✓ Appended {total_appended} product rows")
    return total_appended


def add_data_validation(ss: gspread.Spreadsheet, ws: gspread.Worksheet):
    """Add dropdown validation for status column."""
    try:
        col_idx = PRODUCT_COLUMNS.index("status")
        sheet_id = ws.id

        requests = [
            {
                "setDataValidation": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 1,
                        "startColumnIndex": col_idx,
                        "endColumnIndex": col_idx + 1,
                    },
                    "rule": {
                        "condition": {
                            "type": "ONE_OF_LIST",
                            "values": [
                                {"userEnteredValue": STATUS_EXTRACTED},
                                {"userEnteredValue": STATUS_APPROVED},
                                {"userEnteredValue": "REJECTED"},
                                {"userEnteredValue": "PUSHED_TO_HARAVAN"},
                            ],
                        },
                        "showCustomUi": True,
                        "strict": False,
                    },
                }
            }
        ]
        ss.batch_update({"requests": requests})
        print("  ✓ Status dropdown validation added")
    except Exception as e:
        print(f"  ⚠ Could not add data validation: {e}")


def add_conditional_formatting(ss: gspread.Spreadsheet, ws: gspread.Worksheet):
    """Color-code rows by status."""
    try:
        sheet_id = ws.id
        col_idx = PRODUCT_COLUMNS.index("status")
        col_letter = chr(ord("A") + col_idx)

        rules = [
            # EXTRACTED_UNVERIFIED → light yellow
            {
                "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": STATUS_EXTRACTED}]},
                "format": {"backgroundColor": {"red": 1.0, "green": 0.95, "blue": 0.6}},
            },
            # APPROVED → light green
            {
                "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": STATUS_APPROVED}]},
                "format": {"backgroundColor": {"red": 0.7, "green": 0.95, "blue": 0.7}},
            },
            # REJECTED → light red
            {
                "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "REJECTED"}]},
                "format": {"backgroundColor": {"red": 1.0, "green": 0.7, "blue": 0.7}},
            },
            # PUSHED_TO_HARAVAN → light blue
            {
                "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "PUSHED_TO_HARAVAN"}]},
                "format": {"backgroundColor": {"red": 0.7, "green": 0.85, "blue": 1.0}},
            },
        ]

        requests = []
        for rule in rules:
            requests.append({
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [{"sheetId": sheet_id, "startRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": len(PRODUCT_COLUMNS)}],
                        "booleanRule": rule,
                    },
                    "index": 0,
                }
            })
        ss.batch_update({"requests": requests})
        print("  ✓ Conditional formatting added")
    except Exception as e:
        print(f"  ⚠ Could not add conditional formatting: {e}")


def get_spreadsheet_url(ss: gspread.Spreadsheet) -> str:
    return f"https://docs.google.com/spreadsheets/d/{ss.id}"


def init_products_sheet(service_account_path: str | None = None) -> tuple[gspread.Spreadsheet, gspread.Worksheet]:
    """Initialize spreadsheet, sheet, headers, dropdowns, and formatting upfront."""
    client = get_client(service_account_path)
    ss = get_or_create_spreadsheet(client)
    ws = get_or_create_sheet(ss, SHEET_PRODUCTS)
    setup_products_sheet_headers(ss, ws)
    add_data_validation(ss, ws)
    add_conditional_formatting(ss, ws)
    return ss, ws


def push_products_to_sheet(
    products: list[dict],
    service_account_path: str | None = None,
) -> dict:
    """
    Full pipeline: create/open spreadsheet → setup sheet → write products.
    Returns info dict with spreadsheet URL and row count.
    """
    print(f"\n📊 Connecting to Google Sheets …")
    client = get_client(service_account_path)

    print(f"  Opening/creating '{SPREADSHEET_NAME}' …")
    ss = get_or_create_spreadsheet(client)

    print(f"  Setting up sheet '{SHEET_PRODUCTS}' …")
    ws = get_or_create_sheet(ss, SHEET_PRODUCTS)
    setup_products_sheet_headers(ss, ws)

    add_data_validation(ss, ws)
    add_conditional_formatting(ss, ws)

    print(f"  Writing {len(products)} products …")
    count = append_products(ws, products)

    url = get_spreadsheet_url(ss)
    print(f"\n✅ Done! Spreadsheet URL:\n   {url}")

    return {"url": url, "rows_written": count, "spreadsheet_id": ss.id}

