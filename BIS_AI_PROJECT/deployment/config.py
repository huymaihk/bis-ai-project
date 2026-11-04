"""Container-only configuration: values must come from the hosting secret store."""
import os
BIS_ACCESS_PIN = os.environ['BIS_ACCESS_PIN']
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY','')
HARAVAN_TOKEN = os.getenv('HARAVAN_TOKEN','')
HARAVAN_SHOP = os.getenv('HARAVAN_SHOP','')
HARAVAN_PUSH_ENABLED = False
SPREADSHEET_ID_OR_URL = os.getenv('BIS_MEMORY_SHEET_ID','')
SPREADSHEET_NAME = 'BIS_Textile_Product_Master'
SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_APPLICATION_CREDENTIALS','/run/secrets/service_account.json')

SHEET_PRODUCTS = 'PRODUCTS'

STATUS_EXTRACTED = 'EXTRACTED_UNVERIFIED'

STATUS_APPROVED = 'APPROVED'

PRODUCT_COLUMNS = ['product_id', 'status', 'source_page', 'product_name', 'product_name_en', 'sku', 'category', 'material', 'color', 'width_cm', 'weight_gsm', 'pattern', 'finish', 'description', 'price_vnd', 'price_usd', 'min_order_qty', 'unit', 'image_urls', 'haravan_product_id', 'created_at', 'updated_at', 'notes']
