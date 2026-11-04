import React, { useState } from 'react';
import {
  DepartmentId,
  ProductRecord,
  VerificationStatus,
} from '../types/bisTypes';
import { evaluateHaravanDraftReadiness } from '../utils/workflowRules';
import { createHaravanProductDraft } from '../services/bisBackendAdapter';
import { ProductVisualCanvas } from './ProductVisualCanvas';
import { AgentRobotAvatar } from './AgentRobotAvatar';
import {
  CheckSquare,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Send,
  Save,
  ExternalLink,
  ShieldCheck,
} from 'lucide-react';

interface OperationsViewProps {
  product: ProductRecord;
  reduceMotion: boolean;
  onResolveDuplicate: (
    sku: string,
    haravanId: string,
    resolution: 'confirmed_unique' | 'merged_draft'
  ) => void;
  onCreatedHaravanDraft: (
    sku: string,
    draftId: string,
    previewUrl: string,
    createdAt: string
  ) => void;
  onNavigateDepartment: (dept: DepartmentId) => void;
}

export const OperationsView: React.FC<OperationsViewProps> = ({
  product,
  reduceMotion,
  onResolveDuplicate,
  onCreatedHaravanDraft,
  onNavigateDepartment,
}) => {
  const [subTab, setSubTab] = useState<'checklist' | 'duplicates' | 'actions'>('checklist');
  const [approvalNote, setApprovalNote] = useState<string>(
    'Thông tin đầy đủ, khác biệt chính: dải tải 50 kN (so với 03026 là 30 kN). Đề xuất phê duyệt và tạo nháp trên Haravan.'
  );
  const [isSubmittingDraft, setIsSubmittingDraft] = useState<boolean>(false);
  const [draftFeedback, setDraftFeedback] = useState<string | null>(null);
  const [manualOverrideReady, setManualOverrideReady] = useState<boolean>(true);

  const readiness = evaluateHaravanDraftReadiness(product);
  const primaryDuplicate = product.duplicates[0];

  const checklistRows: {
    id: string;
    label: string;
    pageBadge?: string;
    status: VerificationStatus;
    targetDept: DepartmentId;
  }[] = [
    {
      id: 'chk-basic',
      label: 'Thông tin cơ bản (SKU, tên VI/EN)',
      status: 'approved',
      targetDept: 'technical',
    },
    {
      id: 'chk-specs',
      label: 'Thông số kỹ thuật',
      status: product.checklist.technicalEvidence,
      targetDept: 'technical',
    },
    {
      id: 'chk-marketing',
      label: 'Mô tả sản phẩm (VI/EN)',
      status: product.checklist.marketingContent,
      targetDept: 'marketing',
    },
    {
      id: 'chk-image',
      label: 'Hình ảnh sản phẩm (đã duyệt)',
      status: manualOverrideReady ? 'approved' : product.checklist.imageStandard1254,
      targetDept: 'imagestudio',
    },
    {
      id: 'chk-citation',
      label: 'Tài liệu & trích dẫn (Citation)',
      pageBadge: `Trang ${product.activePdfPage}`,
      status: 'approved',
      targetDept: 'technical',
    },
  ];

  const handleCreateHaravanDraftClick = async () => {
    setIsSubmittingDraft(true);
    setDraftFeedback(null);
    try {
      if (primaryDuplicate && primaryDuplicate.resolution === 'unresolved') {
        onResolveDuplicate(product.sku, primaryDuplicate.haravanId, 'confirmed_unique');
      }
      const res = await createHaravanProductDraft(product);
      onCreatedHaravanDraft(
        product.sku,
        res.draftId,
        res.haravanPreviewUrl,
        res.createdAt
      );
      setDraftFeedback(
        `Đã khởi tạo Bản nháp trên Haravan thành công (Mã bản nháp: ${res.draftId} · Chế độ Chỉ tạo nháp, chưa công khai).`
      );
    } finally {
      setIsSubmittingDraft(false);
    }
  };

  return (
    <div className="p-3 lg:p-5 max-w-[1500px] mx-auto space-y-4">
      {/* Top Department Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 card-8d-dark border border-[#4E3E36] rounded-2xl px-5 py-3">
        <div className="flex items-center gap-3">
          <AgentRobotAvatar
            department="operations"
            size="sm"
            isActive={true}
            reduceMotion={reduceMotion}
          />
          <div>
            <h1 className="text-base lg:text-lg font-bold text-[#FAF6F0]">
              Vận hành (OPERATIONS)
            </h1>
            <p className="text-xs text-[#C4B5AA]">
              Phê duyệt sản phẩm, kiểm tra trùng lặp & đẩy Haravan (nháp) · Tuyệt đối không có quyền xóa sản phẩm Haravan
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="px-2.5 py-1 rounded-full card-8d-dark-recessed text-[#4ADE80] font-mono border border-[#4D3D35] inline-flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Chế độ An toàn: Chỉ Tạo Bản Nháp</span>
          </span>
        </div>
      </div>

      {draftFeedback && (
        <div className="bg-gradient-to-r from-[#DCFCE7] to-[#CCFBF1] border border-[#86EFAC] text-[#14532D] px-4 py-3 rounded-xl text-xs font-bold shadow-md flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-[#16A34A] shrink-0" />
            <span>{draftFeedback}</span>
          </div>
          {product.haravanDraft && (
            <span className="font-mono text-[11px] bg-white px-2.5 py-1 rounded border border-[#86EFAC]">
              URL: {product.haravanDraft.haravanPreviewUrl}
            </span>
          )}
        </div>
      )}

      {/* MAIN STORYBOARD CARD: WARM IVORY WORKSPACE */}
      <div className="card-8d-ivory text-[#1F1916] border border-[#D8CEC2] rounded-2xl overflow-hidden">
        {/* Top Breadcrumb Bar */}
        <div className="px-5 py-2.5 surface-8d-warm border-b border-[#D8CEC2] flex items-center justify-between text-xs text-[#574B43]">
          <div className="flex items-center gap-1.5 font-medium">
            <span>Danh sách sản phẩm</span>
            <span>&gt;</span>
            <strong className="text-[#1E1916]">Chi tiết phê duyệt</strong>
          </div>
          <span className="font-mono text-[11px]">
            Dữ liệu minh họa · G:\My Drive\BIS_AI_PROJECT
          </span>
        </div>

        {/* Product Summary Banner inside Card */}
        <div className="p-4 sm:px-5 card-8d-light border-b border-[#DED4C8] flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="w-16 h-16 rounded-xl border border-[#DED4C8] overflow-hidden bg-[#F8F5F0] shrink-0">
              <ProductVisualCanvas
                sku={product.sku}
                variant="bis-reference"
                backgroundId="bis-warm-ivory"
                paddingPercent={8}
                className="w-full h-full"
              />
            </div>
            <div>
              <div className="text-base font-extrabold font-mono text-[#1E1916]">
                {product.sku}
              </div>
              <div className="text-sm font-bold text-[#1E1916]">
                {product.nameVi}
              </div>
              <div className="text-xs text-[#6E5D53]">{product.nameEn}</div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {product.haravanDraft ? (
              <span className="px-3.5 py-1.5 rounded-full bg-[#DCFCE7] border border-[#86EFAC] text-[#15803D] text-xs font-bold inline-flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4" />
                <span>Trạng thái: Đã tạo nháp ({product.haravanDraft.draftId})</span>
              </span>
            ) : (
              <span className="px-3.5 py-1.5 rounded-full bg-[#FEF3C7] border border-[#FDE68A] text-[#B45309] text-xs font-bold inline-flex items-center gap-1.5">
                <Clock className="w-4 h-4" />
                <span>Trạng thái: Chờ phê duyệt</span>
              </span>
            )}
          </div>
        </div>

        {/* Sub-Tabs Bar: 1. Kiểm tra & phê duyệt | 2. Kiểm tra trùng lặp | 3. Hành động */}
        <div className="px-5 bg-[#EFE8DE] border-b border-[#D8CEC2] flex items-center gap-6">
          {[
            { id: 'checklist', label: '1. Kiểm tra & phê duyệt' },
            { id: 'duplicates', label: '2. Kiểm tra trùng lặp' },
            { id: 'actions', label: '3. Hành động' },
          ].map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setSubTab(t.id as typeof subTab)}
              className={`py-2.5 text-xs sm:text-sm font-bold border-b-2 transition-colors ${
                subTab === t.id
                  ? 'border-[#D9382C] text-[#D9382C]'
                  : 'border-transparent text-[#6E5D53] hover:text-[#1E1916]'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* 2-COLUMN MAIN CONTENT: LEFT CHECKLIST + RIGHT DUPLICATE MATCH EVIDENCE */}
        <div className="p-5 grid grid-cols-1 lg:grid-cols-12 gap-5">
          {/* LEFT 6 COLS: Danh sách kiểm tra phê duyệt */}
          <div className="lg:col-span-6 card-8d-light rounded-2xl border border-[#DED4C8] p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-[#EFE8DE] pb-2.5">
              <div className="flex items-center gap-2 text-sm font-extrabold text-[#1E1916]">
                <CheckSquare className="w-4 h-4 text-[#D9382C]" />
                <span>Danh sách kiểm tra phê duyệt</span>
              </div>
              <button
                type="button"
                onClick={() => setManualOverrideReady((prev) => !prev)}
                className="text-[11px] font-mono text-[#6E5D53] hover:text-[#1E1916] underline"
              >
                {manualOverrideReady ? 'Chế độ: Đã xác nhận đủ 5 mục' : 'Đồng bộ trực tiếp theo tab'}
              </button>
            </div>

            <div className="divide-y divide-[#EFE8DE]">
              {checklistRows.map((row) => {
                const isOk = row.status === 'approved';
                return (
                  <div
                    key={row.id}
                    className="py-3 flex items-center justify-between gap-3 text-xs sm:text-sm"
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      {isOk ? (
                        <div className="w-5 h-5 rounded bg-[#16A34A] text-white flex items-center justify-center shrink-0">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                        </div>
                      ) : (
                        <div className="w-5 h-5 rounded bg-[#F59E0B] text-white flex items-center justify-center shrink-0">
                          <AlertTriangle className="w-3.5 h-3.5" />
                        </div>
                      )}
                      <span className="font-semibold text-[#1E1916] truncate">
                        {row.label}
                      </span>
                      {row.pageBadge && (
                        <span className="px-2 py-0.5 rounded bg-[#EFE8DE] border border-[#D8CEC2] text-[11px] font-mono font-bold text-[#4A3B34] shrink-0">
                          {row.pageBadge}
                        </span>
                      )}
                    </div>

                    <button
                      type="button"
                      onClick={() => onNavigateDepartment(row.targetDept)}
                      className="text-xs font-bold text-[#574B43] hover:text-[#D9382C] underline shrink-0"
                    >
                      Xem
                    </button>
                  </div>
                );
              })}
            </div>

            {!readiness.canCreateDraft && !manualOverrideReady && (
              <div className="p-3 rounded-xl bg-[#FEF3C7] border border-[#FDE68A] text-xs text-[#92400E]">
                Lưu ý: Còn {readiness.blockingReasons.length} điều kiện đang chờ xác nhận.
              </div>
            )}
          </div>

          {/* RIGHT 6 COLS: Kết quả kiểm tra trùng lặp & Bằng chứng so khớp */}
          <div className="lg:col-span-6 card-8d-light rounded-2xl border border-[#DED4C8] p-4 space-y-3.5">
            <div className="flex items-center justify-between border-b border-[#EFE8DE] pb-2.5">
              <div className="flex items-center gap-2 text-sm font-extrabold text-[#1E1916]">
                <CheckCircle2 className="w-4 h-4 text-[#16A34A]" />
                <span>Kết quả kiểm tra trùng lặp</span>
              </div>
            </div>

            {/* Summary Banner matching Storyboard */}
            <div className="p-3 rounded-xl bg-[#F0FDF4] border border-[#BBF7D0] flex items-start gap-2.5 text-xs">
              <CheckCircle2 className="w-5 h-5 text-[#16A34A] shrink-0 mt-0.5" />
              <div className="text-[#14532D] leading-relaxed">
                <div className="font-bold">Không phát hiện trùng lặp chính xác.</div>
                <div>
                  Có <strong>1 sản phẩm tương tự</strong> (độ tương đồng:{' '}
                  <strong className="text-[#D9382C]">
                    {primaryDuplicate?.similarityPercent ?? 92}%
                  </strong>
                  ).
                </div>
              </div>
            </div>

            {/* Similar Product Card */}
            <div className="space-y-1.5">
              <div className="text-xs font-extrabold text-[#1E1916]">
                Sản phẩm tương tự
              </div>
              <div className="p-3 rounded-xl surface-8d-warm border border-[#DED4C8] flex items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-14 h-14 rounded-lg border border-[#DED4C8] bg-white overflow-hidden shrink-0">
                    <ProductVisualCanvas
                      sku="03026"
                      variant="bis-reference"
                      backgroundId="bis-pure-white"
                      paddingPercent={10}
                      className="w-full h-full"
                    />
                  </div>
                  <div>
                    <div className="text-xs font-mono font-extrabold text-[#1E1916]">
                      {primaryDuplicate?.sku || '03026'}
                    </div>
                    <div className="text-xs font-bold text-[#2B221E]">
                      {primaryDuplicate?.title ||
                        'Máy đo độ bền kéo vải (phiên bản 30 kN)'}
                    </div>
                    <div className="text-xs text-[#574B43]">
                      Độ tương đồng:{' '}
                      <strong className="text-[#D9382C]">
                        {primaryDuplicate?.similarityPercent ?? 92}%
                      </strong>
                    </div>
                  </div>
                </div>

                {primaryDuplicate && (
                  <button
                    type="button"
                    onClick={() =>
                      onResolveDuplicate(
                        product.sku,
                        primaryDuplicate.haravanId,
                        'confirmed_unique'
                      )
                    }
                    className={`px-2.5 py-1.5 rounded-lg text-xs font-bold border transition-colors shrink-0 ${
                      primaryDuplicate.resolution === 'confirmed_unique'
                        ? 'bg-[#DCFCE7] text-[#15803D] border-[#86EFAC]'
                        : 'bg-white text-[#D9382C] border-[#D9382C] hover:bg-[#FFF5F3]'
                    }`}
                  >
                    {primaryDuplicate.resolution === 'confirmed_unique'
                      ? '✔ Đã xác nhận khác biệt'
                      : 'So sánh chi tiết'}
                  </button>
                )}
              </div>
            </div>

            {/* Bằng chứng so khớp Table (Exact match to Storyboard) */}
            <div>
              <div className="text-xs font-extrabold text-[#1E1916] mb-1.5">
                Bằng chứng so khớp
              </div>
              <div className="rounded-xl border border-[#DED4C8] overflow-hidden">
                <table className="w-full text-xs border-collapse">
                  <thead>
                    <tr className="bg-[#EFE8DE] text-[#4A3B34] border-b border-[#DED4C8]">
                      <th className="py-2 px-3 text-left font-bold">Trường thông tin</th>
                      <th className="py-2 px-3 text-left font-bold">
                        {product.sku} (hiện tại)
                      </th>
                      <th className="py-2 px-3 text-left font-bold">
                        {primaryDuplicate?.sku || '03026'} (tương tự)
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#EFE8DE]">
                    <tr className="bg-[#FFF5F3]">
                      <td className="py-2 px-3 font-semibold text-[#1E1916]">Dải tải</td>
                      <td className="py-2 px-3 font-mono font-extrabold text-[#D9382C]">
                        0.5 – 50 kN
                      </td>
                      <td className="py-2 px-3 font-mono font-bold text-[#B91C1C]">
                        0.5 – 30 kN
                      </td>
                    </tr>
                    <tr>
                      <td className="py-2 px-3 font-semibold text-[#4A3B34]">Hành trình</td>
                      <td className="py-2 px-3 font-mono text-[#1E1916]">1,200 mm</td>
                      <td className="py-2 px-3 font-mono text-[#574B43]">1,200 mm</td>
                    </tr>
                    <tr>
                      <td className="py-2 px-3 font-semibold text-[#4A3B34]">Tiêu chuẩn</td>
                      <td className="py-2 px-3 font-mono text-[#1E1916]">ISO 13934-1</td>
                      <td className="py-2 px-3 font-mono text-[#574B43]">ISO 13934-1</td>
                    </tr>
                    <tr>
                      <td className="py-2 px-3 font-semibold text-[#4A3B34]">
                        Tên sản phẩm
                      </td>
                      <td className="py-2 px-3 text-[#1E1916]">{product.nameVi}</td>
                      <td className="py-2 px-3 text-[#574B43]">{product.nameVi}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        {/* BOTTOM BAR: Ghi chú phê duyệt (tùy chọn) + Tạo bản nháp trên Haravan */}
        <div className="px-5 py-4 surface-8d-warm border-t border-[#D8CEC2] flex flex-col lg:flex-row lg:items-end justify-between gap-4">
          <div className="flex-1 space-y-1">
            <div className="flex items-center justify-between text-xs">
              <label
                htmlFor="ops-approval-note"
                className="font-extrabold text-[#1E1916]"
              >
                Ghi chú phê duyệt (tùy chọn)
              </label>
              <span className="font-mono text-[#6E5D53]">
                {approvalNote.length} / 300
              </span>
            </div>
            <textarea
              id="ops-approval-note"
              rows={2}
              maxLength={300}
              value={approvalNote}
              onChange={(e) => setApprovalNote(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-white border border-[#C9BBAE] text-xs text-[#1E1916] leading-relaxed shadow-inner"
            />
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 shrink-0">
            <button
              type="button"
              onClick={() =>
                setDraftFeedback('Đã lưu nháp ghi chú phê duyệt tại trạm Operations.')
              }
              className="px-4 py-2.5 rounded-xl card-8d-interactive text-[#3B302B] border border-[#C9BBAE] text-xs font-bold inline-flex items-center justify-center gap-1.5"
            >
              <Save className="w-3.5 h-3.5" />
              <span>Lưu nháp</span>
            </button>

            <div className="flex flex-col items-center">
              <button
                type="button"
                disabled={isSubmittingDraft}
                onClick={handleCreateHaravanDraftClick}
                className="w-full sm:w-auto px-6 py-2.5 rounded-xl btn-8d-crimson disabled:opacity-60 text-white text-xs sm:text-sm font-extrabold inline-flex items-center justify-center gap-2 transition-all"
              >
                <Send className="w-4 h-4" />
                <span>
                  {isSubmittingDraft
                    ? 'Đang tạo bản nháp...'
                    : 'Tạo bản nháp trên Haravan'}
                </span>
              </button>
              <span className="text-[11px] text-[#574B43] mt-1 font-medium">
                (chỉ nháp, chưa công khai)
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
