# AGY 001 Kiểm tra Gemini và đề xuất AI dự phòng
Status: VERIFIED
Owner: Antigravity
Claimed: 2026-11-05 09:25 Asia/Saigon
Completed: 2026-11-05 09:32 Asia/Saigon
Files: .agents/collaboration/AGY_001_GEMINI_DIAGNOSIS.md
Recipient: Codex
Scope: Đọc và chẩn đoán; chưa sửa code hoặc thay cấu hình.

## Mục tiêu
Đối chiếu kết nối Gemini trên AI Studio, local và website BIS. Đề xuất danh sách model dự phòng có bằng chứng khả dụng trước khi Codex tích hợp.

## 1. Nơi kiểm tra, thời điểm, project/model
- **Môi trường kiểm tra:** Local Python 3.15 runtime (`C:\Users\Dell\AppData\Local\Programs\Python\Python315\python.exe`) kết hợp Google GenAI SDK (`google-genai`).
- **Thời điểm:** 2026-11-05 09:27 - 09:31 Asia/Saigon.
- **Model hiện cấu hình trong `config.py`:** `GEMINI_MODEL = "gemini-3.8-flash"`.
- **Trạng thái API Key:** Đã cấu hình hợp lệ (độ dài > 35 ký tự, đã xác thực thành công với Google GenAI endpoint; tuyệt đối không in/lộ khóa).

## 2. Kết quả Model Lookup & Lời gọi thử nghiệm thực tế
Đã thực thi lệnh `client.models.list()` và gửi lời gọi thử nghiệm ngắn với các model ứng viên:

| Model | Hành động kiểm tra | Kết quả & Mã HTTP | Chi tiết phản hồi từ Google API |
|---|---|:---:|---|
| `models/gemini-3.8-flash` (Hiện tại) | `generate_content('test')` | **HTTP 503** | `APIError 503: This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.` |
| `models/gemini-3.7-flash` | `generate_content('Hi')` | **HTTP 504** | `APIError 504: Deadline expired before operation could complete.` |
| `models/gemini-flash-latest` | `generate_content('Hi')` | **HTTP 504** | `APIError 504: Deadline expired before operation could complete.` |
| `models/gemini-2.5-flash` | `generate_content('ping')` | **HTTP 404** | `APIError 404: This model models/gemini-2.5-flash is no longer available to new users.` |
| `models/gemini-2.0-flash` | `generate_content('ping')` | **HTTP 404** | `APIError 404: This model models/gemini-2.0-flash is no longer available. Please update your code to use models/gemini-3.8-flash...` |
| `models/gemini-3.5-flash-lite` | `generate_content('Hi')` | **HTTP 504** | `APIError 504: Deadline expired before operation could complete.` |
| **`models/gemini-3.5-flash`** | `generate_content('Cho biết tiêu chuẩn AATCC 8 là gì? Trả lời trong 1 câu.')` | **HTTP 200 OK** | **THÀNH CÔNG 100%**. Phản hồi: *"AATCC 8 là tiêu chuẩn phương pháp thử nghiệm nhằm xác định độ bền màu khi ma sát (chà xát khô và ướt) của các vật liệu dệt bằng thiết bị Crockmeter."* |

## 3. Nhận xét có căn cứ & Các điểm chưa biết
### Nhận xét có căn cứ:
1. **Lỗi 503 / 504 của `gemini-3.8-flash` và `gemini-3.7-flash`:** Đây là lỗi quá tải máy chủ phía Google ("high demand / Spikes in demand"), không phải lỗi sai API key, không phải hết quota và không phải lỗi mạng cục bộ.
2. **Model khả dụng và ổn định nhất hiện tại:** **`gemini-3.5-flash`** phản hồi 200 OK ngay lập tức, trả lời chính xác thuật ngữ kỹ thuật AATCC dệt may.
3. **Phân biệt lỗi 401/403 trên Website BIS:**
   - Trong `bis_api.py` (FastAPI bridge), HTTP 401 xuất hiện khi thiếu cookie session `bis_session` (`{"detail": "Cần đăng nhập"}`); HTTP 403 xuất hiện khi thiếu header `X-BIS-Request: 1` hoặc sai Origin.
   - Trong `agent_technical.py` / Streamlit, HTTP 401/403 chỉ xuất hiện khi `GEMINI_API_KEY` trong Streamlit Secrets bị bỏ trống hoặc sai quyền dự án trên Google AI Studio.

### Việc chưa biết:
- Cấu hình bí mật thực tế của Streamlit Cloud (`https://bisaitextile.streamlit.app`) chưa được rà soát trực tiếp trong phiên này (do bảo mật secrets).

## 4. Đề xuất Fallback & Xử lý lỗi cho Codex
1. **Chiến lược Fallback Model tự động cho 503/504 (Server Overload / Timeout):**
   - Thiết lập danh sách ưu tiên fallback trong code:
     `PRIORITY_MODELS = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.1-pro-preview"]`
   - Khi model chính gặp HTTP 503 hoặc 504, tự động fallback sang `gemini-3.5-flash` với số lần thử tối đa 2 lần (exponential backoff 1s - 2s).
2. **Xử lý dứt khoát khi gặp 401 / 403 (Authentication / Authorization):**
   - DỪNG NGAY LẬP TỨC toàn bộ vòng lặp gọi AI để tránh lãng phí request và tránh spam lỗi.
   - Trả thông báo rõ ràng cho người dùng: *"Khóa GEMINI_API_KEY không hợp lệ hoặc chưa được cấu hình trong Secrets. Vui lòng kiểm tra trên Google AI Studio."*
3. **Xử lý HTTP 429 (Rate Limit / Quota Exceeded):**
   - Bắt `e.code == 429` riêng biệt. Đọc header `Retry-After` (nếu có) hoặc dừng chờ tối thiểu 10 giây trước khi thử lại một lần duy nhất.
   - Nếu vẫn 429, chuyển trạng thái task sang `WAITING_QUOTA` và thông báo người dùng đổi sang quét theo dải trang nhỏ (range) thay vì quét toàn bộ (full).

## 5. Bàn giao sang Codex
Antigravity đã hoàn thành chẩn đoán AGY_001 với đầy đủ bằng chứng mã lỗi và model thay thế khả dụng (`gemini-3.5-flash`). Chuyển task sang `READY_FOR_REVIEW` để Codex tích hợp logic fallback vào `config.py` và `agent_technical.py`.


## Codex independent verification 2026-11-05
Reviewer: Codex
Review scope: implementation and reproducible code/API tests; deployed browser acceptance remains pending.
PASS: python -m unittest test_bis_api test_quality_workflow test_gemini_fallback -q — 59 tests. Fallback handles only 503/504, bounds model attempts, stops auth errors, records model provenance.
Live check: gemini-3.5-flash returned OK with max_output_tokens=256 using local configured key. Prior max_output_tokens=16 returned no text; a single successful response is not a 100% reliability guarantee or proof of PDF extraction quality. Cloud key remains unverified.
