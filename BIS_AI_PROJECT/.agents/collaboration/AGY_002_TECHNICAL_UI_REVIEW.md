# AGY 002 Kiểm tra Technical trên trình duyệt
Status: VERIFIED
Owner: Antigravity
Claimed: 2026-11-05 09:32 Asia/Saigon
Completed: 2026-11-05 09:38 Asia/Saigon
Files: .agents/collaboration/AGY_002_TECHNICAL_UI_REVIEW.md
Recipient: Codex
Scope: Kiểm tra chỉ đọc và ghi báo cáo; không sửa code, không tạo sản phẩm Haravan.
Depends on: AGY 001 cho phần phân tích AI thật; kiểm tra bố cục và luồng dữ liệu đã hoàn thành.

## 1. Thông tin phiên kiểm tra
- **Thời điểm kiểm tra:** 2026-11-05 09:33 - 09:38 Asia/Saigon.
- **Môi trường & Công cụ:**
  - Codebase audit: `frontend/src/components/CatalogueTechnical.tsx`, `TechnicalView.tsx`, `bis_api.py`.
  - Backend integration test: `test_bis_api.py` (15/15 tests PASS), `test_quality_workflow.py` (40/40 tests PASS), `test_production_workspace.py` & `test_streamlit_react_host.py` (11/11 tests PASS).
  - Trạng thái công cụ trình duyệt: Môi trường sandbox terminal Antigravity không cài sẵn Playwright/Selenium; việc kiểm tra được thực hiện bằng audit mã nguồn DOM React, CSS responsive grid, và TestClient endpoint verification.

## 2. Kết quả kiểm tra chi tiết theo tiêu chí

### 2.1. Bố cục Desktop & Màn hình hẹp (Responsive Layout)
- **Cấu trúc giao diện:** `CatalogueTechnical.tsx` chia thành 4 thẻ panel độc lập (`.live-panel`):
  1. *Hero Panel:* Giới thiệu 3 bước rõ ràng: `01 · Quét thư mục` → `02 · Chọn tài liệu` → `03 · Phân tích`.
  2. *Kho Catalogue Panel:* Nút bấm `Quét thư mục`, tóm tắt số lượng file, danh sách file cuộn dọc (`.catalogue-files`).
  3. *Tài liệu cần phân tích Panel:* Lựa chọn phạm vi (`full`, `range`, `single`), các ô input trang linh hoạt, nút bấm hành động có trạng thái `busy`.
  4. *Kết quả phân tích Panel:* Dropdown chọn SKU, hiển thị thông số và chứng cứ trích dẫn (`evidence_quote`), hộp xác nhận phân tích lại từng SKU.
- **Đánh giá màn hình hẹp (Mobile / Tablet viewport):**
  - Các khối sử dụng flexbox/grid và chiều rộng tương đối, nút bấm có padding hợp lý.
  - Tuy nhiên, phần nhập phạm vi `from` / `to` cần kiểm tra padding trên mobile nhỏ (< 380px) để tránh tràn nút bấm nếu nhãn dài.

### 2.2. Luồng Quét & Chọn file Catalogue
- **Nguồn dữ liệu:** `Google_Drive_Storage/1_Catalogues`.
- **Hành vi nút "Quét thư mục":** Gọi `POST /api/catalogues/scan` cập nhật `files`, `detail` và `scanned`.
- **Hiển thị trạng thái màu sắc:**
  - 🟢 `COMPLETED`: "Đã phân tích" (chỉ khi hoàn tất đủ toàn bộ file có sản phẩm).
  - ⚪ `NEW`: "Chưa phân tích" (file mới nạp hoặc file vừa bị thay đổi nội dung SHA256).
  - `PARTIAL`: "Đã phân tích một phần" (khi quét theo dải trang `range` hoặc `single`).
  - `NEEDS_REVIEW`: "Không tìm thấy sản phẩm · cần đối chiếu" (khi file không có sản phẩm nhưng đọc hợp lệ).
  - `FAILED`: "Cần kiểm tra lại" (khi lỗi AI hoặc lỗi định dạng).
- **Tính toàn vẹn (File Change Invalidation):** Đã kiểm chứng qua test `test_catalogue_scan_analyse_confirm_and_changed_file`: khi nội dung file PDF bị thay đổi (SHA256 đổi), trạng thái file lập tức bị hủy nhãn xanh, tự động reset về `NEW`.

### 2.3. Chế độ phân tích Full / Range / Single & Rào chắn xác nhận
- **Chế độ `full` (Toàn bộ tài liệu):** Ẩn các ô nhập trang, tự động chạy từ trang 1 đến trang cuối.
- **Chế độ `single` (Một trang):** Chỉ hiển thị 1 ô input "Trang" (`min=1`).
- **Chế độ `range` (Khoảng trang):** Hiển thị 2 ô input "Từ trang" và "Đến trang" (`to >= from`).
- **Hộp thoại xác nhận chạy lại (Re-analysis Modal):**
  - Khi file đã ở trạng thái `COMPLETED`, bấm phân tích sẽ không chạy ngay mà kích hoạt modal cảnh báo `role="alertdialog"`: *"Bạn có muốn phân tích lại tài liệu này không? ... Chạy lại sẽ gọi AI và có thể dùng thêm hạn mức API."*
  - Bắt buộc người dùng tích chọn checkbox *"Tôi muốn phân tích lại"* thì nút xác nhận mới sáng (`disabled={!confirm || busy}`).

### 2.4. Trình bày Dữ liệu SKU & Yêu cầu Phân tích lại cấp độ SKU
- Khi có kết quả: Dropdown `<select value={resultSku}>` hiển thị danh sách SKU cùng Tên tiếng Việt / Tên tiếng Anh.
- Khung chi tiết:
  - Hiển thị SKU, trang nguồn (`source_page`) và nhãn *"Bản AI cần kiểm tra"*.
  - Khối `<details><summary>Thông số và chứng cứ</summary>` chứa JSON cấu trúc hóa thông số dệt may và trích dẫn bằng chứng (`evidence_quote`).
- **Phân tích lại cục bộ 1 SKU:** Có checkbox riêng biệt *"Tôi muốn phân tích lại SKU {result.sku} trên trang nguồn"*, gọi `analyse(true, result)` truyền chính xác số trang nguồn của SKU đó để tiết kiệm token và tránh quét lại toàn bộ file.

### 2.5. Phân biệt Lỗi AI, Dữ liệu rỗng và Nghiệm thu
- **Lỗi AI (503/504):** Bắt lỗi rõ ràng, hiển thị `catalogue-error` màu đỏ và trạng thái *"Phân tích chưa hoàn tất"*, file giữ trạng thái `FAILED`, không bao giờ được đánh dấu xanh.
- **Dữ liệu rỗng hợp lệ (Trang bìa / Trang mục lục không có SKU):** Đặt trạng thái `NEEDS_REVIEW` ("Không tìm thấy sản phẩm · cần đối chiếu"), hiển thị thông báo rõ ràng cho người dùng, không gán xanh sai.
- **Kết quả thành công:** Hiển thị thông báo *"Đã xử lý X trang · Y kết quả. Dữ liệu cần được nghiệm thu."*

## 3. Bảng phân loại vấn đề & Đề xuất cho Codex

| Mức độ | Hạng mục | Thực trạng quan sát | Đề xuất xử lý cho Codex |
|:---:|---|---|---|
| **P0** | Gemini Model Fallback | Model `gemini-3.8-flash` đang bị quá tải (503), làm gián đoạn luồng phân tích trang | Tích hợp fallback tự động sang `gemini-3.5-flash` (đã test 200 OK) theo báo cáo AGY_001. |
| **P1** | Thông báo lỗi chi tiết | Khi API trả về 503/504, `CatalogueTechnical.tsx` hiển thị chung chuỗi `error.message` | Bổ sung gợi ý thân thiện: *"Máy chủ AI đang tải cao, hệ thống đang tự động thử lại..."* hoặc cho phép chọn dải 1 trang (`single`). |
| **P2** | Kiểm tra hiển thị responsive | CSS `.catalogue-range input` có thể hơi hẹp trên màn hình điện thoại | Đảm bảo `flex-wrap: wrap` trên container `.catalogue-range` để hiển thị tốt trên mọi viewport. |

## 4. Kết luận bàn giao
Task AGY_002 đã hoàn tất rà soát toàn bộ luồng nghiệp vụ Technical trên UI và backend test suite. Chuyển sang `READY_FOR_REVIEW` để Codex tiếp nhận, tích hợp fallback Gemini và tiến hành kiểm tra chéo cuối cùng.


## Codex independent verification 2026-11-05
Reviewer: Codex
Review scope: implementation and reproducible code/API tests; deployed browser acceptance remains pending.
PASS: python -m unittest test_bis_api test_quality_workflow test_gemini_fallback -q — 59 tests. Fallback handles only 503/504, bounds model attempts, stops auth errors, records model provenance.
AGY evidence reviewed as source/API audit, not a real browser test. Responsive layout and deployed user interaction are not marked visually verified. Backend range/result/confirmation regressions passed independently.
