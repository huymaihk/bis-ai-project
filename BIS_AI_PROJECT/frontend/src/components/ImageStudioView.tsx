import React, { useState } from 'react';
import {
  BisBackgroundId,
  CandidateImage,
  ProcessedImageRender,
  ProductRecord,
} from '../types/bisTypes';
import { toggleCompareCandidateSelection } from '../utils/workflowRules';
import { ProductVisualCanvas } from './ProductVisualCanvas';
import { AgentRobotAvatar } from './AgentRobotAvatar';
import {
  Crop,
  RotateCw,
  Sliders,
  Layers,
  MessageSquarePlus,
  ZoomIn,
  ZoomOut,
  CheckCircle2,
  Clock,
  Sparkles,
  Upload,
  Columns,
  ArrowRight,
  ExternalLink,
  Maximize2,
} from 'lucide-react';

interface ImageStudioViewProps {
  product: ProductRecord;
  reduceMotion: boolean;
  onSelectSourceImage: (sku: string, candidateId: string) => void;
  onSaveProcessedRender: (sku: string, render: ProcessedImageRender) => void;
  onApproveRenderVersion: (sku: string, reviewerNote: string) => void;
  onRequestReworkRender: (sku: string) => void;
  onAddUploadedCandidate: (sku: string, newCandidate: CandidateImage) => void;
  onProceedToOperations: () => void;
}

export const ImageStudioView: React.FC<ImageStudioViewProps> = ({
  product,
  reduceMotion,
  onSelectSourceImage,
  onSaveProcessedRender,
  onApproveRenderVersion,
  onRequestReworkRender,
  onAddUploadedCandidate,
  onProceedToOperations,
}) => {
  const [studioLayout, setStudioLayout] = useState<'storyboard_3col' | 'aatcc_3d_concept' | 'compare_multi'>('storyboard_3col');
  const [backgroundId, setBackgroundId] = useState<BisBackgroundId>(
    product.activeProcessedRender?.backgroundId || 'bis-warm-ivory'
  );
  const [paddingPercent, setPaddingPercent] = useState<number>(
    product.activeProcessedRender?.paddingPercent || 10
  );
  const [shadowIntensity, setShadowIntensity] = useState<number>(
    product.activeProcessedRender?.shadowIntensity || 18
  );
  const [contrastBoost, setContrastBoost] = useState<boolean>(
    product.activeProcessedRender?.contrastBoost || false
  );
  const [showGrid1254, setShowGrid1254] = useState<boolean>(true);
  const [zoomPercent, setZoomPercent] = useState<number>(100);
  const [aspectRatioMode, setAspectRatioMode] = useState<'1254×1254 (1:1)' | '4:3'>('1254×1254 (1:1)');
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [activeTool, setActiveTool] = useState<'crop' | 'rotate' | 'adjust' | 'bg' | 'note'>('bg');

  const selectedCandidate = product.candidateImages.find(
    (c) => c.id === product.selectedSourceImageId
  );

  const isRenderApproved =
    product.activeProcessedRender?.status === 'approved';

  const handleChooseCandidate = (cand: CandidateImage) => {
    onSelectSourceImage(product.sku, cand.id);
    // Automatically prepare a preview render in 'review' state (never auto-approved!)
    const nextRender: ProcessedImageRender = {
      renderId: `RND-${product.sku}-${Date.now().toString().slice(-3)}`,
      sourceImageId: cand.id,
      backgroundId,
      paddingPercent,
      shadowIntensity,
      contrastBoost,
      dimensions: '1254 × 1254 px',
      createdAt: 'Vừa tạo bản thử',
      status: 'review',
    };
    onSaveProcessedRender(product.sku, nextRender);
  };

  const handleApproveCurrentImage = () => {
    // If user hasn't picked a candidate yet, pick the first PDF candidate and create + approve
    if (!selectedCandidate && product.candidateImages.length > 0) {
      const firstCand = product.candidateImages[0];
      onSelectSourceImage(product.sku, firstCand.id);
      const approvedRender: ProcessedImageRender = {
        renderId: `RND-${product.sku}-${Date.now().toString().slice(-3)}`,
        sourceImageId: firstCand.id,
        backgroundId,
        paddingPercent,
        shadowIntensity,
        contrastBoost,
        dimensions: '1254 × 1254 px',
        createdAt: 'Vừa duyệt xong',
        status: 'approved',
        approvedBy: 'Nguyễn Minh Anh · BIS Textile',
        approvedAt: 'Hôm nay, 15:02',
        reviewerNote: 'Đạt chuẩn 4/4 tiêu chí Benchmark BIS (1254 × 1254 px).',
      };
      onSaveProcessedRender(product.sku, approvedRender);
      return;
    }

    onApproveRenderVersion(
      product.sku,
      'Đạt chuẩn 4/4 tiêu chí Benchmark BIS (Đủ thiết bị, rõ kẹp mẫu, nền Lab, ánh sáng đồng nhất).'
    );
  };

  const handleSimulateUpload = () => {
    const newCand: CandidateImage = {
      id: `cand-upload-${Date.now().toString().slice(-4)}`,
      sku: product.sku,
      sourceType: 'upload',
      label: `Ảnh tải lên từ Studio BIS (${product.sku}_RAW.jpg)`,
      originalDimensions: '1600 × 1600 px',
      aspectRatioNote: 'Tỷ lệ 1:1 gốc phòng chụp BIS',
      sharpnessScore: 'Rất nét (97/100)',
      lightingNote: 'Ánh sáng phòng Lab tiêu chuẩn',
      visualVariant: 'upload-raw',
    };
    onAddUploadedCandidate(product.sku, newCand);
    handleChooseCandidate(newCand);
  };

  const benchmarkChecks = [
    'Đủ toàn bộ thiết bị',
    'Rõ chi tiết kẹp mẫu',
    'Nền phòng thí nghiệm',
    'Ánh sáng đồng nhất',
  ];

  return (
    <div className="p-3 lg:p-5 max-w-[1520px] mx-auto space-y-4">
      {/* Top Department Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 card-8d-dark border border-[#4E3E36] rounded-2xl px-5 py-3">
        <div className="flex items-center gap-3">
          <AgentRobotAvatar
            department="imagestudio"
            size="sm"
            isActive={true}
            reduceMotion={reduceMotion}
          />
          <div>
            <h1 className="text-base lg:text-lg font-bold text-[#FAF6F0]">
              Image Studio
            </h1>
            <p className="text-xs text-[#C4B5AA]">
              Xử lý hình ảnh sản phẩm & chọn ảnh chuẩn · Nguồn PDF, ảnh đề xuất, vùng xử lý lớn 1254×1254 và cột chuẩn tham chiếu
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div
            role="group"
            aria-label="Chế độ hiển thị Image Studio"
            className="inline-flex rounded-xl card-8d-dark-recessed p-1 border border-[#3E322C] text-xs"
          >
            <button
              type="button"
              onClick={() => setStudioLayout('storyboard_3col')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                studioLayout === 'storyboard_3col'
                  ? 'btn-8d-crimson text-white'
                  : 'text-[#B8AAA0] hover:text-white'
              }`}
            >
              Bàn dựng 3 Cột (Storyboard)
            </button>
            <button
              type="button"
              onClick={() => setStudioLayout('aatcc_3d_concept')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
                studioLayout === 'aatcc_3d_concept'
                  ? 'btn-8d-crimson text-white'
                  : 'text-[#B8AAA0] hover:text-white'
              }`}
            >
              Phối cảnh Studio 3D (AATCC)
            </button>
            <button
              type="button"
              onClick={() => setStudioLayout('compare_multi')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all inline-flex items-center gap-1 ${
                studioLayout === 'compare_multi'
                  ? 'btn-8d-crimson text-white'
                  : 'text-[#B8AAA0] hover:text-white'
              }`}
            >
              <Columns className="w-3.5 h-3.5" />
              <span>So sánh Nhiều ảnh ({compareIds.length}/3)</span>
            </button>
          </div>

          <button
            type="button"
            onClick={onProceedToOperations}
            className="px-3.5 py-1.5 rounded-lg btn-8d-crimson text-white text-xs font-semibold inline-flex items-center gap-1.5 transition-all"
          >
            <span>Sang bước Duyệt (Operations)</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {studioLayout === 'storyboard_3col' ? (
        /* STORYBOARD 3-COLUMN BENCHMARK EDITOR (Matches Image 3 Top-Right Panel) */
        <div className="card-8d-ivory text-[#1F1916] border border-[#D8CEC2] rounded-2xl overflow-hidden">
          {/* Sub-Header Bar inside Ivory Card */}
          <div className="px-5 py-2.5 surface-8d-warm border-b border-[#D8CEC2] flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2 text-xs sm:text-sm">
              <span className="font-bold text-[#574B43]">SKU:</span>
              <span className="font-mono font-extrabold text-[#1E1916]">
                {product.sku}
              </span>
              <span className="text-[#8C7B70]">|</span>
              <span className="font-semibold text-[#2B221E]">
                {product.nameVi} / {product.nameEn}
              </span>
            </div>

            <div className="flex items-center gap-2 text-xs">
              <span className="font-mono text-[#6E5D53]">
                Khung thành phẩm chuẩn: <strong>1254 × 1254 px</strong>
              </span>
              <button
                type="button"
                onClick={handleSimulateUpload}
                className="px-2.5 py-1 rounded-lg card-8d-interactive text-[#2B221E] border border-[#C9BBAE] font-semibold inline-flex items-center gap-1"
              >
                <Upload className="w-3.5 h-3.5 text-[#D9382C]" />
                <span>Tải ảnh lên</span>
              </button>
            </div>
          </div>

          {/* 3-COLUMN GRID: LEFT (PDF SOURCE & CANDIDATES) | CENTER (LARGE EDITOR) | RIGHT (BENCHMARK & APPROVAL) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-[#D8CEC2]">
            {/* COLUMN 1 (LEFT 3 COLS): Nguồn tài liệu (PDF) & Ảnh đề xuất */}
            <div className="lg:col-span-3 p-4 space-y-4 bg-[#FAF6F0]">
              {/* Top Card: Nguồn tài liệu (PDF) */}
              <div className="card-8d-light rounded-xl border border-[#DED4C8] p-3 space-y-2">
                <div className="text-xs font-extrabold text-[#1E1916]">
                  Nguồn tài liệu (PDF)
                </div>
                <div className="h-36 rounded-lg border border-[#E5DEC9] overflow-hidden bg-[#F8F5F0]">
                  <ProductVisualCanvas
                    sku={product.sku}
                    variant="pdf-scan-front"
                    backgroundId="bis-warm-ivory"
                    paddingPercent={10}
                    className="w-full h-full"
                  />
                </div>
                <div className="text-center">
                  <div className="text-xs font-bold text-[#1E1916]">
                    Trang {product.activePdfPage} ({product.sku})
                  </div>
                  <div className="text-[11px] font-mono text-[#6E5D53] truncate">
                    {product.catalogueFile}
                  </div>
                </div>
              </div>

              {/* Bottom Card: Ảnh đề xuất (Candidates) */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-extrabold text-[#1E1916]">
                    Ảnh đề xuất ({product.candidateImages.length} lựa chọn)
                  </div>
                  <span className="text-[10px] font-mono text-[#6E5D53]">
                    Chưa tự chọn
                  </span>
                </div>

                <div className="space-y-2 max-h-[330px] overflow-y-auto pr-1">
                  {product.candidateImages.map((cand, index) => {
                    const isSelected = product.selectedSourceImageId === cand.id;
                    const isCompared = compareIds.includes(cand.id);
                    return (
                      <div
                        key={cand.id}
                        onClick={() => handleChooseCandidate(cand)}
                        className={`p-2.5 rounded-xl border-2 cursor-pointer transition-all flex items-center gap-2.5 ${
                          isSelected
                            ? 'bg-[#FFF5F3] border-[#D9382C] shadow-xs'
                            : 'bg-white border-[#DED4C8] hover:border-[#B8AAA0]'
                        }`}
                      >
                        {/* Radio Indicator */}
                        <div
                          className={`w-4 h-4 rounded-full border-2 flex items-center justify-center shrink-0 ${
                            isSelected ? 'border-[#D9382C]' : 'border-[#8C7B70]'
                          }`}
                        >
                          {isSelected && (
                            <div className="w-2 h-2 rounded-full bg-[#D9382C]" />
                          )}
                        </div>

                        {/* Candidate Mini Thumbnail */}
                        <div className="w-12 h-12 rounded-lg border border-[#E5DEC9] overflow-hidden shrink-0 bg-[#F8F5F0]">
                          <ProductVisualCanvas
                            sku={product.sku}
                            variant={cand.visualVariant}
                            backgroundId="bis-pure-white"
                            paddingPercent={10}
                            className="w-full h-full"
                          />
                        </div>

                        {/* Candidate Meta */}
                        <div className="min-w-0 flex-1">
                          <div className="text-xs font-bold text-[#1E1916] truncate">
                            Ảnh {index + 1} –{' '}
                            {cand.pdfPage ? `Trang ${cand.pdfPage}` : 'Studio/Web'}
                          </div>
                          <div className="text-[11px] text-[#6E5D53] truncate">
                            (Nguồn:{' '}
                            {cand.sourceType === 'pdf'
                              ? `PDF Tr.${cand.pdfPage}`
                              : cand.sourceType === 'web'
                              ? cand.webDomain || 'Web'
                              : 'Tải lên'}
                            )
                          </div>
                          {cand.webUrl && (
                            <div className="text-[10px] font-mono text-[#0284C7] truncate flex items-center gap-0.5">
                              <ExternalLink className="w-2.5 h-2.5 shrink-0" />
                              <span className="truncate">{cand.webUrl}</span>
                            </div>
                          )}
                        </div>

                        {/* Compare Checkbox */}
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setCompareIds(
                              (prev) =>
                                toggleCompareCandidateSelection(prev, cand.id)
                                  .nextIds
                            );
                          }}
                          title="Chọn để so sánh nhiều ảnh"
                          className={`px-1.5 py-0.5 rounded text-[10px] font-mono border ${
                            isCompared
                              ? 'bg-[#D9382C] text-white border-[#D9382C]'
                              : 'bg-[#F6F1EA] text-[#574B43] border-[#D5C8B8]'
                          }`}
                        >
                          So sánh
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* COLUMN 2 (CENTER 6 COLS): Chỉnh sửa ảnh sản phẩm (Large Processing Canvas) */}
            <div className="lg:col-span-6 p-4 flex flex-col justify-between bg-[#F4EFE6]">
              <div>
                <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                  <h2 className="text-sm font-extrabold text-[#1E1916]">
                    Chỉnh sửa ảnh sản phẩm
                  </h2>
                  <span className="text-xs font-mono text-[#6E5D53]">
                    {selectedCandidate
                      ? `Đang nạp: ${selectedCandidate.label}`
                      : 'Đang hiển thị bản xem trước — Hãy chọn 1 ảnh nguồn ở cột trái'}
                  </span>
                </div>

                {/* Top Editing Tool Strip (Cắt, Xoay, Điều chỉnh, Nền, Chú thích) */}
                <div className="grid grid-cols-5 gap-1.5 bg-white p-1.5 rounded-xl border border-[#DED4C8] mb-3">
                  {[
                    { id: 'crop', label: 'Cắt', Icon: Crop },
                    { id: 'rotate', label: 'Xoay', Icon: RotateCw },
                    { id: 'adjust', label: 'Điều chỉnh', Icon: Sliders },
                    { id: 'bg', label: 'Nền BIS', Icon: Layers },
                    { id: 'note', label: 'Chú thích', Icon: MessageSquarePlus },
                  ].map((tool) => {
                    const ToolIcon = tool.Icon;
                    const isAct = activeTool === tool.id;
                    return (
                      <button
                        key={tool.id}
                        type="button"
                        onClick={() => setActiveTool(tool.id as typeof activeTool)}
                        className={`py-1.5 px-2 rounded-lg text-xs font-semibold flex flex-col sm:flex-row items-center justify-center gap-1.5 transition-colors ${
                          isAct
                            ? 'bg-[#2B221E] text-white'
                            : 'text-[#4A3B34] hover:bg-[#F6F1EA]'
                        }`}
                      >
                        <ToolIcon className="w-3.5 h-3.5" />
                        <span>{tool.label}</span>
                      </button>
                    );
                  })}
                </div>

                {/* Sub-Controls for Background & Safe Margin */}
                <div className="mb-3 px-3 py-2 rounded-xl bg-white/80 border border-[#DED4C8] flex flex-wrap items-center justify-between gap-2 text-xs">
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-[#4A3B34]">Nền chuẩn BIS:</span>
                    {[
                      { id: 'bis-warm-ivory', label: 'Phòng Lab Ấm' },
                      { id: 'bis-pure-white', label: 'Trắng Tinh' },
                      { id: 'bis-lab-neutral', label: 'Xám Trung tính' },
                      { id: 'bis-transparent', label: 'Tách nền PNG' },
                    ].map((bg) => (
                      <button
                        key={bg.id}
                        type="button"
                        onClick={() => setBackgroundId(bg.id as BisBackgroundId)}
                        className={`px-2 py-1 rounded text-[11px] font-semibold border ${
                          backgroundId === bg.id
                            ? 'bg-[#D9382C] text-white border-[#D9382C]'
                            : 'bg-[#F6F1EA] text-[#4A3B34] border-[#D5C8B8]'
                        }`}
                      >
                        {bg.label}
                      </button>
                    ))}
                  </div>

                  <label className="inline-flex items-center gap-1.5 cursor-pointer font-medium text-[#4A3B34]">
                    <input
                      type="checkbox"
                      checked={showGrid1254}
                      onChange={(e) => setShowGrid1254(e.target.checked)}
                      className="rounded text-[#D9382C]"
                    />
                    <span>Khung 1254×1254</span>
                  </label>
                </div>

                {/* Large Square 1254×1254 Studio Canvas */}
                <div className="relative mx-auto w-full max-w-[440px] aspect-square rounded-2xl border-2 border-[#C9BBAE] shadow-inner overflow-hidden bg-white">
                  <ProductVisualCanvas
                    sku={product.sku}
                    variant={selectedCandidate?.visualVariant || 'bis-reference'}
                    backgroundId={backgroundId}
                    paddingPercent={paddingPercent}
                    shadowIntensity={shadowIntensity}
                    contrastBoost={contrastBoost}
                    showGrid1254={showGrid1254}
                    zoomScale={zoomPercent / 100}
                    className="w-full h-full"
                  />
                </div>
              </div>

              {/* Bottom Zoom & Aspect Ratio Toolbar matching Storyboard */}
              <div className="mt-4 pt-3 border-t border-[#DED4C8] flex flex-wrap items-center justify-between gap-2 text-xs">
                <div className="inline-flex items-center gap-1 bg-white px-2.5 py-1 rounded-lg border border-[#C9BBAE] font-mono">
                  <button
                    type="button"
                    onClick={() => setZoomPercent((z) => Math.max(80, z - 10))}
                    aria-label="Thu nhỏ ảnh"
                    className="p-0.5 hover:text-[#D9382C]"
                  >
                    <ZoomOut className="w-3.5 h-3.5" />
                  </button>
                  <span className="px-2 font-bold">{zoomPercent}%</span>
                  <button
                    type="button"
                    onClick={() => setZoomPercent((z) => Math.min(140, z + 10))}
                    aria-label="Phóng to ảnh"
                    className="p-0.5 hover:text-[#D9382C]"
                  >
                    <ZoomIn className="w-3.5 h-3.5" />
                  </button>
                </div>

                <div className="flex items-center gap-2">
                  <label htmlFor="ratio-select" className="font-semibold text-[#4A3B34]">
                    Tỷ lệ:
                  </label>
                  <select
                    id="ratio-select"
                    value={aspectRatioMode}
                    onChange={(e) =>
                      setAspectRatioMode(e.target.value as typeof aspectRatioMode)
                    }
                    className="bg-white border border-[#C9BBAE] rounded-lg px-2.5 py-1 text-xs font-mono font-bold text-[#1E1916]"
                  >
                    <option value="1254×1254 (1:1)">1254×1254 (1:1)</option>
                    <option value="4:3">4:3 (Catalogue)</option>
                  </select>
                </div>
              </div>
            </div>

            {/* COLUMN 3 (RIGHT 3 COLS): Chuẩn tham chiếu (Benchmark) & Trạng thái ảnh */}
            <div className="lg:col-span-3 p-4 flex flex-col justify-between bg-[#FAF6F0] space-y-4">
              <div className="space-y-4">
                {/* Benchmark Card */}
                <div className="card-8d-light rounded-xl border border-[#DED4C8] p-3.5 space-y-3">
                  <h2 className="text-xs font-extrabold text-[#1E1916]">
                    Chuẩn tham chiếu (Benchmark)
                  </h2>

                  <div className="h-40 rounded-lg border border-[#E5DEC9] overflow-hidden bg-[#F8F5F0]">
                    <ProductVisualCanvas
                      sku={product.sku}
                      variant="bis-reference"
                      backgroundId="bis-warm-ivory"
                      paddingPercent={8}
                      className="w-full h-full"
                    />
                  </div>

                  {/* 4 Benchmark Criteria Checkmarks */}
                  <div className="space-y-2 pt-1">
                    {benchmarkChecks.map((criterion, idx) => (
                      <div
                        key={idx}
                        className="flex items-center gap-2 text-xs font-semibold text-[#2B221E]"
                      >
                        <CheckCircle2 className="w-4 h-4 text-[#16A34A] shrink-0" />
                        <span>{criterion}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Image Approval Status Box (Human-in-the-loop) */}
                <div className="card-8d-light rounded-xl border border-[#DED4C8] p-3.5 space-y-2">
                  <div className="text-xs font-extrabold text-[#1E1916]">
                    Trạng thái ảnh
                  </div>

                  {isRenderApproved ? (
                    <div className="p-2.5 rounded-lg bg-[#DCFCE7] border border-[#86EFAC] text-[#15803D] flex items-center gap-2 text-xs font-bold">
                      <CheckCircle2 className="w-4 h-4 text-[#16A34A] shrink-0" />
                      <div>
                        <div>Đạt chuẩn (Đã phê duyệt)</div>
                        <div className="text-[10px] font-normal text-[#166534]">
                          Khung 1254 × 1254 px · Duyệt bởi Minh Anh
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="p-2.5 rounded-lg bg-[#FEF3C7] border border-[#FDE68A] text-[#B45309] flex items-center gap-2 text-xs font-bold">
                      <Clock className="w-4 h-4 text-[#D97706] shrink-0" />
                      <div>
                        <div>Chờ người duyệt</div>
                        <div className="text-[10px] font-normal text-[#92400E]">
                          AI không tự động báo đạt chuẩn khi chưa bấm phê duyệt
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Bottom Approval CTA Buttons */}
              <div className="space-y-2 pt-2 border-t border-[#E2D8CC]">
                <button
                  type="button"
                  onClick={handleApproveCurrentImage}
                  className="w-full py-2.5 px-4 rounded-xl btn-8d-crimson text-white text-xs sm:text-sm font-bold transition-all"
                >
                  Phê duyệt ảnh
                </button>

                <button
                  type="button"
                  onClick={() => {
                    onRequestReworkRender(product.sku);
                    const nextIdx =
                      (product.candidateImages.findIndex(
                        (c) => c.id === product.selectedSourceImageId
                      ) +
                        1) %
                      product.candidateImages.length;
                    if (product.candidateImages[nextIdx]) {
                      handleChooseCandidate(product.candidateImages[nextIdx]);
                    }
                  }}
                  className="w-full py-2 px-4 rounded-xl card-8d-interactive text-[#3B302B] border border-[#C9BBAE] text-xs font-bold"
                >
                  Chọn ảnh khác
                </button>
              </div>
            </div>
          </div>
        </div>
      ) : studioLayout === 'aatcc_3d_concept' ? (
        /* 3D STUDIO SHOWCASE CONCEPT (Matches Image 2 `/assets/aistudio/image_c51dbc18.png`) */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
          <div className="lg:col-span-9 rounded-2xl overflow-hidden border border-[#433630] bg-[#1A1412] shadow-2xl flex flex-col justify-between">
            <div className="relative w-full aspect-[16/11] min-h-[440px] overflow-hidden select-none">
              <img
                src="/assets/aistudio/image_c51dbc18.png"
                alt="Phối cảnh 3D Image Studio BIS TEXTILE AI"
                className="absolute max-w-none pointer-events-none"
                style={{
                  left: '-22.5%',
                  top: '-10.5%',
                  width: '162%',
                  height: '130%',
                }}
              />
            </div>
            <div className="relative z-10 w-full flex flex-wrap items-center justify-between gap-3 bg-[#161210] border-t border-[#433630] p-3">
              <div className="text-xs text-[#FAF6F0]">
                <span className="font-bold text-[#E03B2F]">PHỐI CẢNH STUDIO 3D BIS:</span>{' '}
                Mô phỏng buồng chụp thiết bị kiểm tra dệt may chuẩn AATCC / ISO ({product.sku})
              </div>
              <button
                type="button"
                onClick={() => setStudioLayout('storyboard_3col')}
                className="px-3 py-1.5 rounded-lg bg-[#D9382C] hover:bg-[#B82D22] text-white text-xs font-bold transition-colors"
              >
                Mở Bàn dựng 3 Cột để Chỉnh sửa & Phê duyệt
              </button>
            </div>
          </div>

          <div className="lg:col-span-3 flex flex-col gap-3">
            <div className="bg-[#231D1A] border border-[#3E322C] rounded-2xl p-4 space-y-2.5">
              <div className="text-xs font-bold text-[#FAF6F0]">
                📄 PDF – Trang {product.activePdfPage}
              </div>
              <div className="bg-[#F6F1EA] rounded-xl p-3 text-[#1E1916]">
                <div className="text-[11px] font-bold">AATCC / ISO Test Method</div>
                <div className="h-28 my-1">
                  <ProductVisualCanvas
                    sku={product.sku}
                    variant="pdf-scan-front"
                    className="w-full h-full rounded"
                  />
                </div>
                <div className="text-right text-[10px] font-mono font-bold">
                  {product.activePdfPage} / {product.catalogueTotalPages}
                </div>
              </div>
            </div>

            <div className="bg-[#231D1A] border border-[#3E322C] rounded-2xl p-4 space-y-2">
              <div className="text-xs font-bold text-[#FAF6F0]">
                Nguồn ảnh & Trạng thái duyệt
              </div>
              <div className="p-2.5 rounded-lg bg-[#2E2622] text-xs text-[#E5D9CE]">
                Nguồn: Chụp studio BIS & PDF Trang {product.activePdfPage}
              </div>
              <div className="p-2.5 rounded-lg bg-[#2E2622] text-xs font-bold text-[#FBBF24]">
                {isRenderApproved ? '✔ Đã duyệt đạt chuẩn' : '🕒 Chờ duyệt'}
              </div>
              <button
                type="button"
                onClick={handleApproveCurrentImage}
                className="w-full py-2 rounded-xl bg-[#D9382C] hover:bg-[#B82D22] text-white text-xs font-bold"
              >
                Phê duyệt ảnh ngay
              </button>
            </div>
          </div>
        </div>
      ) : (
        /* MULTI-IMAGE SIDE-BY-SIDE COMPARISON MODE */
        <div className="bg-[#F6F1EA] text-[#1F1916] border border-[#D8CEC2] rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-[#D8CEC2] pb-3">
            <div>
              <h2 className="text-base font-extrabold text-[#1E1916]">
                So sánh Nhiều Ảnh Ứng viên ({compareIds.length}/3 ảnh đã chọn)
              </h2>
              <p className="text-xs text-[#574B43]">
                Đối chiếu độ nét, góc chụp và chi tiết ngàm kẹp trước khi chọn làm ảnh nguồn chuẩn 1254 × 1254.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setStudioLayout('storyboard_3col')}
              className="px-3 py-1.5 rounded-lg bg-[#2B221E] text-white text-xs font-bold"
            >
              Quay lại Bàn dựng 3 Cột
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {(compareIds.length > 0
              ? product.candidateImages.filter((c) => compareIds.includes(c.id))
              : product.candidateImages.slice(0, 3)
            ).map((cand) => (
              <div
                key={cand.id}
                className="bg-white rounded-xl border border-[#DED4C8] p-3.5 space-y-2.5"
              >
                <div className="h-56 rounded-lg border border-[#E5DEC9] overflow-hidden">
                  <ProductVisualCanvas
                    sku={product.sku}
                    variant={cand.visualVariant}
                    backgroundId="bis-warm-ivory"
                    className="w-full h-full"
                  />
                </div>
                <div className="text-xs font-bold text-[#1E1916]">{cand.label}</div>
                <div className="text-[11px] text-[#574B43]">
                  Kích thước gốc: {cand.originalDimensions} · {cand.sharpnessScore}
                </div>
                <button
                  type="button"
                  onClick={() => {
                    handleChooseCandidate(cand);
                    setStudioLayout('storyboard_3col');
                  }}
                  className="w-full py-2 rounded-lg bg-[#D9382C] text-white text-xs font-bold"
                >
                  Chọn làm ảnh xử lý chính
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
