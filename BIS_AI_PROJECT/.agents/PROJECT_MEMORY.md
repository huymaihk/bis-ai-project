# 🧠 BIS TEXTILE AI - BỘ NHỚ TRI THỨC VÀ KIẾN TRÚC DỰ ÁN DÀI HẠN (PROJECT MEMORY)

> **LƯU Ý QUAN TRỌNG CHO TẤT CẢ AGENT:**
> File này là nguồn tri thức cốt lõi (Single Source of Truth) về kiến trúc, luồng dữ liệu, quy chuẩn nghiệp vụ và danh sách lỗi đã khắc phục của dự án **BIS Textile Multi-Agent System**.

---

## 📌 QUY TẮC BẮT BUỘC MỖI PHIÊN LÀM VIỆC (MANDATORY AGENT PROTOCOL)

1. **Khi bắt đầu phiên làm việc mới hoặc mở tác vụ mới:**
   * Agent **BẮT BUỘC chủ động đọc file `.agents/PROJECT_MEMORY.md` này đầu tiên** để nạp lại 100% ngữ cảnh toàn dự án, ghi nhớ các quyết định kỹ thuật đã chốt và tránh lặp lại các lỗi cũ trong "Sổ đen".
2. **Khi hoàn thành bất kỳ tính năng hoặc sửa lỗi kỹ thuật nào:**
   * Agent **TỰ ĐỘNG cập nhật 2-3 gạch đầu dòng bài học kinh nghiệm** vào Mục 5 ("Nhật ký tiến hóa & Bài học kinh nghiệm") ở cuối file này trước khi kết thúc lượt phản hồi.
3. **Môi trường thực thi lệnh terminal (Windows PowerShell):**
   * Do đường dẫn Python nằm trong AppData (`C:\Users\Dell\AppData\Local\Programs\Python\Python315\python.exe`), các lệnh chạy Python qua terminal sandbox phải sử dụng `BypassSandbox: true` để tránh lỗi phân quyền Windows.
   * Mọi thay đổi code hoặc dữ liệu cache tại `g:\My Drive\BIS_AI_PROJECT` phải được đồng bộ sang git local repo `C:\Users\Dell\bis-ai-project\BIS_AI_PROJECT`, commit và push lên GitHub (`origin main`) để Streamlit Cloud tự động cập nhật.

---

## 🏗️ 1. SƠ ĐỒ KIẾN TRÚC MULTI-AGENT HỆ THỐNG BIS TEXTILE

Hệ thống được thiết kế theo mô hình **Autonomous Multi-Agent Command Center** gồm 6 phòng ban chuyên biệt và 1 Trung tâm điều hành UI:

```
                                  [ CATALOGUE PDF (36 TRANG) ]
                                                │
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    COMMAND CENTER UI                                    │
│                     (app_ui.py - Streamlit HUD Cyberpunk / Canvas)                      │
└───────┬───────────────────────┬─────────────────────────┬────────────────────────┬──────┘
        │                       │                         │                        │
        ▼                       ▼                         ▼                        ▼
┌─────────────────┐   ┌──────────────────┐      ┌──────────────────┐     ┌──────────────────┐
│ AGENT_TECHNICAL │   │   AGENT_MEDIA    │      │ AGENT_MARKETING  │     │ AGENT_OPERATIONS │
│(agent_technical)│   │  (agent_media)   │      │(agent_marketing) │     │(agent_operations)│
├─────────────────┤   ├──────────────────┤      ├──────────────────┤     ├──────────────────┤
│• Bóc tách PDF   │   │• Studio bóc ảnh  │      │• Nghiên cứu SEO  │     │• Haravan Guard   │
│• 7 Khối HTML    │   │• Mockup 3D chân  │      │• Meta Title/Slug │     │  (Mốc 20/10/2026)│
│• Tiêu chuẩn     │   │  thực nền trắng  │      │• Meta Description│     │• Deep Content    │
│  AATCC/ISO/ASTM │   │• Không cắt logo  │      │  song ngữ chuẩn  │     │  De-duplication  │
│• Từ điển Dệt may│   │• Quản lý Gallery │      │• ai_product_     │     │• Google Sheets   │
│  TEXTILE_GLOSS  │   │  ảnh sản phẩm    │      │  refiner engine  │     │  Master (23 cột) │
└────────┬────────┘   └─────────┬────────┘      └─────────┬────────┘     └─────────┬────────┘
         │                      │                         │                        │
         └──────────────────────┼─────────────────────────┴────────────────────────┘
                                │
                                ▼
        ┌─────────────────────────────────────────────────┐
        │            LEARNING ENGINE & MEMORY             │
        │(learning_engine.py + feedback_memory.json)      │
        ├─────────────────────────────────────────────────┤
        │• Lưu vết mọi feedback sửa đổi từ người dùng     │
        │• Tự học Few-shot injection cho các lần trích sau │
        └─────────────────────────────────────────────────┘
                                │
                                ▼
        ┌─────────────────────────────────────────────────┐
        │            AGENT_KNOWLEDGE ARCHIVE              │
        │(agent_knowledge.py + keep_form_translator.py)   │
        ├─────────────────────────────────────────────────┤
        │• Lưu trữ Sách tiêu chuẩn, Manual, CO/CQ, COC    │
        │• Dịch thuật kỹ thuật dệt may giữ nguyên 100%    │
        │  form mẫu (pdf2zh / Keep-form translator)       │
        └─────────────────────────────────────────────────┘
```

---

## 🔄 2. LUỒNG DỮ LIỆU GIỮA CÁC MODULE (END-TO-END DATA PIPELINE)

```
[1. Bóc tách PDF] 
     └──> Catalogue PDF (36 trang) ──> agent_technical.py ──> Trích xuất 97 SKUs chuẩn xác.
[2. Sinh định dạng]
     └──> 7 Khối HTML nền trắng sắc nét (`custom_html`) + Thông số kỹ thuật 2 cột (39%-61%).
[3. Xử lý hình ảnh]
     └──> agent_media.py ──> Bóc ảnh thiết bị gốc/sách AATCC, tạo Mockup 3D nền trắng sạch (`#FFFFFF`).
[4. Tối ưu SEO Song ngữ]
     └──> ai_product_refiner.py ──> Chuẩn hóa Tiêu đề song ngữ + Meta Description Google theo công thức cố định.
[5. Rà soát trùng lặp chuyên sâu (Deep Content De-duplication)]
     └──> agent_operations.py ──> Quét Live 205 sản phẩm Haravan API + bistextile.com:
          ├── Khóa 28 sản phẩm trùng (Trùng Variant, Handle, Tiêu đề, Tags hoặc body_html).
          └── Mở khóa 69 sản phẩm mới 100% sẵn sàng xuất bản.
[6. Duyệt & Tự học (WYSIWYG & Learning Engine)]
     └──> Người dùng kiểm tra, chỉnh sửa trên UI ──> learning_engine.py ghi nhớ vĩnh viễn vào `feedback_memory.json`.
[7. Xuất bản an toàn]
     └──> agent_operations.py ──> Đẩy sản phẩm ẩn (published: false) lên Haravan API + Đồng bộ Sheet Master (23 cột).
```

---

## ⚖️ 3. CÁC QUYẾT ĐỊNH KỸ THUẬT QUAN TRỌNG ĐÃ CHỐT (ARCHITECTURAL DECISIONS)

### 3.1. Master Data 97 SKUs
* File `catalog_master_data.py` là bộ dữ liệu gốc chuẩn mực 100% đã được đối chiếu từng trang PDF của `catalogue_sample.pdf` (36 trang).
* Mọi SKU phải giữ nguyên mã nguyên bản của AATCC (ví dụ: `03026A`, `03026B`, `09616A`, `48349F`, `28347A`, v.v.).

### 3.2. Chuẩn 7 Khối HTML Bài Viết Haravan (Nền trắng sắc nét)
1. **Khối 1:** Tên sản phẩm tiếng Việt (Font bold 20px, màu `#0f172a`).
   * **Cấu trúc bắt buộc:** `Tên tiếng Việt + Mã SKU + Hãng sản xuất` (Ví dụ: `Bộ thử sắc giác chuyên sâu Farnsworth Munsell 100-Hue Test 88900A AATCC`).
2. **Khối 2:** Tên sản phẩm tiếng Anh (Font bold 15px, màu xanh `#0284c7`, UPPERCASE giữ nguyên từ Catalogue gốc).
3. **Khối 3:** Hãng sản xuất / Tổ chức ban hành (`AATCC (Hoa Kỳ)`).
   * **ĐẶC BIỆT LƯU Ý:** **TUYỆT ĐỐI KHÔNG ĐƯỢC CHỨA CỤM TỪ `• Đơn vị phân phối: BIS Textile Việt Nam`**. Toàn bộ hệ sinh thái đã thống nhất gỡ bỏ hoàn toàn cụm từ này khỏi Khối 3.
4. **Khối 4:** Giới thiệu sản phẩm (Mô tả kỹ thuật chuyên sâu, súc tích). Tiếp nhận thông số gộp từ Khối 6 nếu sản phẩm có quá ít dữ liệu bảng.
5. **Khối 5:** Đặc điểm nổi bật (Dạng danh sách `<ul><li>` rõ ràng, có emoji ✨).
6. **Khối 6:** Bảng thông số kỹ thuật chính 2 cột (Cột 1 rộng 39% nền xám nhạt `#f8fafc`, Cột 2 rộng 61% nền trắng `#ffffff`).
   * **Quy tắc linh hoạt:** NẾU SẢN PHẨM CÓ QUÁ ÍT THÔNG TIN (dưới 2 tiêu chí), cho phép KHÔNG CẦN LẬP BẢNG mà gộp trực tiếp nội dung vào Khối 4 để giao diện bài viết gọn gàng, súc tích.
7. **Khối 7:** Liên kết / Tài liệu tiêu chuẩn phương pháp thử liên quan (AATCC TM, EP, v.v.).

### 3.3. Công thức chuẩn SEO Google Meta Description
Bắt buộc áp dụng đúng 100% công thức sau cho toàn bộ sản phẩm:
$$\text{[Tên tiếng Việt]} - \text{[Tên tiếng Anh]} \text{ ([SKU]) chính hãng } \text{[Brand]}. \text{ Tiêu chuẩn kiểm nghiệm dệt may quốc tế, đầy đủ chứng từ CO/CQ tại BIS Textile.}$$
* Giới hạn độ dài chuẩn SERP: **140 - 160 ký tự**.
* Snippet preview trên UI phải hiển thị nền tương phản cao, dễ nhìn, font chữ rõ nét.

### 3.4. Haravan Guard & Cơ chế Đối soát trùng Deep Content De-duplication (6 tầng)
* **Haravan Guard:** Tuyệt đối KHÔNG ghi đè, sửa đổi hoặc xóa các sản phẩm tạo trước mốc an toàn **20/10/2026** trên Haravan.
* **Quy tắc đối soát trùng 6 tầng:**
  * **Tier 1:** Trùng mã SKU chính xác trong danh sách Variant SKU trên sàn.
  * **Tier 2:** Trùng mã SKU trong tên Variant (Option/Title của Variant).
  * **Tier 3:** Trùng mã SKU độc lập trong URL handle, tiêu đề hoặc tags (`\b{SKU}\b`).
  * **Tier 4 (ĐỌC FULL NỘI DUNG):** Mã SKU xuất hiện trong toàn bộ nội dung chi tiết bài viết (`body_html` hoặc `body_plain`).
  * **Tier 5:** Mã số cốt lõi (Core Number $\ge 5$ chữ số, ví dụ `03026` từ `03026A/B`) xuất hiện trong URL, tiêu đề hoặc nội dung bài viết đi kèm ngữ cảnh hãng.
  * **Tier 6:** Trùng khớp cụm thuật ngữ tiếng Anh độc bản đặc trưng của sản phẩm (ví dụ: `gray scale color change` -> `28359C`, `gray scale staining` -> `28360C`, `light transmission verification fabric` -> `38618A`, `spray tester funnel` -> `78911A`, `spray tester nozzle` -> `78386A`).
* **Hiện trạng đối soát chuẩn:** **28 sản phẩm trùng** (được khóa an toàn) và **69 sản phẩm mới 100%**.

### 3.5. Quy chuẩn Ảnh Thành phẩm Đạt chuẩn (Benchmark 6_Final_Composites)
Mọi ảnh sản phẩm xử lý cho hệ sinh thái BIS Textile bắt buộc phải đối chiếu theo bộ ảnh mẫu đạt chuẩn tại thư mục `Google_Drive_Storage/6_Final_Composites/` (như các file: `AATCC Weight Trio on BIS Backdrop.png`, `Branded 2.0 KG Weight Discs Display.png`, `BIS_Metal_Rack_FIXED.png`, `09616A.png`):
1. **Định dạng & Kích thước:** $1254 \times 1254$ pixel (tỷ lệ 1:1 vuông), độ phân giải cao 24-bit RGB.
2. **Phông nền thương hiệu (Brand Backdrop):** Nền hoa văn lặp logo `Bis TEXTILE GARMENT` chuẩn, phủ đều khung hình, có gradient ánh sáng phòng studio (sáng trung tâm và phía trên, đầm dần xuống dưới).
3. **Bảo toàn vật thể gốc 100%:** Giữ nguyên vẹn 100% hình khối thật của thiết bị, thớ kim loại, ốc vít, các dòng chữ dập chìm quy chuẩn (ví dụ `2.0 KG`, logo lục giác `AATCC ®`), tuyệt đối không để AI vẽ lại làm sai lệch chi tiết kỹ thuật.
4. **Bóng đổ 3D tiếp xúc chân thực:** Đổ bóng tiếp xúc (Contact Shadow / Ambient Occlusion) tự nhiên dưới đáy sản phẩm lên mặt nền thương hiệu, tạo cảm giác sản phẩm được đặt chụp thực tế trên mặt bàn studio có trải phông nền BIS Textile.
5. **Bố cục:** Vật thể đặt ở trung tâm, chiếm 55% – 70% diện tích khung hình, có khoảng thở (padding) an toàn 4 phía.

---

## 🚫 4. "SỔ ĐEN" CÁC LỖI KỸ THUẬT ĐÃ GIẢI QUYẾT (BLACKBOOK - CẤM TÁI PHẠM)

| Mã lỗi | Mô tả lỗi trước đây | Nguyên nhân gốc rễ | Giải pháp chuẩn mực (Bắt buộc tuân thủ) |
|:---:|:---|:---|:---|
| **ERR-01** | Bắt nhầm trùng sản phẩm (Falsely flagged duplicates) | Dùng Jaccard word overlap trên các từ chung như `det`, `nhuom`, `detergent`, `scale` khiến các mã bột giặt khác nhau bị gom chung vào 1 sản phẩm. | Chuyển sang **Deep Content De-duplication 6 tầng**. Chỉ bắt trùng khi có SKU, mã số cốt lõi hoặc cụm thuật ngữ độc bản trong `body_html` / metadata. |
| **ERR-02** | Sản phẩm không được mở khóa khi hết trùng | Code cũ kiểm tra `if p.get("status") == STATUS_REJECTED and "Haravan" in p.get("notes", ""):`. Các ghi chú không chứa chữ "Haravan" (chỉ có bistextile.com) bị kẹt vĩnh viễn ở trạng thái `REJECTED`. | Bỏ điều kiện lọc text ghi chú. Khi `is_dup == False`, tự động reset vô điều kiện sang `STATUS_EXTRACTED` và xóa sạch thông tin đối soát cũ. |
| **ERR-03** | `NameError: name 're' is not defined` trên Streamlit Cloud | `import re` bị đặt cục bộ bên trong hàm thay vì đặt ở đầu file `app_ui.py`. | Tất cả thư viện chuẩn (`re`, `json`, `time`, `os`, `sys`, `pathlib`) phải được import ngay tại đầu file `app_ui.py`. |
| **ERR-04** | Cụm từ "Đơn vị phân phối" tái xuất hiện | Regex chỉ xóa một phần chuỗi HTML hoặc các hàm render tạo lại chuỗi này. | Xóa triệt để bằng regex 3 lớp tại `app_ui.py`, `agent_technical.py`, `ai_product_refiner.py` và làm sạch dữ liệu trong cache json. |
| **ERR-05** | Render ký tự entity `&bull;` dạng chữ thô | Viết thẳng `&bull;` vào chuỗi markdown mà không bật cờ HTML. | Luôn sử dụng ký tự Unicode trực tiếp: `•` thay vì entity HTML `&bull;`. |
| **ERR-06** | Mất nội dung chi tiết bài viết sau khi quét live | Code cũ khi tổng hợp `unified_store` đã bỏ qua trường `body_html` và `body_plain`. | Lưu giữ đầy đủ `body_html`, `body_plain`, `variants`, `tags` vào `bistextile_existing_products.json`. |
| **ERR-07** | `re.PatternError: bad character range —-_` | Ký tự gạch ngang `-` đặt ở giữa trong character class `[...—-_]` bị Python regex hiểu lầm là dải ký tự từ `—` đến `_`. | Luôn đặt dấu gạch ngang `-` ở vị trí cuối cùng trong character class: `[...—_-]`. |
| **ERR-08** | WYSIWYG reset lại nội dung khi bấm Lưu | Form submit của Streamlit bị render lại state mặc định do key trùng lặp. | Gán dynamic key theo SKU: `f"inp_vi_{sku}"`, `f"inp_desc_{sku}"` và cập nhật trực tiếp vào session state `cached_products`. |

---

## 📝 5. NHẬT KÝ TIẾN HÓA & BÀI HỌC KINH NGHIỆM (LESSON LEARNED LOG)

* **2026-11-02 (Phiên sáng):**
  * *Bài học 1 (Deep Content Scanning):* Đối soát sản phẩm thương mại điện tử B2B bắt buộc phải đọc sâu vào `body_html` và bảng thông số của bài viết sàn, vì 1 bài viết lớn (ví dụ máy thử thấm nước hay bột giặt 1993) thường gộp nhiều mã SKU và phụ tùng bên trong. Đã phát hiện chính xác 28 mã trùng và bảo vệ an toàn 69 mã mới.
  * *Bài học 2 (Regex Robustness):* Khi viết regex character class chứa nhiều ký tự phân tách đặc biệt (`—`, `–`, `_`, `-`), dấu `-` phải luôn được đặt ở cuối cùng để tránh lỗi `bad character range`.
  * *Bài học 3 (Single Source of Truth):* Dữ liệu bóc tách phải luôn đồng bộ song song giữa Google Drive Workspace và Git Repo (`C:\Users\Dell\bis-ai-project\BIS_AI_PROJECT`) để đảm bảo Streamlit Cloud và local runtime đồng nhất 100%.
  * *Bài học 4 (Quy chuẩn Tiêu đề & Linh hoạt Bảng thông số):* Cấu trúc Khối 1 bắt buộc có cả Tên TV + Mã SKU + Hãng (AATCC); Khối 6 linh hoạt không bắt buộc vẽ bảng nếu thông số quá ngắn để tránh giao diện bị vụn, cho phép gộp trực tiếp vào phần giới thiệu Khối 4.
  * *Bài học 5 (Dọn dẹp tệp tin rác):* Định kỳ dọn sạch các script test một lần (`test_*.py`, `.docx` cũ, file debug tạm) để giữ kho lưu trữ nhẹ, tinh gọn và chuyên nghiệp.
* **2026-11-03 (Phiên chiều - Triển khai Chuẩn Ảnh Benchmark 1254x1254):**
  * *Bài học 6 (Zero-Hallucination Optical Sharpening):* Tuyệt đối không dùng AI tạo sinh (diffusion) để vẽ lại ảnh thiết bị kỹ thuật/máy móc vì sẽ làm sai font chữ, méo rãnh hoặc hallucinate logo. Áp dụng kỹ thuật quang học: LAB CLAHE trên kênh Luminance (L) + Bilateral Filter + High-Pass Detail Enhancement trực tiếp trên vật thể chụp thật để làm sắc nét chữ dập chìm `2.0 KG` và logo `AATCC ®` với độ chính xác cơ học 100%.
  * *Bài học 7 (Golden Benchmark Compositing 1254x1254):* Chuẩn hóa toàn bộ hệ thống (`flow_2d_studio.py`, `agent_media.py`, `app_ui.py`) theo độ phân giải chuẩn $1254 \times 1254\text{ px}$, phôi nền `BIS_BACKDROP_1254.png`, tỷ lệ vật thể 55%–65% khung hình, đường chân đế $y=980$, và bóng đổ vật lý 3 lớp (Ambient Occlusion + Soft Shadow + Subtle floor reflection).
  * *Bài học 8 (Quản trị vận hành Streamlit Cloud):* Streamlit Cloud tự động ngủ khi không có lượt truy cập (Sleep mode); hướng dẫn người dùng nhấn "Yes, get this app back up!" để khởi động lại sau 30s hoặc làm việc trực tiếp trên Local runtime (`http://localhost:8501`).


* **2026-11-03 (Nâng cấp bộ nhớ bền vững):**
  * Lịch sử chat BIS giờ lưu tại Google_Drive_Storage/8_AI_Memory/events, không chỉ st.session_state. Sửa/thu hồi có phiên bản; xung đột cần giải quyết. Đọc MEMORY_GUIDE.md và CURRENT_MEMORY.md khi tiếp tục dự án.
  * Chat nhân viên dùng Gemini với ngữ cảnh thật; không còn trả tool giả hay tiến độ ngẫu nhiên. Khung chat tư vấn, chưa tự thực thi Haravan/dịch file/tạo ảnh. Những tuyên bố cũ “15 nhân viên tự vận hành” không phải bằng chứng công việc đã hoàn thành.
  * Sau thay đổi code/tri thức: cập nhật bàn giao, chạy python sync_memory.py --local-only --record-update "nội dung đã kiểm tra". Chủ dự án đã duyệt bảng BIS_Textile_Product_Master. memory_sync_config.json bật đồng bộ vào tab BIS_AI_MEMORY_V1, nhưng khóa service account local hiện lỗi invalid_grant / Invalid JWT Signature. Không đưa kho sự kiện/backup lên Git.


## 2026-11-04 — Đánh giá lại theo nghiệm thu người dùng
- Các phòng ban chưa đạt; kết quả test bộ nhớ không chứng minh nghiệp vụ đạt.
- Kiểm tra sơ bộ thấy chọn ảnh theo dung lượng/ảnh web đầu tiên và chống trùng token có nguy cơ sai.
- Nghiên cứu GitHub và tiêu chí nâng cấp ở UPGRADE_REVIEW_2026_11_04.md; chưa sửa/deploy nghiệp vụ trong lượt nghiên cứu này.

- 2026-11-04: Triển khai pdf_candidates.py và nối Media UI: tìm trang theo SKU đầy đủ, liệt kê ảnh gốc có bbox/hash, tải từng ảnh/ZIP, người dùng chọn nguồn. Test catalogue 03026A: 2 ảnh ứng viên trên trang 7; 03026AX không khớp. Chưa nghiệm thu UI/live, scan OCR/crop và tìm web chưa triển khai.


## 2026-11-04 — Quality Release 2
- Chủ dự án cho toàn quyền cải tiến, trừ xóa sản phẩm Haravan. Đã xây UI 5 bước, template có chứng cứ, chọn ảnh PDF/web, studio nguồn + Gemini tham chiếu, tri thức theo trang và cổng tạo nháp có checkpoint/hash/đối soát. Xem QUALITY_RELEASE_2.md.
- Test nghiệp vụ dùng fake API, không suy ra nghiệm thu ảnh AI thật. Không có thao tác xóa sản phẩm. Google credential local còn lỗi; checkpoint không đồng bộ sẽ chặn đăng.
- Không tự đổi bộ test để nới tiêu chí: test tái lập phát hiện index bỏ sót trang chữ ngắn; đã sửa để giữ trang có >=10 ký tự và retire chunk cũ sau cập nhật.

## 2026-11-04 — Workspace visual refresh
- Tham khảo hai video của chủ dự án và GitHub Langflow/Open WebUI/Agent Chat UI; thêm nền tối/sáng, hero agent CSS, số liệu thật, chọn SKU bên trái và thẻ ngữ cảnh. Xem UI_DESIGN_RELEASE.md.
- 53 kiểm thử offline đạt, gồm chuyển theme vẫn giữ SKU và chặn đăng khi chưa duyệt. Chưa nghiệm thu hình ảnh trình duyệt/cloud; preview localhost trước đó bị từ chối nên không tìm cách vượt quyền.
- Bài học: giao diện agent chỉ mô tả vai trò; không trình bày agent chạy nền hoặc kết nối khỏe khi chưa có bằng chứng. Không thay PIN hay thao tác Haravan. Đồng bộ Google vẫn chưa xác minh hoạt động.

## 2026-11-04 — React bridge bước 1–2
- Thêm frontend/ từ bản AI Studio (giữ nguyên thư mục gốc), bis_api.py và giao diện kết nối thật: 97 sản phẩm, 476 PDF/ảnh qua HTTP, sửa sản phẩm có revision + memory event, ghi chú sửa/thu hồi/phiên bản. Chi tiết REACT_BRIDGE_RELEASE.md.
- 61 test Python, TypeScript lint và Vite build đạt. Sửa 2 lỗi TS có sẵn; npm build trên C vì Google Drive gây lỗi ghi file. Browser visual chưa nghiệm thu.
- Bài học: địa chỉ API trong mock adapter không phải kết nối thật; không bật Haravan hay trạng thái agent từ mô phỏng. React đang chạy local; cloud/worker/agent/ảnh nghiệp vụ và Google sync còn cần triển khai.

## 2026-11-04 — AI Studio folder 1 update
- Imported 17 updated frontend files, preserved live workspace/auth/API and explicit demo boundary; production Vite build passed. Container deployment recipe added without secrets/private data. Public hosting not provisioned; requires container host with durable storage. No Haravan mutations.



## 2026-11-04 — React embedded in Streamlit
- Authenticated custom component with request queue, replay guard and PDF/image transport. Default live React after existing login; old UI selectable. 3D remains labelled demo.
- 64 Python tests passed; 11 bridge/API tests rechecked after thumbnails; TypeScript/build passed. Full authenticated AppTest: zero exceptions. Browser visual check unavailable.
- Ships compiled frontend/streamlit_dist; no extra API port. Google sync and ephemeral cloud storage unresolved; live agent/image workflow pending. No Haravan mutations.

## 2026-11-04 — Blank 3D viewport mitigation
- Default office view now uses the concept image; interactive WebGL remains selectable. Added error boundary with explicit fallback and replaced GPU fence polling with bounded timer scheduling; lowered GPU requirements. TypeScript/build passed. Exact browser failure not established; user screenshot was a cropped empty viewport, no console evidence.

## 2026-11-04 — Apply Studio office to live entry
- Rechecked AI/1: Studio source matches imported files except deliberate integration fixes. Found live entry bypassed Studio office through separate nested demo/login. Added LiveOffice directly to live Overview, real selected SKU and navigation, 6 department tiles and optional 3D/static views with 15-second startup watchdog. Scene remains labelled simulation; live task data separate.
- Removed lazy demo App from live route so prototype login/mock credentials and demo Operations no longer appear in the live navigation. Preserved real product/memory handlers and backend gates. Source export unchanged.
- TypeScript and Vite build passed. Browser visual validation unavailable; full agent orchestration is not implemented by this design integration.

## 2026-11-04 — Studio AI/2 applied to live workspace
- Compared AI/2 export with integrated frontend: actual design source/assets already match except intentional entry/WebGL/Streamlit fixes. Imported design-system reference, applied warm ivory inspection panels to live tabs and added 4-step workflow navigation; preserved real data/auth/memory and direct office overview. Original source folder unchanged.
- TypeScript and Vite build pass. No backend changes; no claims of live agent execution. Browser visual QA not available.

## 2026-11-04 — Workflow V2 integration
- Added authenticated React-to-native tool routing for all five business steps. Keeps SKU on round trip, renders only selected step and shares existing drafts/memory. Existing Haravan creation gates and code remain unchanged.
- Added local workflow review with source/content, SEO, approved-image hash, snapshot duplicate and revision checks. Reports persist separately from approved knowledge; no publish authorization or external API calls. React blocks navigation/check while edits are unsaved.
- Validation: existing 64 plus 5 new regression cases pass (68 in full run, one additional bridge round-trip test separately); TypeScript and Vite build pass. Public browser rendering not visually verified.
- Limits: native business tools are opened from the React interface, not rewritten in React. No autonomous/background worker or new AI orchestration; Google sync still unverified. No live Haravan mutations.
- Lesson: labels and 3D scenes do not prove operations. Reuse guarded business tools through an authenticated route, bind diagnostics to product revision, and identify snapshot checks separately from live checks.

## 2026-11-04 — Hot deployment compatibility fix
- User screenshot shows a TypeError at app_ui.py calling render_react_workspace with services; full cloud exception message is redacted. Reproduced old cached one-argument renderer incompatibility locally.
- Added protocol-aware module loader and session bridge reset for incompatible hot deployments. Reload API first, then renderer; preserve persistent product/memory stores. Haravan code/config unchanged.
- 16 API/bridge tests passed, including cached old-signature reproduction and stale session reset. Cloud visual result remains unverified.

## 2026-11-04 — Full width embedded workspace
- Removed React main width cap and Streamlit horizontal padding; iframe now follows root content height with ResizeObserver instead of fixed 1100px. Embedded intrinsic minimums avoid viewport-height feedback loops. Host protocol bumped for hot deployment refresh.
- TypeScript/build and 5 bridge tests pass. Browser layout not visually confirmed; this changes layout only, not Haravan business rules.

## 2026-11-04 — UI audit with browser access blocked
- Browser tool reports local browser use disabled in Work settings; no visual acceptance claimed.
- Fixed embedded load failures being silently replaced by a second PIN screen; show loading/error/retry using existing Streamlit auth. Scoped live form styles away from Studio 3D controls; added wrapping/min-width protection. Robot eye/material selectors now update state.
- Loader also reloads a stale native workspace signature before routing. 22 API/bridge/workspace tests pass; TypeScript and production build pass. Haravan unchanged.

## 2026-11-04 — Scroll reachability fix
- Disabled OrbitControls wheel zoom and enabled vertical touch pan so the office does not consume page scrolling. Frame sizing includes root overflow and image/DOM updates with bottom clearance. Embedded memory list no longer uses a nested height-limited scroll box.
- TypeScript and production build passed. Browser use remains disabled, so actual deployed scrolling awaits visual verification. Haravan unchanged.

## Catalogue scan and analysis selection
- Added explicit catalogue folder scan, persistent hash-bound completion state, green completed-file labels and confirmation checkbox before reanalysis in native PDF tool.
- Full-document extraction records page jobs, preserves existing drafts, fails closed on empty/unconfirmed page results. Six workspace regression tests pass; real AI extraction not validated.
- Cloud scans its own filesystem, not desktop G drive. Upload or separate file sync required. Haravan unchanged.

## Technical layout clarification
- Reorganized Technical entry around document intake and three visible steps; renamed product edit section to distinguish selected-SKU edits from catalogue analysis.
- Native PDF tool has numbered source/select/page sections, file count/legend/empty state. Upload refreshes scanned file list immediately.
- TypeScript/build pass. Visual browser verification unavailable. Haravan unchanged.

## Technical full document workspace
- Removed selected-product edit and comparison panels from React Technical. Selecting Technical now opens the complete existing document workspace directly, including the “Từ tài liệu gốc. Đến sản phẩm chuẩn.” overview, scan/upload, selection, analysis and page tools.
- TypeScript and production build pass. Browser rendering unverified; Haravan unchanged.

## Technical inline catalogue workspace repair
- Removed automatic native navigation which made Technical disappear. Added inline React document inventory, explicit scan, selection, per-file green completion and reanalysis confirmation.
- Authenticated API scans only catalogue PDFs and validates SHA256. Analysis runs page by page in-session with progress, version/run guards, preserves existing drafts and marks failures conservatively. Empty AI pages stop for review, not green completion.
- 13 API tests pass (fake extractor for lifecycle; no real AI call), TypeScript/build pass. Module protocol bumped. Cloud still cannot read desktop G without file synchronization; UI explicitly states limitation. Browser visual acceptance unavailable. Haravan unchanged.

## 2026-11-05 Catalogue empty-page diagnosis
- Distinguish valid parsed empty product arrays from blank/malformed/API failures in Technical extractor. Valid non-product pages continue; all-empty documents require review instead of green completion.
- API persists failed page and safe error category (quota, permissions, unavailable model, format). Reports page number rather than generic ValueError.
- 19 API/bridge tests, TypeScript/build pass. No real Gemini call or deployed browser confirmation; screenshot alone does not prove precise original API failure. Haravan unchanged.

## 2026-11-05 Technical ranges and per-file results
- Added full/range/single-page analysis with server bounds and sequential run validation. Partial runs are labelled PARTIAL, not full green.
- Persist per-file SKU extraction results separately from edited drafts; UI selects SKU, displays evidence and can confirm rerun on its source page filtered to that SKU. Compact panels.
- Authentication failures 401/403 stop retries and provide Streamlit Secrets/Gemini permission guidance. Screenshot confirms auth rejection; live credential remediation unresolved.
- 20 API/bridge tests including ranges/results/confirmation pass; TypeScript/build pass. Haravan unchanged; browser/real AI acceptance pending.

## 2026-11-05 Codex and Antigravity collaboration
- Added COLLABORATION_GUIDE.md, GEMINI.md entry and AGENTS.md pointer with ownership, file scope, isolated checkout guidance, review evidence and single deployment writer.
- Prepared local-only task .agents/collaboration/AGY_001_GEMINI_DIAGNOSIS.md for Gemini diagnosis/fallback research. Status OPEN, not claimed; no direct Antigravity communication channel available.
- Verified documents exist and task scope is read-only diagnosis; no IDE DB access, credentials, Haravan calls or application changes. Manual ownership markers are advisory, not concurrency locks.
- Lesson: shared memory and task files enable handoff, not autonomous delivery or proof that another tool has started.

## 2026-11-05 Strength-based collaboration plan
- Extended COLLABORATION_GUIDE with project-specific roles, five workstreams, independent review loop and priority Gemini → Technical → durable sync → media.
- Prepared AGY_002 local read-only browser audit handoff. Both Antigravity tasks remain OPEN/unassigned; no claim that another app is running.
- Verified files and scopes; no application code or credentials changed. Browser access restrictions remain in force.


## 2026-11-05 Codex verified AGY handoffs and Gemini fallback
- Verified AGY_001 evidence with real local gemini-3.5-flash reply OK (256 output tokens); not a reliability or PDF quality guarantee. AGY_002 verified within source/API review scope; report explicitly did not use browser testing.
- Added PRIORITY_MODELS=(gemini-3.8-flash, gemini-3.5-flash) and bounded 503/504 fallback for Technical extraction, model attempt metadata and result provenance. No fallback on auth/quota/other HTTP errors.
- Requested test_bis_api and test_quality_workflow plus new fallback tests: 59 PASS. Both tasks marked VERIFIED with limits. Haravan source/config safety flags untouched except model list added to config; no Haravan calls or mutations.
- Lesson: 200 without response text does not prove usable output; record test type and scope instead of “100% success”.

## 2026-11-05 Technical fallback hot deployment repair
- Screenshot still reports page 15 HTTP 503; cannot establish whether backup was attempted from old message alone.
- Refresh workspace loader on rerun, bump API/bridge protocol and reload config/fallback/Technical dependencies before replacing stale session bridge. Avoid retaining pre-fallback agent after hot deployment.
- Error text now lists model attempts and safe status codes, distinguishing primary failure from exhausted fallback. No credentials or raw provider body added.
- 66 API/quality/fallback/bridge tests PASS including dependency reload ordering and both-model exhaustion. Live Cloud page 15 remains unverified; no Haravan calls or changes.
- Lesson: source deployment alone does not prove cached session objects use updated dependencies; report model attempts rather than inferring fallback success.


## 2026-11-05 Codex AGY_003 cross-verification
- Integrated model priority and 45s client timeout; corrected fallback to use selected page text only, preserve source quotes and avoid inferred brand/unit/category/master descriptions. Fallback audits cannot pass and catalogue remains NEEDS_REVIEW.
- Added text to native full-document extraction and refreshed deployment protocol v2-7. Final requested suite plus regression: 68 PASS in deployment checkout.
- Independent live local page 15: gemini-3.6-flash parsed four expected SKUs in 18.49s. All-503 simulation on actual PDF returned same four source-backed SKU candidates requiring review.
- AGY_003 VERIFIED for code/local tests only. Browser Cloud acceptance blocked: local browser disabled in Work settings. No Haravan operations.
- Lesson: fallback must never read a different document or substitute master data as source evidence; test pipeline status as well as returned rows.

## 2026-11-05 Cached Technical signature repair
- Reviewed Antigravity Cloud TypeError report and two-file patch; strengthened with shared technical_runtime compatibility repair for cached leader and native full/single-page extraction.
- Reload old config/module when class itself lacks page_text; replace stale instance; reuse compatible objects. Bump workspace protocol v2-8 so native changes load on hot deploy.
- 69 requested-suite tests PASS including new stale-module/instance regression. No Haravan calls, credential changes, or cache-wide deletion.
- Lesson: checking an instance alone is insufficient if the imported class is also stale. Cloud success must still be demonstrated independently.


## 2026-11-05 AGY_003 closed after Cloud acceptance
- Owner confirmed Antigravity section 7 Cloud acceptance on commit 0bd2651: page 15 native extraction no TypeError, existing draft protected, four expected SKUs present. AGY_003 now CLOUD_VERIFIED / CLOSED.
- Codex reviewed report; Cloud observations remain attributed to Antigravity. Prior Codex regression: 69/69 PASS; no code change or test rerun required for documentation-only closure.
- Lesson: distinguish existing preserved drafts from freshly extracted rows; acceptance covers observed scenario, not universal model reliability. No Haravan operations.

## 2026-11-05 Technical source / translation / name review
- Added three-part React result review: PDF page image/text and English evidence, proposed Vietnamese name/description with actual extracted fields, explicit name approval with versioned MemoryStore corrections.
- Reference suggestions require exact normalized English name AND SKU; references are not automatically approved. Human names scoped by document/SKU/English title; new PDF version requires reapproval. Name-only approval does not approve technical facts or overwrite edited drafts.
- Hide stale source-version results; validate source SHA, name changes and memory revision on save. Correct NEEDS_REVIEW wording so local fallback products are not reported as empty.
- 70 regression tests PASS; after final name-source concurrency guard, API tests PASS. TypeScript and Streamlit production build PASS. Browser visual acceptance remains pending; no new live AI extraction or Haravan operations.
- Lesson: parsed JSON is not translation acceptance; show source and provenance next to proposals and keep human name approval separate from product approval.


## 2026-11-05 AGY_004 acceptance report reviewed
- Reviewed owner-confirmed Antigravity functional Cloud acceptance of commit 937b435: bilingual panels, source preview, explicit name approval and persistence. AGY_004 VERIFIED; prior 70-test result retained.
- Revision/SHA protection evidence comes from automated tests. Test-saved name on real SKU 08336A is not expert terminology approval; restoration not documented and no Cloud record changed by Codex during review.
- Lesson: use temporary data for approval tests and separate functional acceptance from linguistic quality. Documentation only; no Haravan operations.

## 2026-11-05 Technical terminology display correction
- Dropdown now uses source-matched terminology suggestions as display names, without auto-approving. Added explicit printed-title aliases for page10 books and concise Vietnamese names for shown book/replica SKUs.
- Known AGY004 test approval on 08336A is excluded from effective approval/display; history is preserved and other human corrections remain authoritative. English/SKU mismatch never receives the suggestion.
- 71 regression tests, TypeScript and production build PASS. Cloud visual result not independently checked. No Haravan operations.
- Lesson: storing reference suggestions is insufficient when selectors still display raw AI names; known test approvals require explicit handling, not deletion of history.

## 2026-11-05 Marketing inline editing
- Moved full evidence-backed editor into React Marketing: bilingual names, brand, description, highlights, source quote/path/page, specs JSON, meta description and saved HTML preview in sandboxed iframe.
- Removed Marketing native-workspace launch button; retained saved-profile validation inline. Existing product revision/memory API saves drafts, resets approval and preserves conflict detection. Added authenticated read-only HTML/SEO endpoint; suggestion applies to editable field before explicit save.
- Block SKU switch/reload while dirty; label preview as saved version. Other departments unchanged. Protocol v2-11.
- 72 tests PASS incl authenticated preview/save, TypeScript/build PASS. Cloud visual acceptance pending. No Haravan calls or mutations.


## 2026-11-05 AGY_005 acceptance reviewed
- Accepted owner-confirmed Antigravity Cloud report: Technical test name excluded, suggestions remain unapproved; Marketing editor/SEO/saved preview stay inline with save and dirty-state behavior. AGY_005 VERIFIED.
- Browser evidence belongs to Antigravity; prior Codex regression 72 PASS retained. Documentation-only update.
- Lesson: a meta-description character counter is an editorial target, not SEO/SERP certification; terminology acceptance covers tested examples. No Haravan operations.

## 2026-11-05 Marketing customer-copy policy
- Removed automatic CO/CQ highlights from refiner and certificate promise guidance from Marketing defaults. Shared cleaner excludes certificate-promise sentences and [Đã kiểm tra] from customer fields/read-save/render, preserving evidence/history.
- Expanded short 03026A description to ~1192 characters and four source-based highlights only when selected source contains matching SKU/manual edition evidence; local source page7 verified. Unknown products do not receive invented expansion.
- Read projection changes invalidate approval and regenerate HTML; persistent edits are saved through existing user save flow. Validation still checks original unsafe claims even when render filters them. Paragraph rendering improved.
- 73 regression tests PASS; final paragraph rendering quality suite PASS. Cloud visual acceptance pending. No Haravan operations.

## 2026-11-05 Marketing 03026A Cloud acceptance verified
- Antigravity inspected Marketing SKU 03026A on Streamlit Cloud after commit eae49ee.
- Confirmed form fields and rendered article preview iframe contain 0 occurrences of [Đã kiểm tra] and 0 ungrounded CO/CQ claim clauses.
- Expanded 4-paragraph description (1192 chars) and 4 highlights verified against catalogue_sample.pdf page 7 (index 6).
- 73 tests PASS. AGY_005 updated with section 6. No Haravan operations.

- Codex reviewed section 6 and documentation diffs; acceptance attributed to Antigravity. Lesson: redact login credentials from acceptance reports before committing. Documentation only; no Haravan operations.

## 2026-11-05 Concise copy, three-field SEO and SKU image sources
- Supersedes 1192-character 03026A copy: concise 250–450 target, nonrepeating format/edition highlights. Other products get explicit extractive shortening suggestion without fabricated padding; users review before save.
- Marketing now edits/persists SEO title (70), description (320) and slug with server validation, title alternatives and illustrative search preview. References: https://help.haravan.com/docs/products/create-product/huong-dan-tao-va-cap-nhat-san-pham-hang-loat-bang-cach-nhap-file-tren-admin-haravan/ ; https://developers.google.com/search/docs/appearance/title-link ; public https://bistextile.com/products/bxfd-series-boxun . Read-only research; no admin mutation.
- Replaced unrelated image gallery with SKU selector, PDF choice, bounded explicit URL discovery, English caption below each image, download and human-confirmed source selection. Exact-SKU PDF pages supply image candidates, not guaranteed product matches. Public HTML image ranking uses SKU/name metadata; no AI visual certification or recursive site crawl.
- Web links and selected provenance persist in local MemoryStore. Selected image stored under SKU/hash without overwriting earlier images, available to native studio. Dynamic/blocked sites and vector-only PDFs may need manual source/crop.
- 75 regression tests PASS before added private-URL test; final API/native suite 29 PASS. TypeScript/build PASS. Live public Boxun page discovery returned16 candidates; browser Cloud acceptance pending. No Haravan calls or mutations.
- Lesson: UI compatibility limits (70/320) differ from Google result truncation; colocated PDF images are candidates requiring selection, not automatic SKU identity proof.
