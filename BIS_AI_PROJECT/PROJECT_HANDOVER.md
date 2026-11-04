# 📘 BÀN GIAO TOÀN DIỆN DỰ ÁN CHO CODEX (BIS TEXTILE AI MULTI-AGENT SYSTEM)
> **Dành cho:** Codex / AI Assistant / Kỹ sư tiếp quản dự án  
> **Dự án:** Hệ thống Multi-Agent AI Tự động hóa Dữ liệu Sản phẩm Dệt May Quốc tế - BIS Textile  
> **Thời điểm bàn giao:** 2026-11-04  
> **Tài liệu nguồn cốt lõi đi kèm:** `.agents/PROJECT_MEMORY.md`, `MEMORY_GUIDE.md`, `catalog_master_data.py`

---

## 🧭 1. TỔNG QUAN HỆ THỐNG & MỤC TIÊU DỰ ÁN

### 1.1. Bối cảnh & Tầm nhìn
BIS Textile (bistextile.com) là đơn vị cung ứng thiết bị kiểm nghiệm, vật tư tiêu hao, hóa chất và tài liệu tiêu chuẩn kỹ thuật dệt may quốc tế (AATCC, ISO, ASTM, SDC, JIS). Dự án **BIS Textile AI** xây dựng một trung tâm điều hành tự động hóa (Autonomous Multi-Agent Command Center) nhằm:
1. Bóc tách toàn diện danh mục sản phẩm từ tài liệu kỹ thuật gốc (`catalogue_sample.pdf` 36 trang) thành dữ liệu có cấu trúc cho 97 SKUs.
2. Chuẩn hóa nội dung mô tả kỹ thuật 7 khối HTML chuyên sâu, loại bỏ hoàn toàn các thông tin thừa/sai lệch.
3. Tối ưu hóa SEO Google song ngữ (Việt - Anh) theo công thức chuẩn SERP 140 - 160 ký tự.
4. Đối soát trùng lặp 6 tầng chuyên sâu (Deep Content De-duplication) với toàn bộ 205 sản phẩm đang hoạt động trên Haravan và bistextile.com để bảo vệ nguyên trạng hệ thống cũ.
5. Tự động xử lý ảnh sản phẩm đạt chuẩn Studio thương hiệu quốc tế ($1254 \times 1254\text{ px}$) từ ảnh chụp thực tế hoặc tài liệu scan mà **tuyệt đối không làm biến dạng hình khối, số hiệu, font chữ hay logo**.
6. Đồng bộ đa kênh: Haravan Admin API (dạng bản nháp ẩn an toàn) và Google Sheets Master (23 cột).

### 1.2. Luồng dữ liệu E2E (End-to-End Data Pipeline)
```
[1. Catalogue PDF 36 Trang]
      │
      ▼
[2. agent_technical.py] ──> Bóc tách 97 SKUs, chuẩn hóa thông số dệt may, dựng 7 khối HTML
      │
      ▼
[3. agent_media.py & flow_2d_studio.py] ──> Bóc tách quang học, làm nét không biến dạng (Zero-Hallucination),
      │                                    ghép nền BIS_BACKDROP_1254.png + đổ bóng vật lý 3 lớp (1254x1254 px)
      ▼
[4. agent_marketing.py & ai_product_refiner.py] ──> Chuẩn hóa SEO Google song ngữ + Snippet SERP Preview
      │
      ▼
[5. agent_operations.py] ──> Quét Live Haravan API 205 sản phẩm:
      │                       ├── Khóa 28 sản phẩm trùng lặp (Deep Content De-duplication)
      │                       └── Mở khóa 69 sản phẩm mới 100%
      ▼
[6. app_ui.py (Streamlit HUD)] ──> Người dùng duyệt, chỉnh sửa WYSIWYG
      │                               └── learning_engine.py ghi nhớ vĩnh viễn vào feedback_memory.json
      ▼
[7. Xuất bản an toàn] ──> Đẩy sản phẩm ẩn (published: false) lên Haravan + Ghi Google Sheets Master 23 cột
```

---

## 🤖 2. KIẾN TRÚC MULTI-AGENT & PHÂN CÔNG NHIỆM VỤ

| Tên Module / File | Vai trò Agent | Trách nhiệm cốt lõi |
|:---|:---|:---|
| [`agent_leader.py`](file:///g:/My%20Drive/BIS_AI_PROJECT/agent_leader.py) | **Agent Leader** | Tổng chỉ huy điều phối vòng đời dữ liệu giữa các phòng ban; giám sát tiến độ E2E. |
| [`agent_technical.py`](file:///g:/My%20Drive/BIS_AI_PROJECT/agent_technical.py) | **Technical Agent** | Bóc tách PDF bằng `pymupdf`; trích xuất bảng thông số; sinh chuẩn 7 khối HTML; tra cứu từ điển `TEXTILE_GLOSSARY`. |
| [`agent_media.py`](file:///g:/My%20Drive/BIS_AI_PROJECT/agent_media.py) & [`flow_2d_studio.py`](file:///g:/My%20Drive/BIS_AI_PROJECT/flow_2d_studio.py) | **Media Agent** | Quản lý kho ảnh Google Drive; thực thi pipeline làm nét quang học không biến dạng; composite ảnh chuẩn Benchmark 1254x1254; quản lý review manifest. |
| [`agent_marketing.py`](file:///g:/My%20Drive/BIS_AI_PROJECT/agent_marketing.py) & [`ai_product_refiner.py`](file:///g:/My%20Drive/BIS_AI_PROJECT/ai_product_refiner.py) | **Marketing Agent** | Tạo tiêu đề song ngữ, slug URL, Meta Description chuẩn Google 140-160 ký tự; sinh thẻ tags dệt may. |
| [`agent_operations.py`](file:///g:/My%20Drive/BIS_AI_PROJECT/agent_operations.py) | **Operations Agent** | Giám sát rào chắn Haravan Guard (Mốc 20/10/2026); thực thi đối soát trùng lặp 6 tầng; quản lý Google Sheets Master. |
| [`agent_knowledge.py`](file:///g:/My%20Drive/BIS_AI_PROJECT/agent_knowledge.py) & [`keep_form_translator.py`](file:///g:/My%20Drive/BIS_AI_PROJECT/keep_form_translator.py) | **Knowledge Agent** | Lưu trữ thư viện sách tiêu chuẩn AATCC/ISO, Manual, CO/CQ; dịch tài liệu kỹ thuật giữ nguyên 100% định dạng bằng PDFMathTranslate / deep-translator. |
| [`learning_engine.py`](file:///g:/My%20Drive/BIS_AI_PROJECT/learning_engine.py) | **Learning Engine** | Thu thập mọi lượt chỉnh sửa của người dùng trên UI, lưu vào `feedback_memory.json`, tự động inject few-shot vào prompt các lần sau. |
| [`app_ui.py`](file:///g:/My%20Drive/BIS_AI_PROJECT/app_ui.py) | **Command Center UI** | Web Dashboard Streamlit Cyberpunk/Canvas gồm 6 Tab chức năng, tích hợp xem trước WYSIWYG, SERP Preview, Studio 3D, đối soát sàn và phòng làm việc ảo. |

---

## ⚖️ 3. CÁC QUY CHUẨN KỸ THUẬT & NGHIỆP VỤ BẮT BUỘC (CRITICAL SPECIFICATIONS)

> [!IMPORTANT]
> Đây là các nguyên tắc bất di bất dịch đã được người dùng và chủ dự án phê duyệt. Codex tuyệt đối không được tự ý sửa đổi nếu không có yêu cầu rõ ràng.

### 3.1. Danh mục Master Data 97 SKUs
* File [`catalog_master_data.py`](file:///g:/My%20Drive/BIS_AI_PROJECT/catalog_master_data.py) là **nguồn chân lý gốc (Single Source of Truth)** đã được đối soát 1:1 với 36 trang của `catalogue_sample.pdf`.
* Mọi mã SKU phải giữ nguyên mã nguyên bản của AATCC (ví dụ: `03026A`, `03026B`, `09616A`, `48349F`, `28347A`, v.v.).

### 3.2. Chuẩn 7 Khối HTML Bài Viết Haravan
1. **Khối 1 (Tên tiếng Việt):** Font bold 20px, màu `#0f172a`.
   * **Cấu trúc bắt buộc:** `[Tên sản phẩm tiếng Việt] + [Mã SKU] + [Hãng sản xuất]`  
   *(Ví dụ: `Bộ thử sắc giác chuyên sâu Farnsworth Munsell 100-Hue Test 88900A AATCC`)*
2. **Khối 2 (Tên tiếng Anh):** Font bold 15px, màu xanh `#0284c7`, in hoa toàn bộ (UPPERCASE) giữ nguyên từ tài liệu gốc.
3. **Khối 3 (Hãng sản xuất):** `Hãng sản xuất: AATCC (Hoa Kỳ)`.
   * **LƯU Ý ĐẶC BIỆT:** **TUYỆT ĐỐI KHÔNG ĐƯỢC CHỨA CỤM TỪ `• Đơn vị phân phối: BIS Textile Việt Nam`**. Toàn bộ hệ sinh thái đã gỡ bỏ hoàn toàn cụm từ này.
4. **Khối 4 (Giới thiệu sản phẩm):** Mô tả kỹ thuật chuyên sâu, súc tích. Nhận thông số gộp từ Khối 6 nếu sản phẩm có quá ít dữ liệu.
5. **Khối 5 (Đặc điểm nổi bật):** Danh sách gạch đầu dòng rõ ràng có emoji ✨ ở mỗi ý.
6. **Khối 6 (Bảng thông số kỹ thuật):** Bảng 2 cột (Cột 1 rộng 39% nền xám nhạt `#f8fafc`, Cột 2 rộng 61% nền trắng `#ffffff`).
   * **Quy tắc linh hoạt:** Nếu sản phẩm có dưới 2 thông số, **không bắt buộc lập bảng** mà cho phép gộp trực tiếp vào phần Giới thiệu (Khối 4) để bài viết gọn gàng.
7. **Khối 7 (Tiêu chuẩn liên quan):** Danh sách các phương pháp thử liên quan (AATCC TM, EP, ISO, v.v.).

### 3.3. Chuẩn SEO Google Meta Description
Bắt buộc áp dụng đúng 100% công thức chuẩn SERP:
$$\text{[Tên tiếng Việt]} - \text{[Tên tiếng Anh]} \text{ ([SKU]) chính hãng } \text{[Brand]}. \text{ Tiêu chuẩn kiểm nghiệm dệt may quốc tế, đầy đủ chứng từ CO/CQ tại BIS Textile.}$$
* Độ dài: **140 – 160 ký tự**.
* Snippet preview trên UI hiển thị trên card nền tối có độ tương phản cao.

### 3.4. Rào chắn Haravan Guard & Đối soát trùng Deep Content (6 Tầng)
* **Haravan Guard:** Tuyệt đối KHÔNG ghi đè, sửa đổi hoặc xóa các sản phẩm tạo trước mốc an toàn **20/10/2026** trên Haravan. Mặc định `HARAVAN_PUSH_ENABLED = False` khi thử nghiệm.
* **Đối soát trùng lặp 6 tầng:**
  * **Tier 1:** Trùng mã SKU chính xác trong danh sách Variant SKU trên sàn.
  * **Tier 2:** Trùng mã SKU trong tên/option Variant.
  * **Tier 3:** Trùng mã SKU độc lập trong URL handle, tiêu đề hoặc tags (`\b{SKU}\b`).
  * **Tier 4 (ĐỌC FULL NỘI DUNG):** Mã SKU xuất hiện trong toàn bộ nội dung bài viết sàn (`body_html` hoặc `body_plain`).
  * **Tier 5:** Mã số cốt lõi (Core Number $\ge 5$ chữ số, ví dụ `03026` từ `03026A/B`) xuất hiện trong nội dung đi kèm ngữ cảnh hãng.
  * **Tier 6:** Trùng khớp cụm thuật ngữ tiếng Anh độc bản (ví dụ: `gray scale color change` $\rightarrow$ `28359C`, `gray scale staining` $\rightarrow$ `28360C`, `spray tester funnel` $\rightarrow$ `78911A`).
* **Hiện trạng dữ liệu đã kiểm chứng:** **28 sản phẩm trùng** (được khóa an toàn) và **69 sản phẩm mới 100%**.

### 3.5. Chuẩn Ảnh Thương Hiệu Golden Benchmark ($1254 \times 1254\text{ px}$)
Mọi ảnh thành phẩm đều phải tuân thủ chuẩn của thư mục `Google_Drive_Storage/6_Final_Composites/` (như `AATCC Weight Trio on BIS Backdrop.png`, `BIS_Metal_Rack_FIXED.png`, `09616A.png`):
1. **Độ phân giải:** $1254 \times 1254$ pixel (tỷ lệ 1:1), 24-bit RGB.
2. **Phôi nền:** `BIS_BACKDROP_1254.png` hoa văn lặp logo `Bis TEXTILE GARMENT` có gradient ánh sáng phòng chụp studio.
3. **Bảo toàn vật thể 100% (Zero-Hallucination):** Tuyệt đối KHÔNG dùng AI khuếch tán để vẽ lại từ đầu (vì sẽ méo chữ, sai rãnh cơ khí hoặc sai chính tả logo). Dùng thuật toán **LAB CLAHE trên kênh Luminance (L) + Bilateral Filter + High-Pass Unsharp Masking** trực tiếp trên ảnh chụp thật để khắc nét chữ chìm `2.0 KG` và logo `AATCC ®`.
4. **Bóng đổ vật lý 3 lớp:**
   * Ambient Occlusion dẹp sát chân đế (opacity ~85-90%).
   * Directional Soft Shadow tỏa mềm phía dưới/trước (opacity ~70%, blur 16px).
   * Phản xạ mờ mặt sàn (Subtle Floor Reflection) 18% mờ 1.8px.
5. **Bố cục:** Vật thể đặt ở trung tâm, chiếm 55% – 65% khung hình, chân đế chạm mốc $y = 980\text{ px}$.

---

## 📁 4. BẢN ĐỒ MÃ NGUỒN & CẤU TRÚC THƯ MỤC

```
g:\My Drive\BIS_AI_PROJECT\   (và bản đồng bộ tại C:\Users\Dell\bis-ai-project\BIS_AI_PROJECT)
├── .agents/
│   ├── PROJECT_MEMORY.md            # Bộ nhớ tri thức dài hạn cốt lõi (Bắt buộc đọc khi bắt đầu)
│   ├── rules/handover_sync.md       # Quy tắc đồng bộ handover
│   └── skills/                      # Các skill chuyên sâu (keep-form-translator, image-layout-translator)
├── Google_Drive_Storage/
│   ├── 1_Catalogues/                # Chứa catalogue_sample.pdf (36 trang gốc)
│   ├── 2_Manuals_Standards/         # Sách tiêu chuẩn AATCC/ISO, tài liệu hướng dẫn kỹ thuật
│   ├── 3_Certificates_CO_CQ/        # Chứng chỉ CO/CQ, COC gốc
│   ├── 4_Product_Images/            # Ảnh thô bóc tách từ PDF hoặc do người dùng tải lên ({sku}.jpg)
│   ├── 5_Studio_Backgrounds/        # Phôi nền BIS_BACKDROP_1254.png, BIS_BACKGROUND.png, podium...
│   ├── 5_Draft_Previews/            # Ảnh preview nháp ({sku}_preview.jpg)
│   ├── 6_Final_Composites/          # ẢNH THÀNH PHẨM ĐẠT CHUẨN 1254x1254 ({sku}.png, {sku}_final.jpg)
│   └── 8_AI_Memory/                 # Lưu trữ bộ nhớ đồng bộ đa máy
├── agent_leader.py                  # Agent chỉ huy luồng E2E
├── agent_technical.py               # Agent bóc tách PDF, HTML 7 khối, thông số dệt may
├── agent_media.py                   # Media Agent: quản lý ảnh Drive, composite, manifest
├── flow_2d_studio.py                # Engine xử lý ảnh Benchmark 1254x1254, quang học & đổ bóng 3 lớp
├── agent_marketing.py               # Marketing Agent: SEO Google, meta description
├── ai_product_refiner.py            # Engine tinh chỉnh SEO song ngữ chuẩn SERP
├── agent_operations.py              # Operations Agent: Haravan Guard, De-duplication 6 tầng, Sheets Master
├── agent_knowledge.py               # Knowledge Agent: Quản lý thư viện tiêu chuẩn & tài liệu
├── keep_form_translator.py          # Dịch thuật giữ nguyên 100% định dạng file
├── learning_engine.py               # Thu thập feedback & Few-shot learning
├── app_ui.py                        # Giao diện chính Streamlit (Cyberpunk HUD / 6 Tabs)
├── catalog_master_data.py           # Master Data 97 SKUs chuẩn AATCC đối soát 1:1 từ PDF
├── extracted_products_cache.json    # Cache dữ liệu 97 SKUs đang vận hành (69 mới, 28 trùng)
├── bistextile_existing_products.json# Dữ liệu 205 sản phẩm live quét từ Haravan & bistextile.com
├── feedback_memory.json             # Lịch sử chỉnh sửa của người dùng để AI tự học
├── config.py                        # Cấu hình API Keys (Haravan, Google Gemini, Drive...)
├── sync_memory.py                   # Script đồng bộ bộ nhớ dài hạn
└── PROJECT_HANDOVER.md              # File bàn giao này
```

---

## 🚫 5. "SỔ ĐEN" CÁC LỖI KỸ THUẬT ĐÃ GIẢI QUYẾT (BLACKBOOK - CẤM TÁI PHẠM)

| Mã lỗi | Mô tả lỗi trước đây | Nguyên nhân gốc rễ | Giải pháp chuẩn mực (Codex phải tuân thủ) |
|:---:|:---|:---|:---|
| **ERR-01** | Bắt nhầm trùng sản phẩm | Dùng Jaccard word overlap trên các từ chung (`det`, `nhuom`, `scale`) khiến các loại bột giặt khác nhau bị coi là trùng. | Sử dụng **Deep Content De-duplication 6 tầng**. Chỉ khóa trùng khi có SKU, mã số cốt lõi hoặc cụm thuật ngữ độc bản trong `body_html` / metadata. |
| **ERR-02** | Sản phẩm không được mở khóa khi hết trùng | Code cũ lọc `if "Haravan" in notes:`, khiến ghi chú chỉ chứa `bistextile.com` bị kẹt ở trạng thái `REJECTED`. | Bỏ điều kiện lọc text ghi chú. Khi `is_dup == False`, tự động reset sang `STATUS_EXTRACTED` và xóa sạch metadata đối soát cũ. |
| **ERR-03** | `NameError: name 're' is not defined` trên Streamlit Cloud | `import re` bị khai báo bên trong một hàm thay vì ở đầu file `app_ui.py`. | Mọi thư viện chuẩn (`re`, `json`, `time`, `os`, `sys`, `pathlib`, `cv2`, `PIL`) phải được import ngay tại đầu file `app_ui.py`. |
| **ERR-04** | Cụm từ "Đơn vị phân phối" tái xuất hiện | Regex chỉ xóa một phần chuỗi HTML hoặc hàm render tạo lại chuỗi này. | Áp dụng regex 3 lớp triệt để tại `app_ui.py`, `agent_technical.py`, `ai_product_refiner.py` và làm sạch dữ liệu trong cache json. |
| **ERR-05** | Render ký tự entity `&bull;` dạng chữ thô | Viết thẳng entity `&bull;` vào chuỗi markdown mà không bật cờ HTML. | Luôn sử dụng ký tự Unicode trực tiếp: `•` thay vì entity HTML `&bull;`. |
| **ERR-06** | Mất nội dung chi tiết bài viết sau khi quét live | Code cũ bỏ qua trường `body_html` và `body_plain` khi lưu store. | Lưu giữ đầy đủ `body_html`, `body_plain`, `variants`, `tags` vào `bistextile_existing_products.json`. |
| **ERR-07** | `re.PatternError: bad character range —-_` | Dấu gạch ngang `-` đặt ở giữa character class bị hiểu lầm là dải ký tự. | Luôn đặt dấu gạch ngang `-` ở vị trí cuối cùng trong character class: `[...—_-]`. |
| **ERR-08** | WYSIWYG reset lại nội dung khi bấm Lưu | Key của Streamlit widget bị trùng lặp hoặc render lại state mặc định. | Gán dynamic key theo SKU: `f"inp_vi_{sku}"`, `f"inp_desc_{sku}"` và cập nhật trực tiếp vào session state `cached_products`. |

---

## 💻 6. HƯỚNG DẪN THIẾT LẬP MÔI TRƯỜNG & VẬN HÀNH CHO CODEX

### 6.1. Môi trường thực thi & Đường dẫn Python
* **Hệ điều hành:** Windows 11.
* **Đường dẫn Python 3.15:** `C:\Users\Dell\AppData\Local\Programs\Python\Python315\python.exe`.
* **Quy tắc Terminal Sandbox:**
  * Do Python nằm trong AppData và workspace nằm trên ổ ảo Google Drive `G:\My Drive`, các lệnh chạy Python qua terminal sandbox phải sử dụng `BypassSandbox: true` để tránh lỗi phân quyền Windows (`ItemNotFoundException` hoặc `Access Denied`).
  * Tránh dùng chuỗi escape phức tạp lồng nhau trong PowerShell command line. Hãy viết script phụ trợ vào thư mục scratch rồi gọi thực thi script đó.

### 6.2. Khởi chạy Giao diện UI (Streamlit Local)
```powershell
& "C:\Users\Dell\AppData\Local\Programs\Python\Python315\python.exe" -m streamlit run "g:\My Drive\BIS_AI_PROJECT\app_ui.py" --server.port 8501 --server.headless true
```
* Truy cập trên trình duyệt: `http://localhost:8501`.

### 6.3. Triển khai & Vận hành Streamlit Community Cloud
* **Repository:** `https://github.com/huymaihk/bis-ai-project.git` (Branch: `main`).
* **Deploy URL:** `https://bisaitextile.streamlit.app`.
* **Hiện tượng Sleep ("Zzzz This app has gone to sleep..."):**
  * Đây là cơ chế tiết kiệm tài nguyên mặc định của Streamlit Cloud miễn phí khi không có tương tác một thời gian.
  * Chỉ cần nhấn nút màu xanh **"Yes, get this app back up!"** trên màn hình, web app sẽ tự động tỉnh dậy sau khoảng 30 giây.
* **Quy trình đẩy code lên Cloud:**
  Mọi chỉnh sửa tại `G:\My Drive\BIS_AI_PROJECT\` phải được đồng bộ sang git repo cục bộ `C:\Users\Dell\bis-ai-project\BIS_AI_PROJECT\`, commit và push lên `origin main`:
  ```powershell
  # 1. Copy file đã sửa sang repo git local
  # 2. Thực hiện git commit & push
  git -C "C:\Users\Dell\bis-ai-project\BIS_AI_PROJECT" add -A
  git -C "C:\Users\Dell\bis-ai-project\BIS_AI_PROJECT" commit -m "feat/fix: mô tả nội dung"
  git -C "C:\Users\Dell\bis-ai-project\BIS_AI_PROJECT" push origin main
  ```

### 6.4. Đồng bộ Bộ nhớ Dự án (Persistent Memory Sync)
Sau mỗi lần cập nhật và kiểm thử thành công, chạy lệnh:
```powershell
& "C:\Users\Dell\AppData\Local\Programs\Python\Python315\python.exe" "g:\My Drive\BIS_AI_PROJECT\sync_memory.py" --local-only --record-update "Nội dung cập nhật đã xác minh, kết quả test và việc còn tồn đọng"
```

---

## 📌 7. TRẠNG THÁI HIỆN TẠI & LỘ TRÌNH TIẾP NỐI (ROADMAP FOR CODEX)

### 7.1. Các hạng mục ĐÃ HOÀN TẤT 100%
- [x] Master data 97 SKUs bóc tách chính xác từ Catalogue PDF 36 trang.
- [x] Cơ chế 7 khối HTML và quy chuẩn SEO Google Meta Description song ngữ.
- [x] Haravan Guard và Đối soát trùng Deep Content 6 tầng (28 trùng, 69 mới).
- [x] Xóa bỏ triệt để cụm từ "Đơn vị phân phối: BIS Textile Việt Nam" trên toàn bộ bài viết.
- [x] Pipeline làm nét quang học không biến dạng và phôi nền chuẩn Studio Benchmark $1254 \times 1254\text{ px}$.
- [x] Hệ thống ghi nhớ phản hồi `learning_engine.py` và lưu trữ tri thức `.agents/PROJECT_MEMORY.md`.
- [x] Đồng bộ toàn bộ mã nguồn lên GitHub `origin main`.

### 7.2. Các việc CẦN LÀM TIẾP THEO (Pending Tasks)
1. **Google Sheets Service Account Credentials:**
   * Tệp khóa service account hiện tại bị lỗi `Invalid JWT Signature / invalid_grant`. Cần thay thế credentials hợp lệ trong cấu hình bảo mật nếu chủ dự án yêu cầu kích hoạt lại đồng bộ tự động lên Google Sheets Master bằng service account. (Hiện tại tính năng đọc ghi local và Drive vẫn hoạt động bình thường).
2. **Xuất bản lên Haravan:**
   * Hiện tại cờ an toàn `HARAVAN_PUSH_ENABLED` đang đặt là `False` (bảo vệ tuyệt đối cho shop). Khi chủ dự án duyệt lệnh xuất bản cho 69 sản phẩm mới, Codex kích hoạt đẩy ở chế độ ẩn (`published: false`) để kiểm tra hiển thị trước khi công khai.
3. **Mở rộng kho ảnh sản phẩm thực tế:**
   * Tiếp tục tiếp nhận ảnh chụp thật của các thiết bị còn lại đặt vào `Google_Drive_Storage/4_Product_Images/` và chạy `flow_2d_studio.py` để tự động tạo toàn bộ ảnh đạt chuẩn $1254 \times 1254\text{ px}$.


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
