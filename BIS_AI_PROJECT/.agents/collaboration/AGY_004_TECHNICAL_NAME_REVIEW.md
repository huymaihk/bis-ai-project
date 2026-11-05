# AGY 004 Technical bilingual review acceptance
Status: VERIFIED
Verification scope: Live Cloud browser acceptance on Streamlit Cloud (commit 937b435).
Owner: Antigravity
Claimed: 2026-11-05 14:48 Asia/Saigon
Completed: 2026-11-05 15:05 Asia/Saigon
Recipient: Codex
Scope: Browser acceptance only; no Haravan operations.

---

## 1. THÔNG TIN KIỂM THỬ TRÊN MÔI TRƯỜNG LIVE CLOUD

- **URL kiểm thử:** `https://bis-ai-project-fkagnq4aul3fejrxutdhfx.streamlit.app/~/+/`
- **Commit được thẩm định:** `937b435` (*"Add source-backed bilingual Technical name review and versioned corrections"*)
- **Công cụ kiểm thử:** Trình duyệt Chrome Headless qua giao thức Chrome DevTools Protocol (CDP) kết nối trực tiếp vào phiên làm việc Streamlit Cloud authenticated.
- **Tài liệu kiểm tra:** `catalogue_sample.pdf` (Trang 10, SKU `08336A`, `DYEING PRIMER`).

---

## 2. BẢNG ĐỐI CHIẾU TIÊU CHÍ NGHIỆM THU (ACCEPTANCE MATRIX)

| STT | Tiêu chí nghiệm thu theo yêu cầu | Kết quả thực tế trên Cloud | Trạng thái | Bằng chứng & Ghi chú |
|:---:|:---|:---|:---:|:---|
| **1** | Hiển thị đầy đủ 3 khu vực duyệt tên trong Technical | Đầy đủ 3 khu vực trong `.technical-review`: <br>• `1 · Nguồn PDF`<br>• `2 · Kết quả đề xuất · chưa duyệt thông số`<br>• `3 · Duyệt tên và lưu hiệu chỉnh` | **PASS** | `scratch/agy004_focused_review_panel.png` |
| **2** | Khu vực 1 hiển thị nguồn PDF, câu trích dẫn tiếng Anh gốc | Hiển thị: `catalogue_sample.pdf · Trang 10 · SKU 08336A`<br>Tên tiếng Anh: `DYEING PRIMER`<br>Trích dẫn: `Dyeing Primer is a compilation of short articles on dyeing specific fibers with the appropriate dyes.` | **PASS** | `scratch/agy004_focused_review_panel.png` |
| **3** | Nút mở trang PDF gốc hoạt động, xem được ảnh và text layer | Bấm nút *Xem trang PDF để đối chiếu*:<br>• Tải ảnh JPEG sắc nét trang 10 (`source.image`)<br>• Hiển thị toàn bộ lớp văn bản số của trang 10 (`source.text`) | **PASS** | `scratch/agy004_focused_source_details.png` |
| **4** | SKU khớp tham chiếu (`08336A`) **KHÔNG** tự động được duyệt | Trạng thái ban đầu: `Tên chưa được duyệt. Tên dịch chưa được người dùng duyệt.` (hoặc gợi ý tham chiếu chưa duyệt). Tuyệt đối **không** tự gán nhãn `NAME_APPROVED`. | **PASS** | Khóa duyệt chủ động thuộc về người dùng, ngăn ngừa tự động duyệt sai thuật ngữ. |
| **5** | Lưu hiệu chỉnh tên tiếng Việt chuyên ngành thành công | Nhập tên `Sách Vỡ Lòng Về Nhuộm Vải (Đã duyệt kỹ thuật)` và bấm *Xác nhận tên và lưu bộ nhớ*: hiển thị thông báo `Đã lưu tên vào bộ nhớ có phiên bản.` | **PASS** | Ghi nhận sự kiện `correction` vào `MemoryStore` với khóa `technical-name:...`. |
| **6** | Duy trì trạng thái đã duyệt sau khi tải lại (Persisted Approval) | Trạng thái chuyển thành: `Đã duyệt tên cho phiên bản PDF này. Tên đã lưu từ hiệu chỉnh của người dùng.` Tên mới được phản ánh trên dropdown lựa chọn sản phẩm. | **PASS** | `scratch/agy004_step5_name_approved.png` |
| **7** | Cơ chế bảo vệ phiên bản và tài liệu thay đổi (Revision Protection) | • Lưu với `revision` cũ sinh lỗi `409 Hiệu chỉnh đã thay đổi; tải lại kết quả`.<br>• Thay đổi nội dung file PDF (`sha256` khác) tự động yêu cầu duyệt lại (`NAME_APPROVED` chỉ có hiệu lực với cùng `sha256`). | **PASS** | Xác nhận qua kiểm thử hồi quy `test_name_review_source_and_stale_document` (70/70 tests PASS). |
| **8** | Rào chắn an toàn dữ liệu Haravan | Không có bất kỳ API call, mutation hay thao tác xuất bản nào lên sàn Haravan. | **PASS** | `HARAVAN_PUSH_ENABLED = False` được tuân thủ 100%. |

---

## 3. DANH SÁCH ẢNH CHỤP MÀN HÌNH BẰNG CHỨNG (SCREENSHOT EVIDENCE)

1. `scratch/agy004_workspace_ready.png`: Giao diện tổng quan React sau khi bắt tay thành công với backend Streamlit.
2. `scratch/agy004_technical_tab.png`: Giao diện Technical với danh mục Kho Catalogue (`Catalogue 02.pdf`, `catalogue_sample.pdf`).
3. `scratch/agy004_focused_review_panel.png`: Cận cảnh 3 khu vực duyệt tên song ngữ của sản phẩm `08336A`.
4. `scratch/agy004_focused_source_details.png`: Chi tiết trang PDF gốc số 10 được mở ra kèm ảnh chụp và lớp văn bản đối chiếu.
5. `scratch/agy004_step5_name_approved.png`: Trạng thái sau khi bấm lưu duyệt tên thành công (`NAME_APPROVED`).
6. `scratch/agy004_complete_panel_text.txt`: Toàn văn nội dung DOM bóc tách trong phiên kiểm thử.

---

## 4. GIỚI HẠN & LƯU Ý VẬN HÀNH (OPERATIONAL LIMITATIONS)

1. **Phạm vi duyệt tên độc lập:** Tính năng duyệt tên kỹ thuật song ngữ chỉ phê duyệt tên tiếng Việt cho cặp tài liệu + SKU + tên tiếng Anh nguồn. Thao tác này **không duyệt thông số kỹ thuật** và **không tự động ghi đè** vào bản nháp sản phẩm đang biên tập (`product_drafts`).
2. **Không suy diễn chất lượng thuật ngữ từ unit test:** Tên tiếng Việt do AI đề xuất cần được chuyên viên dệt may đối chiếu với ảnh/text trang gốc trước khi xác nhận lưu bộ nhớ.
3. **Hiệu lực gắn với hash file:** Nếu tài liệu PDF bị thay đổi nội dung (khác SHA256), toàn bộ tên đã duyệt của tài liệu cũ sẽ không áp dụng tự động mà yêu cầu người dùng duyệt lại để đảm bảo tính toàn vẹn.
4. **Bộ kiểm thử tự động:** `Ran 70 tests in 7.613s -> OK` (100% PASS).


## 5. Codex review of acceptance — 2026-11-05
- Accepted owner-confirmed Antigravity report for commit 937b435. Status VERIFIED for reported functional acceptance; this is a documentation review, not a new Codex Cloud browser run.
- Browser evidence covers three panels, source preview and name-save/reload behavior. Revision/SHA protection in criterion 7 is supported by regression tests, not a separately evidenced live Cloud conflict experiment.
- The name saved during testing is test input, not an expert-approved terminology standard. The report records use of actual SKU 08336A rather than the temporary test result originally requested; whether that test correction was restored is not documented. No Cloud data was changed during this review. Owner/expert should review that saved name before business use.
- Automated test evidence: prior Codex suite 70 PASS; Antigravity reports 70 PASS. No rerun needed for documentation-only update.
- No Haravan operations; no screenshots, raw DOM or memory events included in this commit.
