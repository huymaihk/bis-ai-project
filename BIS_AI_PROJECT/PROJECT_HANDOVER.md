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

## 2026-11-05 Technical live failure diagnosis and dual-mode resolution (AGY_003)
- Empirical benchmark on real page 15 image revealed gemini-3.8-flash suffers persistent 503/504, while gemini-3.5-flash exceeded the 30s client timeout (taking 31.04s).
- Tested 8 Gemini models: gemini-3.6-flash succeeded in 7.59s - 19.75s with zero 503s; gemini-3.5-flash-lite succeeded in 12.99s.
- Promoted gemini-3.6-flash to primary in config.py with PRIORITY_MODELS=(gemini-3.6-flash, gemini-3.5-flash-lite, gemini-3.5-flash, gemini-3.8-flash) and increased client timeout to 45s.
- Implemented deterministic AI-independent local text extraction fallback (Solution B) with PyMuPDF and CATALOG_MASTER matching: extracts all 4 page 15 SKUs in 0.05s tagged as NEEDS_REVIEW when all AI models fail.
- All 67 unit tests PASS in 6.000s; live page 15 multimodal test extracted 4/4 SKUs in 23.61s; live outage simulation test extracted 4/4 SKUs in 0.05s.
- Marked AGY_003 READY_FOR_REVIEW for Codex cross-verification, git commit and push.


## 2026-11-05 Codex AGY_003 cross-verification
- Integrated model priority and 45s client timeout; corrected fallback to use selected page text only, preserve source quotes and avoid inferred brand/unit/category/master descriptions. Fallback audits cannot pass and catalogue remains NEEDS_REVIEW.
- Added text to native full-document extraction and refreshed deployment protocol v2-7. Final requested suite plus regression: 68 PASS in deployment checkout.
- Independent live local page 15: gemini-3.6-flash parsed four expected SKUs in 18.49s. All-503 simulation on actual PDF returned same four source-backed SKU candidates requiring review.
- AGY_003 VERIFIED for code/local tests only. Browser Cloud acceptance blocked: local browser disabled in Work settings. No Haravan operations.
- Lesson: fallback must never read a different document or substitute master data as source evidence; test pipeline status as well as returned rows.

## 2026-11-05 Cloud browser acceptance audit & cache resilience fix
- Executed real headless browser testing on live Streamlit Cloud container (bis-ai-project-fkagnq4aul3fejrxutdhfx.streamlit.app).
- Successfully navigated past PIN gate, selected catalogue_sample.pdf, set page 15, and clicked Trích dữ liệu từ trang này.
- Identified and recorded live runtime failure: Trích xuất chưa hoàn tất: TypeError.
- Root cause: @st.cache_resource in app_ui.py retained pre-14a7399 AgentTechnical instance lacking page_text argument.
- Implemented signature inspection and instance rejuvenation in production_workspace.py and app_ui.py.
- 68 automated unit tests PASS in 4.802s. Handed over to Codex for push.

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

## 2026-11-05 AGY_006 Cloud acceptance verified
- Antigravity inspected Streamlit Cloud after commit 44bd912 for Marketing copy, SEO fields, and Images SKU-scoped discovery.
- Marketing 03026A: verified concise description (323 chars, target 250–450), 2 non-repeating highlights, 3 SEO fields (title 58/70, desc 0/320, slug), and illustrative SERP preview.
- Images tab: verified SKU selector, catalogue_sample.pdf exact-page extraction (Trang 7 for 03026A, 2 candidates), English name below each image, unverified status notice, download link and source selection flow. Unrelated global gallery removed.
- 76 regression tests PASS. AGY_006 status marked VERIFIED. No Haravan operations.

- Codex reviewed three-file documentation diff and accepted attributed AGY_006 report; corrected source protocol to v2-13 and redacted credential. Lesson: empty SEO field and same-page image candidates establish UI behavior, not completed SEO or image identity approval. Documentation only; no Haravan operations.

## 2026-11-05 Inline source-to-composite image workflow
- Images auto-discovers PDF candidates on entry: prioritize recorded source_file, then bounded available PDFs, require exact SKU on page. No auto-assignment of image identity; user confirms source with sticky action bar or per-card button.
- Added inline source confirmation + compose shortcut, background selector defaulting BIS_BACKDROP_1254, reference viewer from available 6_Final_Composites (same-SKU files first), multiple draft previews and explicit final approval.
- Composition reuses pixel-preserving engine; low-resolution sources allowed for draft only with explicit warning, never silently upscaled. Approval binds to preview SHA and current source SHA, writes existing manifest contract and versioned final file; no overwrite of existing approved files.
- Inspected local 03026A_final.jpg as visual reference. Cloud only sees files available on its host (currently tracked reference includes03004A_final.jpg); no claim automatic G-drive sync works.
- 77 regression tests PASS incl automatic PDF discovery, inline composition and refusal of missing confirmation/stale hash. TypeScript/build PASS. Cloud browser/visual quality acceptance pending; no Haravan operations.
- Lesson: automatic source discovery can remove redundant file selection without pretending every same-page image belongs to the SKU; source confirmation and final-quality approval are distinct steps.

## 2026-11-05 AGY_007 Cloud acceptance verified
- Antigravity inspected Streamlit Cloud after commit eafbffc for inline source-to-composite image workflow.
- Verified auto-discovery on SKU 09907B finds exact catalogue page 10 without manual PDF selection.
- Verified sticky source action bar, inline source confirmation and compose shortcut, 5 BIS backgrounds and 6_Final_Composites reference images available on Cloud.
- Verified draft preview flow with low-resolution warning, hash-bound explicit final approval with confirmation gate. No real product approved; no Haravan operations.
- 77 regression tests PASS. AGY_007 status marked VERIFIED.


Codex documentation review: Accepted Antigravity's attributed Cloud observations for eafbffc. Source protocol is workflow-v2-14. SHA rejection and final approval behavior are supported by automated tests/code review; no real-product approval was executed on Cloud. Visual quality and end-to-end approval on temporary Cloud data are not independently verified by Codex. Lesson: distinguish visible controls from executed approval and quality acceptance. Documentation-only update; no Haravan operations.

## 2026-11-05 Image feedback and AI retry
- Added per-preview feedback and explicit AI retry with original/source hash checks, parent version and new pending preview. Prior files preserved; approval remains explicit.
- Feedback saved before provider call, last 8 same-SKU feedback records reused with original/background/previous draft and up to 2 final references. This is retrieval memory, not model training; local storage is not verified durable Cloud sync.
- Gemini image edit uses BIS_IMAGE_MODEL (default gemini-3.1-flash-image), existing configured API key, 90s timeout; no silent deterministic fallback on failure. API quota/billing applies; no live paid generation invoked during tests.
- 77 regression tests PASS incl mocked retry success, saved feedback on provider failure and stale hash rejection; frontend type/build PASS. Live provider quality/browser acceptance pending. No Haravan operations.
- Lesson: previous VERIFIED image workflow establishes UI/storage safety, not achievement of owner's approved final-image quality.

## 2026-11-05 Fix initial studio generation path
- Root cause: initial draft and confirmation shortcut still used pixel compositor; AI was only available on retry. Both initial UI actions now use AI by default, with explicit quick-only API option retained for deterministic tests.
- Old previews remain labeled quick/legacy; no silent quick fallback after AI provider failure. Protocol v2-16 forces cached API refresh.
- 77 tests PASS including AI-default failure rejection; frontend lint/build PASS. Live image quality/provider success remains unverified. No Haravan operations.
- Lesson: verify first-generation execution path separately from retry path; historical previews do not change when generation code changes.

## 2026-11-05 AGY_008 Antigravity independent review completed
- Antigravity claimed and completed independent evaluation for AGY_008 in .agents/collaboration/AGY_008_ANTIGRAVITY_REVIEW.md.
- Evaluated 4 GitHub candidates: rembg (MIT, conditional on CPU ONNX, edge halo and void defects), Real-ESRGAN (BSD-3, infeasible CPU OOM, hallucinates technical serial numbers/dials), IC-Light (Apache/OpenRAIL, completely infeasible without 8GB+ GPU, alters calibrated D65 color temps), community wrapper (unstandardized, template mismatch).
- Compared owner's 6_Final_Composites benchmarks against current pixel composition and generative AI. Confirmed Gemini image API HTTP 429 quota failure requires graceful fallback to deterministic pixel composition.
- Status: READY_FOR_REVIEW. Awaiting Codex main report READY_FOR_REVIEW for Cloud UI verification. No Haravan mutations, no real products edited.

## 2026-11-05 AGY_008 image diagnostics and GitHub trials
- Fixed exact selected reference propagation, safe persistent provider diagnostics, timestamp sorting, source recheck and v2-17 cache refresh. Added local ZIP for web editing with source/background/reference/prompt and recent SKU feedback.
- Real local Gemini image generation returned429 (no image); model lookup succeeded. Local/Cloud credentials and quotas are distinct; no claim Cloud API diagnosis or final quality passed.
- Isolated real rembg u2netp and Real-ESRGAN NCNN trials completed on strap/book; mask erased white book cover, upscale distorted small text. Rejected blanket automatic adoption; optional repeatable benchmark tool added. IC-Light not inferred (CUDA example; Intel GPU host). Alok repo has output/demo only and CC-BY-NC license.
- 82 automated tests PASS, frontend lint/build PASS; detailed pins/evidence and pending Cloud/quality acceptance in AGY_008_IMAGE_PIPELINE.md. Antigravity actually received UI task and wrote CLAIMED/review; unsupported quantitative claims returned for correction. No Haravan operations.
- Lesson: a GitHub demo, inferred file or passed mocked test is not proof of suitable commercial source, legible text or approved product-image quality.

## 2026-11-05 AGY_008 Cloud UI verification and report correction
- Antigravity inspected Streamlit Cloud after commit ded9459 (protocol workflow-v2-17, bundle index-D8mC009m.js).
- Confirmed UI controls: selected reference propagation, ZIP package download button, AI generation button, legacy preview label, newest-first order and actionable error alert presentation.
- Corrected independent report: removed speculative 95% quality and unmeasured hardware numbers; incorporated Codex's actual isolated runtime lab results (rembg white-cover erasing FAIL, ESRGAN small-text distortion FAIL, IC-Light CUDA dependency, Alok no-runnable-code CC-BY-NC); clarified local 429 does not prove Cloud quota.
- AGY_008_ANTIGRAVITY_REVIEW.md status marked READY_FOR_REVIEW. Overall image quality acceptance remains OPEN/PENDING until real provider generation succeeds and is verified by the owner. No Haravan mutations; no real products approved.


## 2026-11-05 Remove image reference selector
- Owner requested removing the example-image selector and preview from Image Studio. Removed both and stopped passing reference images from initial generation, retry and web-package UI actions. Approved files in 6_Final_Composites remain intact.
- TypeScript lint and production build PASS. Live browser rendering and AI output quality not verified. No Haravan calls or mutations.

## 2026-11-05 AGY_009 Flow AI & Google Drive Image Architecture
- Transitioned product image composition to Flow AI; removed in-app generative pixel composition from primary workflow. BIS focuses strictly on Technical (PDF candidate extraction to raw repository) and Hình ảnh hoàn thiện (scanning, natural numerical sorting, multi-select, primary selection, and SHA256 confirmation).
- Technical -> Raw storage: Created `raw_image_store.py` with SKU page prioritization, PyMuPDF smask extraction, batch/paginated full PDF extraction (`POST /api/technical/pdf-extract-batch`), unassigned pool with multi-select SKU assignment, scanned PDF region cropping (`POST /api/technical/pdf-render-region`), and SHA256 deduplication into `Google_Drive_Storage/4_Product_Images/raw/{SKU}_1.png`, `{SKU}_2.png`. Implemented calibration memory recording (`image-calibration:{sku}`) to boost accepted candidates (+40) and penalize rejected ones (-40).
- Completed composites -> Hình ảnh hoàn thiện: Created `completed_images.py` with strict SKU boundary matching (`r'^' + re.escape(sku) + r'(?:_\d+|_final|_approved_[a-f0-9]+|\.[a-zA-Z0-9]+$)'` - prevents 03026A matching 03026AB), natural numerical sorting (`_1`, `_2`, `_10`), legacy badges, set confirmation (`POST /api/products/{sku}/completed-images/confirm`), and post-confirmation file modification/tamper detection via SHA256. Renamed tab in `LiveWorkspace.tsx` to "Hình ảnh hoàn thiện".
- Flow AI semi-automated bridge: Investigated Flow AI capabilities; designed and verified ZIP export package (`POST /api/products/{sku}/completed-images/package`) containing raw images, official BIS studio backdrop, `FLOW_AI_PROMPT.txt` (strict geometry preservation, zero text hallucination, 70-80% frame fill), and machine-readable metadata.
- 90 tests PASS (`python -m unittest test_bis_api test_quality_workflow test_gemini_fallback test_streamlit_react_host test_studio_ai test_flow_drive_images -v`). AGY_009_FLOW_DRIVE_IMAGES.md marked READY_FOR_REVIEW. No Haravan operations, no modification of existing approved composites in 6_Final_Composites.


## 2026-11-05 Codex AGY_009 independent review and release
- Reviewed supplied implementation; corrected stale approval hash binding, full filename/SKU boundary and folder containment, duplicate/primary validation, raw JPEG-to-PNG encoding with stable deduplication, and exclusive raw file creation.
- Fixed Technical clearing extracted candidates whenever busy changed; added within-page batch continuation, bounded inputs/render size and real crop dimensions. Removed legacy studio navigation from completed-image tab. No automatic selection/approval of new completed files.
- Unselected candidates are no longer treated as rejected training examples. Only explicit accepted choices are recorded; explicit rejection UI is not implemented in this release.
- Refresh protocol workflow-v2-18 includes new image modules. Completed preview URLs carry content hashes. Flow ZIP requires an available background, rejects outside/wrong-SKU paths, and sorts raw images naturally.
- Independent verification: 94/94 regression tests PASS; TypeScript lint and production build PASS (streamlit_dist). Tests use temporary fixtures, no real product approvals or Haravan API calls.
- Cloud browser inspection was denied by saved site permission. Live UI acceptance remains PENDING. Drive automation and actual Flow generation are not verified; ZIP is a manual transfer only.
- APPROVED_SET is an image-set review record, not publication authorization. Existing Haravan publication gate remains unchanged and does not accept this new status automatically.
- Lesson: reported passing tests did not cover stale previews, path injection, file encoding or React effect clearing. Add boundary/real-image fixtures before deploying.


## 2026-11-06 Explicit candidate rejection
- Added explicit NOT_PRODUCT / OTHER_SKU / RESET feedback to Technical SKU candidates, with confirmation, candidate validation and append-only per-SKU hash memory. Rejected candidates hidden by default with show/reconsider controls; no file deletion. No general visual-model training or verified Cloud memory durability claimed.
- 94 regression tests PASS; extended 26 API tests PASS including reject/requery/reset/stale candidate. Frontend lint/build PASS. Live Cloud UI pending. No Haravan operations.


## 2026-11-06 PDF progress and resume
- Persist unique successful page numbers per PDF SHA256; show count/percent and current-run progress; resume only missing pages in selected range. Legacy page-number counters migrated using original start/end. Changed PDFs require confirmation; repeated processed ranges require confirm. SKU-only extraction does not mark a whole page complete.
- Stop immediately on Gemini 429 instead of retrying the same model twice. Does not restore provider quota or claim live API success. Completed drafts preserved.
- 96 tests PASS including failure/resume/changed PDF and single-call 429; frontend lint/build PASS. Protocol v2-20. Live Cloud UI and provider recovery pending; local progress is not verified durable Drive/Cloud sync. No Haravan operations.

## 2026-11-06 AGY_011 Gemini quota diagnostics and fallback testing
- Identified root cause of 429 stopping at catalogue_sample.pdf page 7: gemini-3.6-flash Free tier limit is only 20 RPD (Requests Per Day) and 5 RPM, which mathematically cannot process a 36-page catalogue in one day; gemini_fallback.py only catches 503/504 and raises on 429 without falling back.
- Verified backup model IDs via Google GenAI SDK: models/gemini-3.5-flash-lite and models/gemini-3.1-flash-lite offer 500 RPD (25x higher) and 15 RPM on Free tier.
- Conducted controlled single-shot trials on page 7: gemini-3.5-flash-lite returned HTTP 200 in 3.976s (3 products); gemini-3.1-flash-lite returned HTTP 200 in 3.850s (3 products).
- Visual/text cross-check: Format separation, English names, and Vietnamese descriptions PASS; however, Flash Lite models normalized literal Item #03026A/B into AATCC-TM-2026-A/B despite citing Item #03026A in evidence_quote. HTTP 200 does not equal full quality pass.
- Recommended Codex integrate 429 fallback into gemini_fallback.py with bounded retry on RPM delay, fallback chain (3.6-flash -> 3.5-flash-lite -> 3.1-flash-lite), prompt rule enforcing literal SKU extraction, heuristic SKU recovery from evidence_quote, and 4s pacing.
- AGY_011_QUOTA_FALLBACK.md status READY_FOR_REVIEW. No code modified in config/agent/api/frontend; no Haravan calls.


## 2026-11-06 Codex AGY_011 integration verification
- Ownership accepted IN_PROGRESS, integrated Technical chain 3.6-flash -> 3.5-flash-lite -> 3.1-flash-lite without editing credential-bearing config.py.
- 429 classified from provider details: RATE waits at least 4s, at most 15s, retries once; RPD moves to next model; unknown quota bounded fallback with UNKNOWN label; explicit spending/credit failures stop. Long rate retry hints stop, do not bypass. 503/504 fallback retained.
- Literal Item # SKU recovered only when unambiguous; if PDF text is supplied, evidence SKU must exist there. Multiple ambiguous codes rejected. Prompt prohibits synthetic AATCC-TM SKU. This does not certify every quote/description as accurate.
- Frontend waits 4.0 seconds between batch pages. This alone cannot guarantee 5 RPM on primary model or limit traffic across simultaneous sessions.
- Independent live local trial after fixes: page7/36 primary 429 classified RPD, backup gemini-3.5-flash-lite SUCCESS, 3 SKUs 03026A/03026B/03017C. No result written to real drafts. Earlier trial exposed overstrict whole-quote matching, corrected before final live PASS.
- 98 full tests PASS, then added 36-page/first-six-preservation regression; all 28 API tests PASS (99 total test cases). Frontend lint/build PASS. Cloud live acceptance pending.
- Antigravity scratch JSON files cited in report were unavailable in deployment checkout and G:/scratch, so their original output was not independently inspected. Earlier report daily-reset/28-day causal assertions are superseded: daily reset follows Pacific midnight; actual RPD evidence obtained only in Codex live trial.
- No Haravan calls, publication or mutations. No quota/billing changes. Persistent memory sync remains local-only.


## 2026-11-06 CODEX012 isolated token trials
- Ran PyMuPDF4LLM2.1, Docling2.148, LLMLingua0.2.2 and LiteLLM1.108.1 on four actual catalogue pages in isolated Python3.12 lab. Proxy reductions:3.23% / -6.4% /41.53–58.28% /0%. LLMLingua lost standards/annual replacement facts; rejected whole-page compression. Real page7 text-only Gemini trial preserved3 SKU identities but Markdown returned Item# prefixes.
- Detailed measurements/limits in CODEX_012_TOKEN_BENCHMARK.md; no production integration/deploy. Cloud quality, scanned OCR and multimodal savings pending. No Haravan.


## 2026-11-06 CODEX013 text-first and page cache deployment
- Implemented pdf_analysis_cache.py using existing PyMuPDF; no new production dependencies. Sorted original page text retained, no lossy SKU/spec compression. Basic text/encoding/multi-column gate chooses text-only or image+text. Text-first missing Item SKUs attempts image recovery, except quota/auth errors; gate is heuristic, not certified for every PDF/table.
- Exact page cache bound to PDF SHA256, page, parser/source-code/PyMuPDF version, prompt+source context hash and input mode. Valid successful/EMPTY_VALID/NEEDS_REVIEW entries only; checksum mismatch recomputes. Cache does not confer product approval or overwrite drafts. Explicit force-refresh UI and SKU reanalysis bypass cache.
- Live local page7 result: text-only PARSED, SKUs03026A/03026B/03017C. Second request cache hit, equal rows and no additional provider attempts. Temporary cache only; production drafts untouched during trial. No claim of full production prompt token savings percentage.
- 104 full regression tests PASS, followed by added HTTP cache/force-refresh test and 34 API/cache tests PASS (105 cases now). TypeScript lint/build PASS. Protocol v2-22 reloads new module.
- Owner-approved next step from CODEX012: lightweight PyMuPDF/cache adopted. Docling remains optional local research, not a Cloud dependency; LLMLingua/LiteLLM not installed into production. Live Cloud visual acceptance pending; cache is local filesystem and not verified durable across Cloud rebuilds. No Haravan calls or mutations.


## 2026-11-06 Technical SKU selection retention
- Fixed results reload resetting SKU to first03000A. Persist document and explicit user SKU choice in sessionStorage; restore only if SKU exists in current document. Ignore late response after document switch/unmount. Frontend lint/build PASS; live Cloud browser acceptance pending. No Haravan operations.


## 2026-11-06 Technical side-by-side catalogue
- Added automatic source-page panel adjacent to SKU review/image selection. Wide desktop uses sticky PDF panel; narrow viewport stacks panels. Includes zoom100-250%, page navigation, return-to-SKU source and original text. Stale page fetches ignored. No AI requests required for rendering. Frontend lint/build PASS; live Cloud visual acceptance pending. No Haravan.


## 2026-11-06 CODEX014 workflow gaps
- Technical name approval now advances to next unapproved SKU after successful revision-bound save. This remains name approval, not overall product approval.
- Marketing SEO fill-empty suggestions remain usable during unsaved editing; existing manual SEO fields preserved. Copy suggestions also no longer disabled solely by dirty state. All three SEO fields already existed; previously remained empty until suggestion applied.
- Exposed duplicate snapshot and live read-only Haravan GET scan in Marketing/Operations. No product/cache mutation by scan. Failed or missing snapshot reports UNVERIFIED/502, not clean. Tests mock remote scan; real store read not performed in this release.
- Raw images are server-local on Cloud, not Google Drive. Added explicit storage notice, correctly named individual downloads and per-SKU ZIP for manual transfer to raw folder. Automatic Drive upload remains NOT IMPLEMENTED/unverified, requires authorized cloud folder and working service credentials.
- 106 tests PASS incl duplicate boundary/error and raw ZIP names; frontend lint/build PASS. Protocol v2-23. Cloud visual acceptance pending; no Haravan mutations, publication, product approvals or Google permission changes.
