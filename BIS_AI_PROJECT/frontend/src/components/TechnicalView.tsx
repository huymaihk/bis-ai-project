import React, { useState } from 'react';
import {
  ProductRecord,
  TechnicalSpecItem,
  VerificationStatus,
} from '../types/bisTypes';
import { ProductVisualCanvas } from './ProductVisualCanvas';
import { AgentRobotAvatar } from './AgentRobotAvatar';
import {
  FileText,
  ZoomIn,
  ZoomOut,
  Download,
  Maximize2,
  RotateCcw,
  Save,
  CheckCircle2,
  AlertTriangle,
  BookOpen,
  ArrowRight,
} from 'lucide-react';

interface TechnicalViewProps {
  product: ProductRecord;
  reduceMotion: boolean;
  onUpdateSpecStatus: (
    sku: string,
    specId: string,
    newStatus: VerificationStatus,
    newVal?: string
  ) => void;
  onChangePdfPage: (sku: string, page: number) => void;
  onProceedToMarketing: () => void;
}

export const TechnicalView: React.FC<TechnicalViewProps> = ({
  product,
  reduceMotion,
  onUpdateSpecStatus,
  onChangePdfPage,
  onProceedToMarketing,
}) => {
  const [selectedSpecId, setSelectedSpecId] = useState<string>(
    product.specs[0]?.id || ''
  );
  const [pdfZoom, setPdfZoom] = useState<number>(100);
  const [nameViInput, setNameViInput] = useState<string>(product.nameVi);
  const [nameEnInput, setNameEnInput] = useState<string>(product.nameEn);
  const [specValues, setSpecValues] = useState<Record<string, string>>(() => {
    const map: Record<string, string> = {};
    product.specs.forEach((s) => {
      map[s.id] = s.value;
    });
    return map;
  });
  const [savedBanner, setSavedBanner] = useState<string | null>(null);

  // Sync local state when SKU changes
  React.useEffect(() => {
    setNameViInput(product.nameVi);
    setNameEnInput(product.nameEn);
    const nextMap: Record<string, string> = {};
    product.specs.forEach((s) => {
      nextMap[s.id] = s.value;
    });
    setSpecValues(nextMap);
    setSelectedSpecId(product.specs[0]?.id || '');
    setSavedBanner(null);
  }, [product.sku, product.nameVi, product.nameEn, product.specs]);

  const activeSpec: TechnicalSpecItem | undefined =
    product.specs.find((s) => s.id === selectedSpecId) || product.specs[0];

  const thumbnailPages = [14, 15, 16, 17, 18];

  const handleSaveAllSpecs = () => {
    product.specs.forEach((spec) => {
      const val = specValues[spec.id] ?? spec.value;
      onUpdateSpecStatus(product.sku, spec.id, 'approved', val);
    });
    setSavedBanner(
      `Đã lưu và xác minh ${product.specs.length} thông số kỹ thuật từ ${product.catalogueFile} (Trang ${product.activePdfPage}).`
    );
  };

  const handleResetSpecs = () => {
    const resetMap: Record<string, string> = {};
    product.specs.forEach((s) => {
      resetMap[s.id] = s.value;
    });
    setSpecValues(resetMap);
    setSavedBanner('Đã làm mới dữ liệu trích xuất gốc từ trang PDF.');
  };

  return (
    <div className="p-3 lg:p-5 max-w-[1500px] mx-auto space-y-4">
      {/* Section Header Matching Storyboard Top-Left Panel */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-[#231D1A] border border-[#3E322C] rounded-2xl px-5 py-3">
        <div className="flex items-center gap-3">
          <AgentRobotAvatar
            department="technical"
            size="sm"
            isActive={true}
            reduceMotion={reduceMotion}
          />
          <div>
            <h1 className="text-base lg:text-lg font-bold text-[#FAF6F0]">
              Kỹ thuật (TECHNICAL)
            </h1>
            <p className="text-xs text-[#C4B5AA]">
              Trích xuất thông số kỹ thuật từ tài liệu · Đối chiếu PDF bên trái & dữ liệu trích dẫn theo trang bên phải
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="px-2.5 py-1 rounded-full bg-[#332924] text-[#F59E0B] font-mono border border-[#4D3D35]">
            Dữ liệu minh họa · G:\My Drive\BIS_AI_PROJECT
          </span>
          <button
            type="button"
            onClick={onProceedToMarketing}
            className="px-3.5 py-1.5 rounded-lg bg-[#D9382C] hover:bg-[#B82D22] text-white font-semibold inline-flex items-center gap-1.5 transition-colors"
          >
            <span>Sang bước Nội dung (Marketing)</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Saved Confirmation Toast */}
      {savedBanner && (
        <div className="bg-[#DCFCE7] border border-[#86EFAC] text-[#14532D] px-4 py-2.5 rounded-xl text-xs font-semibold flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-[#16A34A]" />
            <span>{savedBanner}</span>
          </div>
          <button
            type="button"
            onClick={() => setSavedBanner(null)}
            className="text-xs underline"
          >
            Đóng
          </button>
        </div>
      )}

      {/* MAIN STORYBOARD CARD: WARM IVORY WORKSPACE */}
      <div className="bg-[#F6F1EA] text-[#1F1916] border border-[#D8CEC2] rounded-2xl shadow-xl overflow-hidden">
        {/* Top Document File Bar */}
        <div className="px-4 py-2.5 bg-[#EFE8DE] border-b border-[#D8CEC2] flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-xs sm:text-sm font-semibold text-[#2B221E]">
            <FileText className="w-4 h-4 text-[#D9382C]" />
            <span>
              Tài liệu: <strong className="font-mono">{product.catalogueFile}</strong> (32.4 MB)
            </span>
          </div>
          <div className="flex items-center gap-2 text-xs text-[#6E5D53] font-mono">
            <span>Mã SKU đang đối chiếu: {product.sku}</span>
            <span>·</span>
            <span>Trang hiện tại: {product.activePdfPage} / {product.catalogueTotalPages}</span>
          </div>
        </div>

        {/* 2-COLUMN BODY: LEFT PDF VIEWER + RIGHT EXTRACTED SPECS & CITATION */}
        <div className="grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-[#D8CEC2]">
          {/* LEFT 7 COLS: THUMBNAIL STRIP + PDF PAGE RENDER */}
          <div className="lg:col-span-7 flex flex-col sm:flex-row min-h-[620px]">
            {/* Left Vertical Page Thumbnail Strip */}
            <div className="w-full sm:w-24 bg-[#EAE2D6] border-b sm:border-b-0 sm:border-r border-[#D8CEC2] p-2.5 flex sm:flex-col gap-2.5 overflow-x-auto sm:overflow-y-auto shrink-0">
              <div className="text-[11px] font-bold text-[#4A3B34] px-1 hidden sm:block">
                Trang
              </div>
              {thumbnailPages.map((pg) => {
                const isCurrent = product.activePdfPage === pg;
                return (
                  <button
                    key={pg}
                    type="button"
                    onClick={() => onChangePdfPage(product.sku, pg)}
                    className={`group flex flex-col items-center p-1.5 rounded-lg border-2 transition-all shrink-0 ${
                      isCurrent
                        ? 'bg-white border-[#D9382C] shadow-sm'
                        : 'bg-[#F5EFE6] border-[#C9BBAE] hover:border-[#8C7A6B]'
                    }`}
                  >
                    <div className="w-12 h-16 bg-white border border-[#DED4C8] rounded flex flex-col items-center justify-between p-1">
                      <div className="w-full h-1.5 bg-[#D9382C]/80 rounded-xs" />
                      <div className="w-8 h-8 rounded-xs bg-[#EAE2D6] flex items-center justify-center text-[8px] font-mono text-[#574B43]">
                        {pg === 16 || pg === 14 ? product.sku : `P.${pg}`}
                      </div>
                      <div className="w-full h-2 bg-[#E5DEC9]" />
                    </div>
                    <span
                      className={`text-[11px] font-mono mt-1 font-bold ${
                        isCurrent ? 'text-[#D9382C]' : 'text-[#574B43]'
                      }`}
                    >
                      {pg}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Center PDF Document Viewer */}
            <div className="flex-1 bg-[#524B46] flex flex-col">
              {/* Dark PDF Viewer Toolbar */}
              <div className="px-3.5 py-2 bg-[#36302C] text-[#F5EFE6] flex items-center justify-between text-xs font-mono">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded bg-[#241F1C] border border-[#574B43]">
                    {product.activePdfPage} / {product.catalogueTotalPages}
                  </span>
                </div>

                <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={() => setPdfZoom((z) => Math.max(80, z - 10))}
                    aria-label="Thu nhỏ trang PDF"
                    className="p-1 rounded hover:bg-[#4A423D]"
                  >
                    <ZoomOut className="w-3.5 h-3.5" />
                  </button>
                  <span className="px-2">{pdfZoom}%</span>
                  <button
                    type="button"
                    onClick={() => setPdfZoom((z) => Math.min(130, z + 10))}
                    aria-label="Phóng to trang PDF"
                    className="p-1 rounded hover:bg-[#4A423D]"
                  >
                    <ZoomIn className="w-3.5 h-3.5" />
                  </button>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[11px] text-[#D5C7BC] hidden md:inline">
                    Trang {product.activePdfPage}
                  </span>
                  <Download className="w-3.5 h-3.5 text-[#D5C7BC]" />
                  <Maximize2 className="w-3.5 h-3.5 text-[#D5C7BC]" />
                </div>
              </div>

              {/* Rendered White Catalogue PDF Sheet */}
              <div className="flex-1 p-4 sm:p-6 overflow-auto flex justify-center items-start">
                <div
                  className="w-full max-w-[460px] bg-white text-[#1E1916] rounded shadow-2xl border border-[#D8CEC2] p-5 space-y-3.5 transition-transform origin-top"
                  style={{ transform: `scale(${pdfZoom / 100})` }}
                >
                  {/* Catalogue Page Top Brand Header */}
                  <div className="flex items-baseline justify-between border-b border-[#E5E0D8] pb-2">
                    <div>
                      <div className="text-lg font-black tracking-tight text-[#D9382C] leading-none">
                        BIS
                      </div>
                      <div className="text-xs font-bold text-[#2B221E]">
                        Testing Equipment
                      </div>
                    </div>
                    <span className="text-[10px] font-mono text-[#786B62]">
                      {product.catalogueFile}
                    </span>
                  </div>

                  {/* Highlighted SKU & Product Title Box (Red Dashed Citation Frame) */}
                  <div className="p-2.5 rounded-lg border-2 border-dashed border-[#D9382C] bg-[#FFF8F6]">
                    <span className="inline-block px-2.5 py-0.5 rounded bg-[#D9382C] text-white font-mono font-bold text-xs">
                      {product.sku}
                    </span>
                    <h3 className="text-sm font-extrabold text-[#1E1916] mt-1.5 leading-snug">
                      {product.nameVi} ({product.nameEn})
                    </h3>
                  </div>

                  {/* Equipment Photo/Diagram inside PDF Page */}
                  <div className="h-44 rounded-lg border border-[#E2D9CE] overflow-hidden bg-[#F8F5F0]">
                    <ProductVisualCanvas
                      sku={product.sku}
                      variant="bis-reference"
                      backgroundId="bis-warm-ivory"
                      paddingPercent={8}
                      className="w-full h-full"
                    />
                  </div>

                  {/* Highlighted Specification Table on PDF Page */}
                  <div className="p-2.5 rounded-lg border-2 border-dashed border-[#D9382C]/80 bg-[#FFFDFB]">
                    <div className="text-xs font-extrabold text-[#1E1916] mb-1.5">
                      Thông số kỹ thuật / Specifications
                    </div>
                    <table className="w-full text-[11px] border-collapse">
                      <tbody className="divide-y divide-[#E5E0D8]">
                        {product.specs.map((sp) => {
                          const isSelected = sp.id === activeSpec?.id;
                          return (
                            <tr
                              key={sp.id}
                              onClick={() => setSelectedSpecId(sp.id)}
                              className={`cursor-pointer transition-colors ${
                                isSelected ? 'bg-[#FDECE9] font-bold' : 'hover:bg-[#F6F1EA]'
                              }`}
                            >
                              <td className="py-1 pr-2 text-[#4A3B34]">
                                {sp.labelVi} / {sp.labelEn}
                              </td>
                              <td className="py-1 pl-2 font-mono font-semibold text-[#1E1916] text-right">
                                {specValues[sp.id] ?? sp.value}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>

                  {/* PDF Page Footer */}
                  <div className="pt-1 flex items-center justify-between text-[10px] font-mono text-[#786B62]">
                    <span>BIS TEXTILE STANDARD CATALOGUE</span>
                    <span className="font-bold text-[#2B221E]">
                      Trang {product.activePdfPage}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* RIGHT 5 COLS: EXTRACTED SPECIFICATIONS & PAGE CITATION PANEL */}
          <div className="lg:col-span-5 p-5 bg-[#FAF6F0] flex flex-col justify-between space-y-5">
            <div className="space-y-4">
              {/* Right Column Title */}
              <div className="flex items-center justify-between border-b border-[#E2D8CC] pb-3">
                <div className="flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-[#2B221E] text-[#38BDF8] flex items-center justify-center text-xs font-bold">
                    AI
                  </span>
                  <h2 className="text-base font-extrabold text-[#1E1916]">
                    Trích xuất thông số
                  </h2>
                </div>
                <span className="text-[11px] font-mono text-[#786B62]">
                  Tự động trích dẫn theo trang
                </span>
              </div>

              {/* SKU, Name VI, Name EN Fields */}
              <div className="space-y-2.5">
                <div>
                  <label className="block text-xs font-bold text-[#4A3B34] mb-1">
                    SKU <span className="text-[#D9382C]">*</span>
                  </label>
                  <input
                    type="text"
                    readOnly
                    value={product.sku}
                    aria-label="Mã SKU trích xuất"
                    className="w-full px-3 py-1.5 rounded-lg bg-[#FADCD9] border border-[#E6A8A1] text-[#B91C1C] font-mono font-extrabold text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-[#4A3B34] mb-1">
                    Tên sản phẩm (VI)
                  </label>
                  <input
                    type="text"
                    value={nameViInput}
                    onChange={(e) => setNameViInput(e.target.value)}
                    aria-label="Tên sản phẩm tiếng Việt"
                    className="w-full px-3 py-1.5 rounded-lg bg-white border border-[#D5C8B8] text-[#1E1916] font-semibold text-xs sm:text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-[#4A3B34] mb-1">
                    Tên sản phẩm (EN)
                  </label>
                  <input
                    type="text"
                    value={nameEnInput}
                    onChange={(e) => setNameEnInput(e.target.value)}
                    aria-label="Tên sản phẩm tiếng Anh"
                    className="w-full px-3 py-1.5 rounded-lg bg-white border border-[#D5C8B8] text-[#1E1916] font-semibold text-xs sm:text-sm"
                  />
                </div>
              </div>

              {/* Technical Specifications Table */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-xs font-extrabold text-[#1E1916] uppercase tracking-wider">
                    Thông số kỹ thuật
                  </h3>
                  <span className="text-[11px] text-[#6E5D53]">
                    Bấm vào dòng để xem vị trí trích dẫn
                  </span>
                </div>

                <div className="bg-white rounded-xl border border-[#D8CEC2] divide-y divide-[#EAE2D6] overflow-hidden">
                  {product.specs.map((spec) => {
                    const isSelected = spec.id === activeSpec?.id;
                    const isApproved = spec.status === 'approved';
                    return (
                      <div
                        key={spec.id}
                        onClick={() => setSelectedSpecId(spec.id)}
                        className={`p-2.5 flex items-center justify-between gap-2 cursor-pointer transition-colors ${
                          isSelected ? 'bg-[#FFF5F3]' : 'hover:bg-[#FAF6F0]'
                        }`}
                      >
                        <div className="min-w-0 flex-1">
                          <div className="text-xs font-semibold text-[#3B302B]">
                            {spec.labelVi}
                          </div>
                          <div className="text-[10px] font-mono text-[#8C7B70]">
                            {spec.labelEn} · Trang {spec.pdfPage}
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <input
                            type="text"
                            value={specValues[spec.id] ?? spec.value}
                            onChange={(e) =>
                              setSpecValues((prev) => ({
                                ...prev,
                                [spec.id]: e.target.value,
                              }))
                            }
                            aria-label={`Giá trị ${spec.labelVi}`}
                            className="w-36 sm:w-44 px-2 py-1 rounded bg-[#F6F1EA] border border-[#D5C8B8] text-xs font-mono font-bold text-[#1E1916] text-right"
                          />

                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              const nextStatus: VerificationStatus =
                                spec.status === 'approved' ? 'review' : 'approved';
                              onUpdateSpecStatus(
                                product.sku,
                                spec.id,
                                nextStatus,
                                specValues[spec.id]
                              );
                            }}
                            title={
                              isApproved
                                ? 'Đã xác minh chứng cứ trang PDF'
                                : 'Chưa xác minh — Bấm để xác nhận'
                            }
                            className={`px-2 py-1 rounded text-[10px] font-mono font-bold border transition-colors ${
                              isApproved
                                ? 'bg-[#DCFCE7] text-[#15803D] border-[#86EFAC]'
                                : 'bg-[#FEF3C7] text-[#B45309] border-[#FDE68A]'
                            }`}
                          >
                            {isApproved ? '✔ Đã duyệt' : 'Chờ duyệt'}
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Citation Box (Trích dẫn Citation) */}
              <div className="p-3.5 rounded-xl bg-[#EFE8DE] border border-[#D5C8B8] space-y-1.5">
                <div className="text-xs font-extrabold text-[#1E1916] flex items-center gap-1.5">
                  <BookOpen className="w-3.5 h-3.5 text-[#D9382C]" />
                  <span>Trích dẫn (Citation)</span>
                </div>
                <div className="text-xs text-[#3B302B] flex items-center gap-2">
                  <FileText className="w-3.5 h-3.5 text-[#6E5D53] shrink-0" />
                  <span>
                    Nguồn: <strong className="font-mono">{product.catalogueFile}</strong>
                  </span>
                </div>
                <div className="text-xs text-[#3B302B] flex items-center gap-2">
                  <span className="w-3.5 h-3.5 inline-flex items-center justify-center font-mono font-bold text-[10px] bg-[#D9382C] text-white rounded-xs">
                    P
                  </span>
                  <span>
                    Trang: <strong>{activeSpec?.pdfPage ?? product.activePdfPage}</strong>
                  </span>
                </div>
                {activeSpec && (
                  <div className="pt-1.5 mt-1.5 border-t border-[#D8CEC2] text-[11px] font-mono text-[#574B43] leading-relaxed">
                    {activeSpec.evidenceQuote}
                  </div>
                )}
              </div>
            </div>

            {/* Bottom Action Bar: Làm mới & Lưu thông số */}
            <div className="pt-3 border-t border-[#E2D8CC] flex items-center justify-between gap-3">
              <button
                type="button"
                onClick={handleResetSpecs}
                className="px-4 py-2 rounded-xl bg-white hover:bg-[#EFE8DE] text-[#3B302B] border border-[#C9BBAE] text-xs font-bold inline-flex items-center gap-1.5 transition-colors"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Làm mới</span>
              </button>

              <button
                type="button"
                onClick={handleSaveAllSpecs}
                className="flex-1 py-2.5 px-5 rounded-xl bg-[#D9382C] hover:bg-[#B82D22] text-white text-xs sm:text-sm font-bold shadow-md inline-flex items-center justify-center gap-2 transition-colors"
              >
                <Save className="w-4 h-4" />
                <span>Lưu thông số</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
