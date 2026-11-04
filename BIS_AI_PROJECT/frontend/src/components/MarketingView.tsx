import React, { useState, useEffect } from 'react';
import {
  MarketingSection,
  ProductRecord,
  SeoMetadata,
} from '../types/bisTypes';
import { ProductVisualCanvas } from './ProductVisualCanvas';
import { AgentRobotAvatar } from './AgentRobotAvatar';
import {
  CheckCircle2,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  Save,
  Check,
  ArrowRight,
  Bold,
  Italic,
  Underline,
  List,
  ListOrdered,
  Link2,
} from 'lucide-react';

interface MarketingViewProps {
  product: ProductRecord;
  reduceMotion: boolean;
  onSaveMarketingAndSeo: (
    sku: string,
    sections: MarketingSection[],
    seo: SeoMetadata,
    versionNote: string
  ) => void;
  onProceedToImageStudio: () => void;
}

export const MarketingView: React.FC<MarketingViewProps> = ({
  product,
  reduceMotion,
  onSaveMarketingAndSeo,
  onProceedToImageStudio,
}) => {
  const [subTab, setSubTab] = useState<'content' | 'seo_7part'>('content');
  const [editorLang, setEditorLang] = useState<'vi' | 'en'>('vi');
  const [previewLang, setPreviewLang] = useState<'vi' | 'en'>('vi');
  const [previewSlideIndex, setPreviewSlideIndex] = useState<number>(0);

  // Bilingual Title & Short Description
  const [titleVi, setTitleVi] = useState<string>(product.seo.titleVi);
  const [titleEn, setTitleEn] = useState<string>(product.seo.titleEn);
  const [shortDescVi, setShortDescVi] = useState<string>(
    'Thiết bị kiểm tra độ bền kéo, độ giãn dài và độ đứt của vải theo các tiêu chuẩn quốc tế (ISO 13934-1, ASTM D5034).'
  );
  const [shortDescEn, setShortDescEn] = useState<string>(
    product.seo.descEn
  );
  const [keyFeaturesText, setKeyFeaturesText] = useState<string>(
    product.marketingSections[2]?.content ||
      '• Dải tải: 0.5 – 50 kN, độ chính xác ±0.5%\n• Tốc độ kéo: 0.1 – 500 mm/min\n• Hành trình: 1,200 mm\n• Đáp ứng ISO 13934-1, ASTM D5034'
  );
  const [seoDescVi, setSeoDescVi] = useState<string>(product.seo.descVi);
  const [sections, setSections] = useState<MarketingSection[]>(
    product.marketingSections
  );
  const [savedToast, setSavedToast] = useState<string | null>(null);

  useEffect(() => {
    setTitleVi(product.seo.titleVi);
    setTitleEn(product.seo.titleEn);
    setShortDescEn(product.seo.descEn);
    setSeoDescVi(product.seo.descVi);
    setSections(product.marketingSections);
    setKeyFeaturesText(
      product.marketingSections[2]?.content ||
        '• Dải tải: 0.5 – 50 kN, độ chính xác ±0.5%\n• Tốc độ kéo: 0.1 – 500 mm/min\n• Hành trình: 1,200 mm\n• Đáp ứng ISO 13934-1, ASTM D5034'
    );
    setSavedToast(null);
  }, [product.sku, product.seo, product.marketingSections]);

  const seoLen = seoDescVi.length;
  const isSeoOptimal = seoLen >= 130 && seoLen <= 165;

  const previewSlides: {
    label: string;
    variant: 'bis-reference' | 'pdf-scan-front' | 'pdf-scan-detail' | 'web-angle';
  }[] = [
    { label: 'Toàn cảnh thiết bị', variant: 'bis-reference' },
    { label: 'Ảnh trang PDF gốc', variant: 'pdf-scan-front' },
    { label: 'Cụm ngàm kẹp mẫu', variant: 'pdf-scan-detail' },
    { label: 'Màn hình điều khiển', variant: 'web-angle' },
  ];

  const handleSaveAndUpdate = (isDraftOnly: boolean) => {
    const updatedSections = sections.map((sec, idx) =>
      idx === 2 ? { ...sec, content: keyFeaturesText, hasMissingEvidence: false } : sec
    );
    const updatedSeo: SeoMetadata = {
      ...product.seo,
      titleVi,
      titleEn,
      descVi: seoDescVi,
      descEn: shortDescEn,
    };
    const note = isDraftOnly
      ? `Lưu nháp nội dung VI/EN (${seoLen} ký tự SEO)`
      : `Cập nhật nội dung Marketing & SEO (${seoLen} ký tự)`;

    onSaveMarketingAndSeo(product.sku, updatedSections, updatedSeo, note);
    setSavedToast(
      `${note} thành công — Phiên bản mới đã được ghi vào Bộ nhớ (Memory).`
    );
  };

  return (
    <div className="p-3 lg:p-5 max-w-[1500px] mx-auto space-y-4">
      {/* Top Department Banner */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-[#231D1A] border border-[#3E322C] rounded-2xl px-5 py-3">
        <div className="flex items-center gap-3">
          <AgentRobotAvatar
            department="marketing"
            size="sm"
            isActive={true}
            reduceMotion={reduceMotion}
          />
          <div>
            <h1 className="text-base lg:text-lg font-bold text-[#FAF6F0]">
              Marketing (MARKETING)
            </h1>
            <p className="text-xs text-[#C4B5AA]">
              Biên tập nội dung sản phẩm & tối ưu hiển thị · Song ngữ Việt/Anh, xem trước cửa hàng và bộ đếm SEO
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="px-2.5 py-1 rounded-full bg-[#332924] text-[#F59E0B] font-mono border border-[#4D3D35]">
            Phiên bản hiện tại: {product.marketingVersions[0]?.versionId || 'v1.2'}
          </span>
          <button
            type="button"
            onClick={onProceedToImageStudio}
            className="px-3.5 py-1.5 rounded-lg bg-[#D9382C] hover:bg-[#B82D22] text-white font-semibold inline-flex items-center gap-1.5 transition-colors"
          >
            <span>Sang bước Ảnh (Image Studio)</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {savedToast && (
        <div className="bg-[#DCFCE7] border border-[#86EFAC] text-[#14532D] px-4 py-2.5 rounded-xl text-xs font-semibold flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-[#16A34A]" />
            <span>{savedToast}</span>
          </div>
          <button
            type="button"
            onClick={() => setSavedToast(null)}
            className="text-xs underline"
          >
            Đóng
          </button>
        </div>
      )}

      {/* MAIN STORYBOARD CARD: WARM IVORY WORKSPACE */}
      <div className="bg-[#F6F1EA] text-[#1F1916] border border-[#D8CEC2] rounded-2xl shadow-xl overflow-hidden">
        {/* Sub-Tabs Bar & SKU Indicator */}
        <div className="px-5 pt-3 bg-[#EFE8DE] border-b border-[#D8CEC2] flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-6">
            <button
              type="button"
              onClick={() => setSubTab('content')}
              className={`pb-2.5 text-xs sm:text-sm font-bold border-b-2 transition-colors ${
                subTab === 'content'
                  ? 'border-[#D9382C] text-[#D9382C]'
                  : 'border-transparent text-[#6E5D53] hover:text-[#1E1916]'
              }`}
            >
              Biên tập nội dung
            </button>
            <button
              type="button"
              onClick={() => setSubTab('seo_7part')}
              className={`pb-2.5 text-xs sm:text-sm font-bold border-b-2 transition-colors ${
                subTab === 'seo_7part'
                  ? 'border-[#D9382C] text-[#D9382C]'
                  : 'border-transparent text-[#6E5D53] hover:text-[#1E1916]'
              }`}
            >
              Tối ưu SEO & Cấu trúc 7 phần ({product.marketingSections.length})
            </button>
          </div>

          <div className="pb-2 flex items-center gap-2 text-xs">
            <span className="text-[#574B43] font-medium">Mã sản phẩm (SKU):</span>
            <span className="px-2.5 py-1 rounded-md bg-white border border-[#C9BBAE] font-mono font-bold text-[#1E1916]">
              {product.sku}
            </span>
          </div>
        </div>

        {/* 2-COLUMN BODY: LEFT BILINGUAL & SEO EDITOR + RIGHT STOREFRONT PREVIEW */}
        <div className="grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-[#D8CEC2]">
          {/* LEFT 7 COLS: BILINGUAL CONTENT & SEO COUNTER */}
          <div className="lg:col-span-7 p-5 space-y-4">
            {/* Language Switcher Row */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs">
                <span className="font-semibold text-[#4A3B34]">Ngôn ngữ biên tập:</span>
                <div className="inline-flex rounded-lg bg-[#E5DEC9] p-0.5 border border-[#C9BBAE]">
                  <button
                    type="button"
                    onClick={() => setEditorLang('vi')}
                    className={`px-3 py-1 rounded-md text-xs font-bold transition-colors ${
                      editorLang === 'vi'
                        ? 'bg-[#D9382C] text-white'
                        : 'text-[#4A3B34] hover:text-[#1E1916]'
                    }`}
                  >
                    Tiếng Việt (VI)
                  </button>
                  <button
                    type="button"
                    onClick={() => setEditorLang('en')}
                    className={`px-3 py-1 rounded-md text-xs font-bold transition-colors ${
                      editorLang === 'en'
                        ? 'bg-[#D9382C] text-white'
                        : 'text-[#4A3B34] hover:text-[#1E1916]'
                    }`}
                  >
                    English (EN)
                  </button>
                </div>
              </div>
              <span className="text-[11px] font-mono text-[#6E5D53]">
                Nguồn dẫn chứng: {product.catalogueFile} (Tr.{product.activePdfPage})
              </span>
            </div>

            {subTab === 'content' ? (
              <>
                {/* 1. Tiêu đề sản phẩm / Product Title */}
                <div className="space-y-2 bg-white p-3.5 rounded-xl border border-[#DED4C8]">
                  <div className="text-xs font-extrabold text-[#1E1916]">
                    1. Tiêu đề sản phẩm / Product Title <span className="text-[#D9382C]">*</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-7 h-6 rounded bg-[#FADCD9] text-[#B91C1C] font-mono font-bold text-[11px] flex items-center justify-center shrink-0">
                      VI
                    </span>
                    <input
                      type="text"
                      value={titleVi}
                      onChange={(e) => setTitleVi(e.target.value)}
                      aria-label="Tiêu đề sản phẩm tiếng Việt"
                      className="w-full px-3 py-1.5 rounded-lg bg-[#FAF6F0] border border-[#D5C8B8] text-xs sm:text-sm font-semibold text-[#1E1916]"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-7 h-6 rounded bg-[#E5E0D8] text-[#4A3B34] font-mono font-bold text-[11px] flex items-center justify-center shrink-0">
                      EN
                    </span>
                    <input
                      type="text"
                      value={titleEn}
                      onChange={(e) => setTitleEn(e.target.value)}
                      aria-label="Tiêu đề sản phẩm tiếng Anh"
                      className="w-full px-3 py-1.5 rounded-lg bg-[#FAF6F0] border border-[#D5C8B8] text-xs sm:text-sm font-medium text-[#1E1916]"
                    />
                  </div>
                </div>

                {/* 2. Mô tả ngắn / Short Description */}
                <div className="space-y-2 bg-white p-3.5 rounded-xl border border-[#DED4C8]">
                  <div className="text-xs font-extrabold text-[#1E1916]">
                    2. Mô tả ngắn / Short Description <span className="text-[#D9382C]">*</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="w-7 h-6 rounded bg-[#FADCD9] text-[#B91C1C] font-mono font-bold text-[11px] flex items-center justify-center shrink-0 mt-1">
                      VI
                    </span>
                    <textarea
                      rows={2}
                      value={shortDescVi}
                      onChange={(e) => setShortDescVi(e.target.value)}
                      aria-label="Mô tả ngắn tiếng Việt"
                      className="w-full px-3 py-1.5 rounded-lg bg-[#FAF6F0] border border-[#D5C8B8] text-xs text-[#1E1916] leading-relaxed"
                    />
                  </div>
                  <div className="flex items-start gap-2">
                    <span className="w-7 h-6 rounded bg-[#E5E0D8] text-[#4A3B34] font-mono font-bold text-[11px] flex items-center justify-center shrink-0 mt-1">
                      EN
                    </span>
                    <textarea
                      rows={2}
                      value={shortDescEn}
                      onChange={(e) => setShortDescEn(e.target.value)}
                      aria-label="Mô tả ngắn tiếng Anh"
                      className="w-full px-3 py-1.5 rounded-lg bg-[#FAF6F0] border border-[#D5C8B8] text-xs text-[#1E1916] leading-relaxed"
                    />
                  </div>
                </div>

                {/* 3. Đặc điểm nổi bật / Key Features */}
                <div className="space-y-2 bg-white p-3.5 rounded-xl border border-[#DED4C8]">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-extrabold text-[#1E1916]">
                      3. Đặc điểm nổi bật / Key Features
                    </span>
                    <span className="text-[11px] font-mono text-[#15803D]">
                      ✔ Có dẫn chứng Trang {product.activePdfPage}
                    </span>
                  </div>

                  {/* Formatting Toolbar matching Storyboard */}
                  <div className="flex items-center gap-1 bg-[#F6F1EA] px-2.5 py-1.5 rounded-lg border border-[#DED4C8] text-[#4A3B34]">
                    <Bold className="w-3.5 h-3.5 mx-1 cursor-pointer hover:text-[#1E1916]" />
                    <Italic className="w-3.5 h-3.5 mx-1 cursor-pointer hover:text-[#1E1916]" />
                    <Underline className="w-3.5 h-3.5 mx-1 cursor-pointer hover:text-[#1E1916]" />
                    <span className="text-[#C9BBAE] mx-1">|</span>
                    <List className="w-3.5 h-3.5 mx-1 cursor-pointer hover:text-[#1E1916]" />
                    <ListOrdered className="w-3.5 h-3.5 mx-1 cursor-pointer hover:text-[#1E1916]" />
                    <span className="text-[#C9BBAE] mx-1">|</span>
                    <Link2 className="w-3.5 h-3.5 mx-1 cursor-pointer hover:text-[#1E1916]" />
                  </div>

                  <textarea
                    rows={4}
                    value={keyFeaturesText}
                    onChange={(e) => setKeyFeaturesText(e.target.value)}
                    aria-label="Đặc điểm nổi bật"
                    className="w-full px-3 py-2 rounded-lg bg-[#FAF6F0] border border-[#D5C8B8] text-xs font-medium text-[#1E1916] leading-relaxed"
                  />
                </div>
              </>
            ) : (
              /* 7-Part Structured View */
              <div className="space-y-2.5 max-h-[380px] overflow-y-auto pr-1">
                {sections.map((sec) => (
                  <div
                    key={sec.id}
                    className={`p-3 rounded-xl border ${
                      sec.hasMissingEvidence
                        ? 'bg-[#FEF3C7] border-[#F59E0B]'
                        : 'bg-white border-[#DED4C8]'
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs font-bold text-[#1E1916]">
                      <span>{sec.title}</span>
                      <span className="font-mono text-[11px] text-[#6E5D53]">
                        {sec.evidenceRef}
                      </span>
                    </div>
                    <textarea
                      rows={2}
                      value={sec.content}
                      onChange={(e) =>
                        setSections((prev) =>
                          prev.map((s) =>
                            s.id === sec.id
                              ? { ...s, content: e.target.value, hasMissingEvidence: false }
                              : s
                          )
                        )
                      }
                      className="mt-1.5 w-full px-2.5 py-1.5 rounded bg-[#FAF6F0] border border-[#D5C8B8] text-xs text-[#1E1916]"
                    />
                  </div>
                ))}
              </div>
            )}

            {/* Mô tả SEO (140 – 160 ký tự) + Character Counter */}
            <div className="p-3.5 rounded-xl bg-[#EFE8DE] border border-[#D5C8B8] space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-extrabold text-[#1E1916]">
                  Mô tả SEO (140 – 160 ký tự)
                </span>
                <span
                  className={`font-mono font-bold tabular-nums ${
                    isSeoOptimal ? 'text-[#15803D]' : 'text-[#B45309]'
                  }`}
                >
                  {seoLen} / 160
                </span>
              </div>

              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                <textarea
                  rows={2}
                  value={seoDescVi}
                  onChange={(e) => setSeoDescVi(e.target.value)}
                  aria-label="Mô tả SEO tiếng Việt"
                  className="flex-1 px-3 py-2 rounded-lg bg-white border border-[#C9BBAE] text-xs text-[#1E1916] leading-relaxed"
                />
                <div className="shrink-0 flex items-center gap-1.5 px-3 py-2 rounded-lg bg-[#DCFCE7] border border-[#86EFAC] text-xs font-bold text-[#15803D]">
                  {isSeoOptimal ? (
                    <>
                      <CheckCircle2 className="w-4 h-4 text-[#16A34A]" />
                      <span>Độ dài phù hợp</span>
                    </>
                  ) : (
                    <>
                      <AlertTriangle className="w-4 h-4 text-[#B45309]" />
                      <span>Cần 140–160 ký tự</span>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* RIGHT 5 COLS: STOREFRONT PREVIEW (Xem trước cửa hàng) */}
          <div className="lg:col-span-5 p-5 bg-[#FAF6F0] flex flex-col justify-between space-y-4">
            <div className="space-y-3.5">
              {/* Storefront Preview Header */}
              <div className="flex items-center justify-between border-b border-[#E2D8CC] pb-2.5">
                <h2 className="text-sm font-extrabold text-[#1E1916]">
                  Xem trước cửa hàng (Storefront Preview)
                </h2>
                <div className="inline-flex rounded-md bg-[#E5DEC9] p-0.5 border border-[#C9BBAE] text-[11px] font-mono font-bold">
                  <button
                    type="button"
                    onClick={() => setPreviewLang('vi')}
                    className={`px-2 py-0.5 rounded ${
                      previewLang === 'vi'
                        ? 'bg-[#FADCD9] text-[#B91C1C]'
                        : 'text-[#574B43]'
                    }`}
                  >
                    VI
                  </button>
                  <button
                    type="button"
                    onClick={() => setPreviewLang('en')}
                    className={`px-2 py-0.5 rounded ${
                      previewLang === 'en'
                        ? 'bg-[#FADCD9] text-[#B91C1C]'
                        : 'text-[#574B43]'
                    }`}
                  >
                    EN
                  </button>
                </div>
              </div>

              {/* Storefront Card */}
              <div className="bg-white rounded-2xl border border-[#DED4C8] p-4 shadow-sm space-y-3">
                {/* Main Carousel Image */}
                <div className="relative h-52 rounded-xl bg-[#F4EFE6] border border-[#E5DEC9] overflow-hidden">
                  <ProductVisualCanvas
                    sku={product.sku}
                    variant={previewSlides[previewSlideIndex].variant}
                    backgroundId="bis-warm-ivory"
                    paddingPercent={8}
                    className="w-full h-full"
                  />
                  <button
                    type="button"
                    onClick={() =>
                      setPreviewSlideIndex(
                        (i) => (i - 1 + previewSlides.length) % previewSlides.length
                      )
                    }
                    aria-label="Ảnh trước"
                    className="absolute left-2 top-1/2 -translate-y-1/2 w-7 h-7 rounded-full bg-white/90 border border-[#D8CEC2] flex items-center justify-center text-[#1E1916] shadow"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      setPreviewSlideIndex((i) => (i + 1) % previewSlides.length)
                    }
                    aria-label="Ảnh tiếp theo"
                    className="absolute right-2 top-1/2 -translate-y-1/2 w-7 h-7 rounded-full bg-white/90 border border-[#D8CEC2] flex items-center justify-center text-[#1E1916] shadow"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>

                {/* 4 Thumbnail Previews */}
                <div className="grid grid-cols-4 gap-2">
                  {previewSlides.map((slide, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setPreviewSlideIndex(idx)}
                      className={`h-14 rounded-lg border-2 overflow-hidden transition-all ${
                        previewSlideIndex === idx
                          ? 'border-[#D9382C] shadow-xs'
                          : 'border-[#E5DEC9] opacity-75 hover:opacity-100'
                      }`}
                    >
                      <ProductVisualCanvas
                        sku={product.sku}
                        variant={slide.variant}
                        backgroundId="bis-pure-white"
                        paddingPercent={10}
                        className="w-full h-full"
                      />
                    </button>
                  ))}
                </div>

                {/* Product Title & Short Description in Storefront */}
                <div className="pt-1 space-y-1.5">
                  <h3 className="text-base font-extrabold text-[#1E1916]">
                    {previewLang === 'vi' ? titleVi : titleEn}
                  </h3>
                  <p className="text-xs text-[#4A3B34] leading-relaxed">
                    {previewLang === 'vi' ? shortDescVi : shortDescEn}
                  </p>
                </div>

                {/* Storefront Preview CTA */}
                <button
                  type="button"
                  onClick={() => handleSaveAndUpdate(true)}
                  className="w-full py-2 rounded-xl bg-[#E04F44] hover:bg-[#C83E33] text-white text-xs font-bold shadow-xs transition-colors"
                >
                  Thêm vào dự thảo
                </button>
              </div>
            </div>

            {/* Bottom Action Bar: Lưu nháp & Cập nhật nội dung */}
            <div className="pt-3 border-t border-[#E2D8CC] flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => handleSaveAndUpdate(true)}
                className="px-4 py-2 rounded-xl bg-white hover:bg-[#EFE8DE] text-[#3B302B] border border-[#C9BBAE] text-xs font-bold inline-flex items-center gap-1.5 transition-colors"
              >
                <Save className="w-3.5 h-3.5" />
                <span>Lưu nháp</span>
              </button>

              <button
                type="button"
                onClick={() => handleSaveAndUpdate(false)}
                className="px-5 py-2.5 rounded-xl bg-[#D9382C] hover:bg-[#B82D22] text-white text-xs sm:text-sm font-bold shadow-md inline-flex items-center gap-1.5 transition-colors"
              >
                <Check className="w-4 h-4" />
                <span>Cập nhật nội dung</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
