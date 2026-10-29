# BIS Textile Pipeline

## Cấu trúc dự án
```
BIS_AI_PROJECT/
├── main_pipeline.py         ← Entry point chính
├── extractor.py             ← PDF → Gemini 1.5 Pro → Products
├── sheets_manager.py        ← Quản lý Google Sheets
├── haravan_uploader.py      ← Đẩy lên Haravan (có rào chắn)
├── config.py                ← Cấu hình API keys, constants
├── requirements.txt         ← Thư viện cần thiết
├── catalogue_sample.pdf     ← File PDF cần xử lý (bạn tự đặt vào)
└── service_account.json     ← Google Service Account (bạn tự đặt vào)
```

## Cài đặt

```bash
pip install -r requirements.txt
# Tùy chọn: để đọc PDF tốt hơn
pip install pymupdf
```

## Chạy pipeline

```bash
# Trích xuất PDF → Google Sheets (mặc định)
python main_pipeline.py

# Chỉ định PDF khác
python main_pipeline.py --pdf "D:/catalogues/spring2026.pdf"

# Đẩy sản phẩm APPROVED lên Haravan (sau khi review)
python main_pipeline.py --haravan-push
```

## Quy trình duyệt sản phẩm

1. Chạy `python main_pipeline.py` → tất cả sản phẩm vào Sheets với status `EXTRACTED_UNVERIFIED`
2. Mở Google Sheets: **BIS_Textile_Product_Master** → sheet **PRODUCTS**
3. Review từng sản phẩm:
   - Đổi status → `APPROVED` (sẽ push lên Haravan)
   - Đổi status → `REJECTED` (bỏ qua)
4. Trong `config.py`, đặt `HARAVAN_PUSH_ENABLED = True`
5. Chạy `python main_pipeline.py --haravan-push`

## Rào chắn an toàn Haravan

| Điều kiện | Kết quả |
|-----------|---------|
| `HARAVAN_PUSH_ENABLED = False` | 🚫 Không push, dừng lại |
| Không có flag `--haravan-push` | ⏭ Bỏ qua Haravan |
| Product status ≠ `APPROVED` | ⏭ Bỏ qua product đó |
| Tất cả điều kiện đúng | ✅ Push lên Haravan |

