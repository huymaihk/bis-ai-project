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
