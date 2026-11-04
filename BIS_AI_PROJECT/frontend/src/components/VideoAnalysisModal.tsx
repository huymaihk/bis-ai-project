import React from 'react';
import { ADAPTER_ENDPOINTS, DEFAULT_BACKEND_CONFIG } from '../services/bisBackendAdapter';
import { X, CheckCircle2, Sparkles, Terminal } from 'lucide-react';

interface VideoAnalysisModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const VideoAnalysisModal: React.FC<VideoAnalysisModalProps> = ({
  isOpen,
  onClose,
}) => {
  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="video-analysis-modal-title"
      className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 overflow-y-auto"
    >
      <div className="bg-[#12141A] border border-[#323846] rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto p-6 space-y-6 text-xs text-[#D1D5DB]">
        <div className="flex items-start justify-between gap-4 border-b border-[#222631] pb-4">
          <div>
            <span className="font-mono text-[#38BDF8] text-[11px]">
              TÀI LIỆU THIẾT KẾ & KIẾN TRÚC KẾT NỐI BACKEND PYTHON
            </span>
            <h2
              id="video-analysis-modal-title"
              className="text-lg font-bold text-[#F3F4F6] mt-0.5"
            >
              Phân tích 2 Video Tham khảo, 3 Đề xuất Thiết kế & Hướng dẫn Kết nối Python
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Đóng cửa sổ phân tích"
            className="p-1.5 rounded-lg bg-[#181B23] text-[#9CA3AF] hover:text-white border border-[#323846]"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* 1. Phân tích 2 Video */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-[#0B0C0F] border border-[#222631] space-y-2">
            <div className="font-mono text-[#F59E0B] font-bold">
              VIDEO 1 (@axial.studio — SAMS Agent Office)
            </div>
            <ul className="space-y-1.5 text-[#D1D5DB]">
              <li>
                · <strong>Không gian nhóm Agent:</strong> Mặt bằng isometric tối màu có đường dẫn sáng nối giữa các phòng chức năng (Agent Lab, Studio, HQ).
              </li>
              <li>
                · <strong>Tạo hình Robot đại diện:</strong> Robot 3D bo góc vuông vức, bề mặt kim loại anodized bóng mịn (Vàng, Bạc, Xanh, Đỏ, Tím) với kính visor đen và đôi mắt sáng biểu cảm.
              </li>
              <li>
                · <strong>Trình bày luồng việc:</strong> Kết hợp bàn làm việc của từng Agent với thẻ tiến độ nổi và nút duyệt trực tiếp ("They ask. You answer.").
              </li>
            </ul>
          </div>

          <div className="p-4 rounded-xl bg-[#0B0C0F] border border-[#222631] space-y-2">
            <div className="font-mono text-[#E11D48] font-bold">
              VIDEO 2 (@renandooke — Editorial Dark Precision)
            </div>
            <ul className="space-y-1.5 text-[#D1D5DB]">
              <li>
                · <strong>Màu sắc & Ánh sáng:</strong> Nền đen carbon sâu (#0B0C0F) kết hợp sắc đỏ Crimson (#E11D48) mạnh mẽ, tạo độ tương phản tuyệt đối khi soi chi tiết hình ảnh.
              </li>
              <li>
                · <strong>Kiểu chữ & Bố cục:</strong> Phân cấp chữ sans-serif đậm khỏe khoắn đi cùng số thứ tự/thông số monospace thẳng hàng, chia khung bằng đường kẻ mảnh 1px.
              </li>
              <li>
                · <strong>Tư duy đối chiếu:</strong> Cách đặt tiêu đề và khung so sánh "FROM RAW. TO REAL." rất phù hợp với bàn đối chiếu Ảnh gốc → Bản chuẩn 1254×1254 của Image Studio.
              </li>
            </ul>
          </div>
        </div>

        {/* 2. Ba hướng thiết kế & Lý do lựa chọn */}
        <div className="space-y-3">
          <h3 className="text-sm font-bold text-[#F3F4F6]">
            3 Phương án Thiết kế Đề xuất & Lựa chọn cho BIS TEXTILE AI
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="p-3.5 rounded-xl bg-[#0B0C0F] border border-[#222631]">
              <div className="font-bold text-[#F3F4F6]">
                Hướng 1: Warm Ivory Editorial Studio
              </div>
              <p className="text-[#9CA3AF] mt-1">
                Lấy tông kem sáng của trang giới thiệu SAMS làm nền chính. Nhẹ nhàng nhưng độ tương phản khi soi ảnh thiết bị nền trắng 1254×1254 chưa tối ưu.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-[#0B0C0F] border border-[#222631]">
              <div className="font-bold text-[#F3F4F6]">
                Hướng 2: Full 3D Spatial Sim Map
              </div>
              <p className="text-[#9CA3AF] mt-1">
                Dành phần lớn màn hình cho bản đồ 3D giả lập văn phòng. Bắt mắt nhưng chiếm diện tích thao tác bảng biểu kỹ thuật và PDF.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-[#181C26] border-2 border-[#0EA5E9]">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white">
                  Hướng 3 (Đã chọn): Obsidian Precision & Tactile Agent Studio
                </span>
                <CheckCircle2 className="w-4 h-4 text-[#38BDF8] shrink-0" />
              </div>
              <p className="text-[#D1D5DB] mt-1">
                Kết hợp khung làm việc tối chuẩn phòng Lab của Video 2 (giúp đánh giá ảnh trắng 1254×1254 chính xác nhất) với hệ thống Robot Agent phân màu kim loại và sơ đồ luồng thu gọn được từ Video 1.
              </p>
            </div>
          </div>
        </div>

        {/* 3. Hướng dẫn nối Backend Python & Streamlit */}
        <div className="p-4 rounded-xl bg-[#0B0C0F] border border-[#222631] space-y-2.5">
          <div className="flex items-center gap-2 text-sm font-bold text-[#F3F4F6]">
            <Terminal className="w-4 h-4 text-[#38BDF8]" />
            <span>Kiến trúc Adapter Kết nối Backend Python / Streamlit Hiện có</span>
          </div>
          <p className="text-[#9CA3AF]">
            Toàn bộ giao tiếp dữ liệu được tách riêng tại <code className="font-mono text-[#E2E8F0]">src/services/bisBackendAdapter.ts</code>. Khi chuyển từ bản mẫu sang môi trường thực tế, chỉ cần cấu hình biến môi trường <code className="font-mono text-[#38BDF8]">VITE_BIS_PYTHON_API_URL</code> trỏ về FastAPI / Streamlit Bridge (`{DEFAULT_BACKEND_CONFIG.pythonBaseUrl}`):
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 font-mono text-[11px] text-[#E2E8F0]">
            {Object.entries(ADAPTER_ENDPOINTS).map(([key, val]) => (
              <div key={key} className="p-2 rounded bg-[#12141A] border border-[#222631]">
                <span className="text-[#9CA3AF]">{key}:</span> {val}
              </div>
            ))}
          </div>
        </div>

        {/* 4. Trạng thái khởi tạo UI/UX Pro Max CLI (npx uipro-cli init) */}
        <div className="p-4 rounded-xl bg-[#0B0C0F] border border-[#0EA5E9]/40 space-y-2.5">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 text-sm font-bold text-[#F3F4F6]">
              <Sparkles className="w-4 h-4 text-[#F59E0B]" />
              <span>UI/UX Pro Max Design System (Đã khởi tạo qua CLI)</span>
            </div>
            <span className="px-2 py-0.5 rounded bg-[#16A34A]/20 text-[#4ADE80] font-mono text-[10px] border border-[#16A34A]/40">
              ACTIVE · v2.x
            </span>
          </div>
          <p className="text-[#9CA3AF]">
            Bộ quy chuẩn <code className="font-mono text-[#F59E0B]">ui-ux-pro-max</code> đã được cài đặt vào dự án tại{' '}
            <code className="font-mono text-[#E2E8F0]">.gemini/skills/ui-ux-pro-max</code>,{' '}
            <code className="font-mono text-[#E2E8F0]">.agent/skills/ui-ux-pro-max</code> và lưu trữ cấu hình chuẩn tại{' '}
            <code className="font-mono text-[#38BDF8]">design-system/bis-textile-ai/MASTER.md</code>:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] text-[#D1D5DB]">
            <div className="p-2.5 rounded bg-[#12141A] border border-[#222631]">
              <strong className="text-white block mb-0.5">8D Tactile Depth & Metallic Grid</strong>
              Đổ bóng đa tầng (<code className="font-mono text-[#F59E0B]">.card-8d-*</code>) và mặt sàn kim loại phay xước 2 cấp (<code className="font-mono text-[#F59E0B]">.agent-floor-grid</code> 48px/16px).
            </div>
            <div className="p-2.5 rounded bg-[#12141A] border border-[#222631]">
              <strong className="text-white block mb-0.5">Chuẩn Pre-Delivery Checklist</strong>
              100% Lucide SVG icons, <code className="font-mono text-[#38BDF8]">cursor-pointer</code>, vòng focus bàn phím rõ nét, tương phản &gt; 4.5:1 và hỗ trợ <code className="font-mono text-[#38BDF8]">prefers-reduced-motion</code>.
            </div>
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 bg-[#0EA5E9] hover:bg-[#0284C7] text-white font-semibold rounded-lg"
          >
            Đóng và Tiếp tục Thao tác Bản mẫu
          </button>
        </div>
      </div>
    </div>
  );
};
