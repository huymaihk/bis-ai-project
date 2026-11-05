# AGY 006 Copy SEO and SKU image acceptance
Status: VERIFIED
Owner: Antigravity
Recipient: Codex
Scope: browser acceptance with temporary test data; no Haravan mutations.

## 1. Môi trường & Bối cảnh kiểm tra
- **Thời điểm kiểm tra:** 2026-11-05 18:05 (GMT+7)
- **Môi trường:** Streamlit Cloud (`https://bis-ai-project-fkagnq4aul3fejrxutdhfx.streamlit.app/~/+/`)
- **Tài khoản / PIN:** Đăng nhập PIN [REDACTED]
- **Commit kiểm tra:** `44bd912` (Giao thức mã nguồn `workflow-v2-13` (Codex đối chiếu commit; báo cáo ban đầu ghi v2-12))
- **Rào chắn an toàn:** Chỉ dùng dữ liệu thử cho thao tác lưu; không lưu dữ liệu thử vào bản nháp sản phẩm thật; tuyệt đối không gọi API Haravan.

---

## 2. Bảng đối chiếu tiêu chí nghiệm thu (Cloud Acceptance)

| STT | Tiêu chí kiểm tra | Kết quả thực tế quan sát trên Cloud | Trạng thái | Bằng chứng |
|:---:|:---|:---|:---:|:---|
| **1** | **Mô tả SKU 03026A rút gọn (250–450 ký tự)** | Đoạn mô tả đạt **323 ký tự** (nằm trong mục tiêu 250–450 ký tự): `Sổ tay AATCC Manual of International Test Methods and Procedures tập hợp các phương pháp thử, quy trình phòng thí nghiệm...`. Bộ đếm hiển thị `323 ký tự`. Nút *Gợi ý rút gọn và bỏ đặc điểm lặp ý* hoạt động. | **PASS** | `agy006_mkt_copy_seo.png`<br>`agy006_cloud_verification.json` |
| **2** | **Đặc điểm nổi bật không lặp ý (Non-repeating highlights)** | 2 điểm nổi bật ngắn gọn, bám sát catalogue trang 7 và **hoàn toàn không lặp lại câu văn trong mô tả**:<br>1. *Mã 03026A là sách bìa cứng; bản tải PDF có mã riêng 03026B.*<br>2. *Cập nhật hằng năm; catalogue ghi ấn phẩm năm 2026 là lần xuất bản thứ 100.* | **PASS** | `agy006_mkt_copy_seo.png`<br>`agy006_cloud_verification.json` |
| **3** | **3 trường SEO độc lập & giới hạn máy chủ** | Hiển thị 3 trường SEO chuẩn hóa kèm bộ đếm giới hạn:<br>• `meta_title`: Tiêu đề trang (58/70 ký tự, max 70)<br>• `meta_description`: Mô tả trang (0/320 ký tự, max 320)<br>• `url_slug`: `aatcc-manual-of-international-test-metho-03026a`<br>Các nút gợi ý tiêu đề từ bản lưu hoạt động ngay tại chỗ. Server trả về HTTP 422 nếu vượt giới hạn độ dài hoặc chứa ký tự xấu. | **PASS** | `agy006_mkt_copy_seo.png`<br>`test_bis_api.py` (76 PASS) |
| **4** | **Xem trước SERP có nhãn minh họa** | Khung xem trước tìm kiếm Google hiển thị rõ nhãn: `Xem trước tìm kiếm · minh họa, Google có thể hiển thị khác`. Hiển thị tiêu đề, mô tả và đường dẫn `https://bistextile.com/products/...`. | **PASS** | `agy006_mkt_copy_seo.png` |
| **5** | **Images tab: Bộ chọn SKU theo phạm vi** | Tab Images không còn dùng gallery ảnh chung chung, mà mở đầu bằng bộ chọn SKU: `Chọn mã sản phẩm để tìm ảnh` với danh sách đầy đủ 97 SKU kèm tên tiếng Anh. Tiêu đề hiển thị: `Tìm ảnh theo SKU 03026A`. | **PASS** | `agy006_images_sku_search.png`<br>`agy006_cloud_verification.json` |
| **6** | **Trích xuất ảnh PDF đúng trang của SKU** | Khi chọn `catalogue_sample.pdf` và bấm *Tìm ảnh trong PDF / link đã nhập* cho 03026A: Hệ thống tìm kiếm và trích xuất chính xác 2 ảnh ứng viên từ **Trang 7** (trang chứa SKU 03026A trong catalogue). | **PASS** | `agy006_images_sku_search.png`<br>`agy006_cloud_verification.json` |
| **7** | **Tên tiếng Anh hiển thị dưới ảnh** | Bên dưới mỗi ảnh ứng viên hiển thị rõ tên tiếng Anh in đậm: `<strong>AATCC MANUAL OF INTERNATIONAL TEST METHODS AND PROCEDURES (Hardbound Book)</strong>`. | **PASS** | `agy006_images_sku_search.png` |
| **8** | **Lưu link web nguồn (tối đa 5 link/SKU)** | Trường `Link trang web nguồn · mỗi dòng một link, tối đa 5` được lưu trữ riêng biệt theo SKU thông qua endpoint `/api/products/{sku}/image-links`. Giới hạn tối đa 5 link và chặn URL private/nội bộ. | **PASS** | `agy006_cloud_verification.json`<br>`test_bis_api.py` |
| **9** | **Ảnh cùng trang giữ nguyên trạng thái chưa xác nhận** | Mỗi ảnh ứng viên được gán nhãn rõ ràng: `SKU mục tiêu: 03026A · Trang 7 · Chưa xác nhận đúng ảnh` cùng thông báo: `Ảnh ứng viên: cùng trang hoặc link chưa chứng minh đúng sản phẩm. Chọn sau khi đối chiếu.` | **PASS** | `agy006_images_sku_search.png` |
| **10** | **Tải ảnh ứng viên & Chọn làm ảnh nguồn** | Mỗi thẻ ảnh có nút `Mở / tải ảnh` (tải blob qua AssetLink an toàn). Nút radio `Tôi đã đối chiếu ảnh này với sản phẩm` kích hoạt nút `Chọn làm ảnh nguồn`. Khi chọn, ảnh được gán trạng thái `SOURCE_SELECTED_NOT_APPROVED` để đưa vào studio xử lý ảnh. | **PASS** | `agy006_images_sku_search.png`<br>`test_bis_api.py` |
| **11** | **Loại bỏ thư viện ảnh toàn cục không liên quan** | Giao diện Images tab loại bỏ hoàn toàn `.live-gallery` hiển thị ảnh lộn xộn; 100% hiển thị theo phạm vi SKU đã chọn (`hasGlobalGallery: False`). | **PASS** | `agy006_images_sku_search.png` |
| **12** | **Cơ chế tìm ảnh web là xếp hạng HTML/Metadata** | `image_sources.py` sử dụng phân tích thẻ `<img>` và `<meta property="og:image">` từ HTML công khai rồi xếp hạng theo heuristic, không giả lập AI visual verification. | **PASS** | `image_sources.py` |
| **13** | **An toàn Haravan & Kiểm thử tự động** | Không lưu dữ liệu thử lên bản nháp thật. Tuyệt đối không gọi API Haravan. Toàn bộ 76 bài kiểm thử tự động PASS (Ran 76 tests in 10.540s -> OK). | **PASS** | `test_bis_api.py`, `test_quality_workflow.py`, `test_gemini_fallback.py`, `test_streamlit_react_host.py` |

---

## 3. Danh sách bằng chứng tệp tin
1. `scratch/agy006_mkt_copy_seo.png` (và bản gốc tại `agy006_mkt_copy_seo.png`): Ảnh chụp Marketing SKU 03026A hiển thị mô tả 323 ký tự, 2 đặc điểm không lặp ý, 3 trường SEO (title 58/70, desc 0/320, slug) và nhãn SERP minh họa.
2. `scratch/agy006_images_sku_search.png` (và bản gốc tại `agy006_images_sku_search.png`): Ảnh chụp Images tab với bộ chọn SKU 03026A, kết quả tìm ảnh từ Trang 7 của `catalogue_sample.pdf`, tên tiếng Anh dưới ảnh, nhãn chưa xác nhận và các nút thao tác.
3. `scratch/agy006_cloud_verification.json`: Dữ liệu DOM, trường form, danh sách SKU và ứng viên trích xuất từ Chrome CDP trên Cloud.

---

## 4. Giới hạn & Lưu ý
- Bản xem trước SERP chỉ mang tính chất minh họa định dạng biên tập (Google tự quyết định cách hiển thị thực tế trên kết quả tìm kiếm).
- Ảnh ứng viên trích xuất từ PDF cùng trang chỉ mang tính gợi ý phôi ảnh, bắt buộc phải có con người đối chiếu (`Tôi đã đối chiếu ảnh này với sản phẩm`) trước khi đưa vào studio xử lý ảnh.
- Không có bất kỳ thao tác nào làm ảnh hưởng đến dữ liệu sản phẩm thật hoặc Haravan.

---

## 5. Kết luận
Task **AGY_006** đạt trạng thái **VERIFIED**.
Toàn bộ các tiêu chí về Marketing Copy rút gọn, 3 trường SEO độc lập có giới hạn, và tính năng tìm ảnh theo phạm vi SKU trong tab Images đã hoạt động chính xác và an toàn trên Streamlit Cloud sau commit `44bd912`.


## 6. Codex documentation review — 2026-11-05
- Accepted owner-confirmed Antigravity acceptance report for 44bd912. VERIFIED retained for reported functional scenarios; Cloud observations are attributed to Antigravity, not a new Codex browser run.
- Reviewed diffs of the three documentation files only. Redacted login credential and checked source protocol against git show 44bd912 (v2-13); the original report's v2-12 label was inconsistent.
- A 0/320 meta description verifies field/counter presence, not completion of SEO content. Same-page image discovery is not product identity approval. Server limits/private URL rejection and persisted source status are supported by tests where cited, not all separately demonstrated as Cloud mutations.
- Antigravity reports 76/76 PASS; prior Codex evidence includes 75-test suite and final 29 API/native tests. No new test run needed for documentation-only changes.
- No raw DOM/screenshots, credentials, memory events or private histories committed. No Haravan API calls, publishing or mutations.
