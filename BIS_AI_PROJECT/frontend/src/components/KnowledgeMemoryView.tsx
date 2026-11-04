import React, { useState } from 'react';
import {
  KnowledgeDoc,
  MemoryEntry,
} from '../types/bisTypes';
import { AgentRobotAvatar } from './AgentRobotAvatar';
import {
  Search,
  Upload,
  Folder,
  FolderOpen,
  FileText,
  Clock,
  CheckCircle2,
  XCircle,
  Edit3,
  RotateCcw,
  Plus,
  Languages,
} from 'lucide-react';

interface KnowledgeMemoryViewProps {
  mode: 'knowledge' | 'memory';
  docs: KnowledgeDoc[];
  memoryEntries: MemoryEntry[];
  reduceMotion: boolean;
  onAddCalibrationEntry: (title: string, content: string, skuContext: string) => void;
  onToggleRevokeMemory: (entryId: string) => void;
  onSwitchMode: (mode: 'knowledge' | 'memory') => void;
}

export const KnowledgeMemoryView: React.FC<KnowledgeMemoryViewProps> = ({
  mode,
  docs,
  memoryEntries,
  reduceMotion,
  onAddCalibrationEntry,
  onToggleRevokeMemory,
  onSwitchMode,
}) => {
  // Knowledge State
  const [searchQuery, setSearchQuery] = useState<string>('ISO 13934-1');
  const [activeFolderId, setActiveFolderId] = useState<string>('intl_std');
  const [expandedDocId, setExpandedDocId] = useState<string | null>(null);
  const [uploadNotice, setUploadNotice] = useState<string | null>(null);

  // Memory State
  const [memorySubTab, setMemorySubTab] = useState<
    'timeline' | 'notes' | 'versions' | 'sync'
  >('timeline');
  const [isEditingNote, setIsEditingNote] = useState<boolean>(false);
  const [knowledgeNoteText, setKnowledgeNoteText] = useState<string>(
    '• Ứng dụng: kiểm tra độ bền kéo, độ giãn dài, độ đứt.\n• Tiêu chuẩn: ISO 13934-1, ASTM D5034.\n• Lưu ý: kiểm tra hiệu chuẩn định kỳ 12 tháng.'
  );
  const [cloudBackupState, setCloudBackupState] = useState<'error' | 'synced'>('error');

  const folders = [
    { id: 'all', label: 'Tất cả tài liệu', count: 68 },
    { id: 'intl_std', label: 'Tiêu chuẩn quốc tế', count: 18 },
    { id: 'sop', label: 'Hướng dẫn vận hành', count: 14 },
    { id: 'calibration', label: 'Bảo trì & hiệu chuẩn', count: 9 },
    { id: 'textile_test', label: 'Thử nghiệm dệt may', count: 12 },
    { id: 'catalog', label: 'Catalog thiết bị', count: 8 },
    { id: 'material', label: 'Kiến thức vật liệu', count: 7 },
  ];

  const filteredDocs = docs.filter((d) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      d.title.toLowerCase().includes(q) ||
      d.fileName.toLowerCase().includes(q) ||
      d.pages.some(
        (p) =>
          p.heading.toLowerCase().includes(q) ||
          p.excerptVi.toLowerCase().includes(q) ||
          p.standardRefs.some((r) => r.toLowerCase().includes(q))
      )
    );
  });

  const handleSaveKnowledgeNote = () => {
    setIsEditingNote(false);
    onAddCalibrationEntry(
      'Cập nhật Ghi chú tri thức (03026A)',
      knowledgeNoteText,
      '03026A'
    );
  };

  return (
    <div className="p-3 lg:p-5 max-w-[1500px] mx-auto space-y-4">
      {/* Top Department Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 card-8d-dark border border-[#4E3E36] rounded-2xl px-5 py-3">
        <div className="flex items-center gap-3">
          <AgentRobotAvatar
            department={mode}
            size="sm"
            isActive={true}
            reduceMotion={reduceMotion}
          />
          <div>
            <h1 className="text-base lg:text-lg font-bold text-[#FAF6F0]">
              {mode === 'knowledge'
                ? 'Tri thức (KNOWLEDGE)'
                : 'Bộ nhớ (MEMORY)'}
            </h1>
            <p className="text-xs text-[#C4B5AA]">
              {mode === 'knowledge'
                ? 'Thư viện tài liệu chuyên ngành dệt may & thiết bị kiểm tra · Tra cứu theo trang trích dẫn'
                : 'Lịch sử trao đổi, ghi chú tri thức, phiên bản & trạng thái đồng bộ trung thực'}
            </p>
          </div>
        </div>

        {/* Quick Switcher between Knowledge and Memory */}
        <div className="inline-flex rounded-xl card-8d-dark-recessed p-1 border border-[#3E322C] text-xs">
          <button
            type="button"
            onClick={() => onSwitchMode('knowledge')}
            className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
              mode === 'knowledge'
                ? 'btn-8d-crimson text-white'
                : 'text-[#B8AAA0] hover:text-white'
            }`}
          >
            Tri thức (Knowledge)
          </button>
          <button
            type="button"
            onClick={() => onSwitchMode('memory')}
            className={`px-3 py-1.5 rounded-lg font-semibold transition-all ${
              mode === 'memory'
                ? 'btn-8d-crimson text-white'
                : 'text-[#B8AAA0] hover:text-white'
            }`}
          >
            Bộ nhớ (Memory)
          </button>
        </div>
      </div>

      {mode === 'knowledge' ? (
        /* =========================================================
           TAB 5: TRI THỨC (KNOWLEDGE) — STORYBOARD BOTTOM-CENTER
           ========================================================= */
        <div className="card-8d-ivory text-[#1F1916] border border-[#D8CEC2] rounded-2xl overflow-hidden">
          {/* Top Search & Upload Bar */}
          <div className="p-4 surface-8d-warm border-b border-[#D8CEC2] flex flex-wrap items-center gap-2.5">
            <div className="relative flex-1 min-w-[240px]">
              <Search className="w-4 h-4 text-[#786B62] absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Tìm kiếm tài liệu, tiêu chuẩn, quy trình... (ví dụ: ISO 13934-1, độ bền kéo)"
                aria-label="Tìm kiếm tài liệu tri thức"
                className="w-full pl-9 pr-4 py-2 rounded-xl bg-white border border-[#C9BBAE] text-xs sm:text-sm text-[#1E1916] shadow-inner"
              />
            </div>

            <button
              type="button"
              onClick={() => setSearchQuery(searchQuery || 'ISO 13934-1')}
              className="px-5 py-2 rounded-xl btn-8d-crimson text-white text-xs sm:text-sm font-bold transition-all"
            >
              Tìm kiếm
            </button>

            <button
              type="button"
              onClick={() =>
                setUploadNotice(
                  'Đã tiếp nhận yêu cầu tải tài liệu mới vào thư mục Tiêu chuẩn quốc tế (Chế độ Demo).'
                )
              }
              className="px-4 py-2 rounded-xl card-8d-interactive text-[#2B221E] border border-[#C9BBAE] text-xs sm:text-sm font-bold inline-flex items-center gap-1.5"
            >
              <Upload className="w-4 h-4 text-[#574B43]" />
              <span>Tải lên</span>
            </button>
          </div>

          {uploadNotice && (
            <div className="px-5 py-2 bg-[#DCFCE7] border-b border-[#86EFAC] text-xs font-semibold text-[#14532D] flex items-center justify-between">
              <span>{uploadNotice}</span>
              <button
                type="button"
                onClick={() => setUploadNotice(null)}
                className="underline"
              >
                Đóng
              </button>
            </div>
          )}

          {/* 2-Column Body: Left Folders (Thư mục tài liệu) + Right Search Results with Citations */}
          <div className="grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-[#D8CEC2]">
            {/* Left 3 Cols: Thư mục tài liệu */}
            <div className="lg:col-span-3 p-4 bg-[#FAF6F0] space-y-2">
              <h2 className="text-xs sm:text-sm font-extrabold text-[#1E1916] px-2 mb-2">
                Thư mục tài liệu
              </h2>
              <div className="space-y-1">
                {folders.map((folder) => {
                  const isAct = activeFolderId === folder.id;
                  return (
                    <button
                      key={folder.id}
                      type="button"
                      onClick={() => setActiveFolderId(folder.id)}
                      className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold transition-colors ${
                        isAct
                          ? 'bg-[#FADCD9] text-[#B91C1C] font-bold border border-[#E6A8A1]'
                          : 'text-[#3B302B] hover:bg-[#EFE8DE]'
                      }`}
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        {isAct ? (
                          <FolderOpen className="w-4 h-4 text-[#D9382C] shrink-0" />
                        ) : (
                          <Folder className="w-4 h-4 text-[#D97706] shrink-0" />
                        )}
                        <span className="truncate">{folder.label}</span>
                      </div>
                      <span className="font-mono text-[11px] text-[#6E5D53]">
                        ({folder.count})
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Right 9 Cols: Kết quả tìm kiếm kèm trang trích dẫn */}
            <div className="lg:col-span-9 p-5 space-y-3.5">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h2 className="text-sm font-extrabold text-[#1E1916]">
                  Kết quả tìm kiếm: &ldquo;{searchQuery || 'Tất cả'}&rdquo; ({filteredDocs.length}{' '}
                  tài liệu)
                </h2>
                <span className="text-xs font-mono text-[#6E5D53]">
                  Bấm vào từng trang trích dẫn bên phải để xem bản dịch thuật ngữ
                </span>
              </div>

              <div className="space-y-3">
                {filteredDocs.map((doc) => {
                  const isExpanded = expandedDocId === doc.id;
                  return (
                    <div
                      key={doc.id}
                      className="card-8d-light rounded-2xl border border-[#DED4C8] p-4 space-y-3"
                    >
                      <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-start">
                        {/* Left 7 Cols: PDF Icon + Title + Metadata + Summary */}
                        <div className="md:col-span-7 flex items-start gap-3">
                          <div className="w-10 h-11 rounded-lg btn-8d-crimson text-white font-mono font-extrabold text-[11px] flex items-center justify-center shrink-0">
                            PDF
                          </div>
                          <div className="space-y-1 min-w-0">
                            <h3 className="text-xs sm:text-sm font-extrabold text-[#1E1916] leading-snug">
                              {doc.title}
                            </h3>
                            <div className="text-[11px] font-mono text-[#6E5D53]">
                              {doc.brand} | {doc.totalPages} trang | Cập nhật: {doc.updatedAt}
                            </div>
                            <p className="text-xs text-[#4A3B34] leading-relaxed pt-0.5">
                              {doc.pages[0]?.excerptVi}
                            </p>
                          </div>
                        </div>

                        {/* Right 5 Cols: Trích dẫn (Page Citations Box matching Storyboard) */}
                        <div className="md:col-span-5 surface-8d-warm rounded-xl border border-[#E5DEC9] p-3 space-y-1.5">
                          <div className="flex items-center justify-between text-xs font-extrabold text-[#1E1916]">
                            <span>Trích dẫn</span>
                            <button
                              type="button"
                              onClick={() =>
                                setExpandedDocId(isExpanded ? null : doc.id)
                              }
                              className="text-[11px] font-mono text-[#D9382C] hover:underline inline-flex items-center gap-1"
                            >
                              <Languages className="w-3 h-3" />
                              <span>{isExpanded ? 'Thu gọn dịch' : 'Đối chiếu EN/VI'}</span>
                            </button>
                          </div>

                          <div className="space-y-1 text-xs text-[#3B302B]">
                            {doc.pages.map((pg) => (
                              <div
                                key={pg.pageNumber}
                                onClick={() => setExpandedDocId(doc.id)}
                                className="py-1 px-2 rounded bg-white border border-[#E5DEC9] hover:border-[#D9382C] cursor-pointer transition-colors font-medium truncate"
                              >
                                {pg.heading}
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>

                      {/* Expanded Bilingual Excerpt Comparison */}
                      {isExpanded && (
                        <div className="pt-3 border-t border-[#EFE8DE] grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                          {doc.pages.map((pg) => (
                            <div
                              key={pg.pageNumber}
                              className="p-3 rounded-xl bg-[#FAF6F0] border border-[#DED4C8] space-y-1"
                            >
                              <div className="font-mono font-bold text-[#D9382C]">
                                {pg.heading}
                              </div>
                              <div className="text-[#574B43] italic">
                                EN: &ldquo;{pg.excerptEn}&rdquo;
                              </div>
                              <div className="text-[#1E1916] font-medium">
                                VI: &ldquo;{pg.excerptVi}&rdquo;
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* =========================================================
           TAB 6: BỘ NHỚ (MEMORY) — STORYBOARD BOTTOM-RIGHT
           ========================================================= */
        <div className="card-8d-ivory text-[#1F1916] border border-[#D8CEC2] rounded-2xl overflow-hidden">
          {/* Top Sub-Tabs Bar */}
          <div className="px-5 surface-8d-warm border-b border-[#D8CEC2] flex flex-wrap items-center gap-6">
            {[
              { id: 'timeline', label: 'Lịch sử trao đổi' },
              { id: 'notes', label: 'Ghi chú tri thức' },
              { id: 'versions', label: 'Phiên bản chỉnh sửa' },
              { id: 'sync', label: 'Đồng bộ dữ liệu' },
            ].map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setMemorySubTab(t.id as typeof memorySubTab)}
                className={`py-3 text-xs sm:text-sm font-bold border-b-2 transition-colors ${
                  memorySubTab === t.id
                    ? 'border-[#D9382C] text-[#D9382C]'
                    : 'border-transparent text-[#6E5D53] hover:text-[#1E1916]'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* 2-COLUMN COMPREHENSIVE STORYBOARD BODY */}
          <div className="p-5 grid grid-cols-1 lg:grid-cols-12 gap-5">
            {/* LEFT 5 COLS: Lịch sử trao đổi (Timeline Hôm nay & Hôm qua) */}
            <div className="lg:col-span-5 card-8d-light rounded-2xl border border-[#DED4C8] p-4 space-y-4">
              <div>
                <h2 className="text-sm font-extrabold text-[#1E1916] border-b border-[#EFE8DE] pb-2">
                  Hôm nay, 15/01/2025
                </h2>
                <div className="mt-3 space-y-3 relative pl-2">
                  {memoryEntries.slice(0, 4).map((entry) => (
                    <div
                      key={entry.id}
                      className={`p-3 rounded-xl border transition-colors ${
                        entry.isRevoked
                          ? 'bg-[#F5F5F4] border-[#D6D3D1] opacity-60 line-through'
                          : 'bg-[#FAF6F0] border-[#E5DEC9]'
                      }`}
                    >
                      <div className="flex items-center justify-between text-[11px] font-mono text-[#6E5D53]">
                        <span>{entry.timestamp.replace('Hôm nay, ', '')}</span>
                        <span className="font-bold text-[#D9382C]">
                          {entry.version}
                        </span>
                      </div>
                      <div className="text-xs sm:text-sm font-bold text-[#1E1916] mt-0.5">
                        {entry.title}
                      </div>
                      <p className="text-xs text-[#4A3B34] mt-1 leading-relaxed">
                        {entry.content}
                      </p>
                      <div className="mt-2 flex items-center justify-between text-[11px]">
                        <span className="font-mono text-[#6E5D53]">
                          {entry.actor}
                        </span>
                        <button
                          type="button"
                          onClick={() => onToggleRevokeMemory(entry.id)}
                          className="text-[#B91C1C] hover:underline inline-flex items-center gap-1 font-semibold"
                        >
                          <RotateCcw className="w-3 h-3" />
                          <span>
                            {entry.isRevoked ? 'Khôi phục' : 'Thu hồi'}
                          </span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h2 className="text-sm font-extrabold text-[#1E1916] border-b border-[#EFE8DE] pb-2">
                  Hôm qua, 14/01/2025
                </h2>
                <div className="mt-3 space-y-2.5 pl-2">
                  <div className="p-3 rounded-xl bg-[#FAF6F0] border border-[#E5DEC9]">
                    <div className="text-[11px] font-mono text-[#6E5D53]">10:21</div>
                    <div className="text-xs font-bold text-[#1E1916]">
                      Tìm tài liệu &ldquo;ISO 13934-1&rdquo;
                    </div>
                    <div className="text-xs text-[#4A3B34]">
                      4 kết quả từ Thư viện Tri thức
                    </div>
                  </div>
                  <div className="p-3 rounded-xl bg-[#FAF6F0] border border-[#E5DEC9]">
                    <div className="text-[11px] font-mono text-[#6E5D53]">11:05</div>
                    <div className="text-xs font-bold text-[#1E1916]">
                      Cập nhật ghi chú tri thức
                    </div>
                    <div className="text-xs text-[#4A3B34]">
                      Thêm hướng dẫn thử nghiệm trên máy 03026A
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* RIGHT 7 COLS: 3 STACKED CARDS (Ghi chú tri thức + Phiên bản chỉnh sửa + Trạng thái đồng bộ) */}
            <div className="lg:col-span-7 space-y-4">
              {/* CARD 1: Ghi chú tri thức (03026A) */}
              <div className="card-8d-light rounded-2xl border border-[#DED4C8] p-4 space-y-3">
                <div className="flex items-center justify-between border-b border-[#EFE8DE] pb-2.5">
                  <h2 className="text-sm font-extrabold text-[#1E1916]">
                    Ghi chú tri thức (03026A)
                  </h2>
                  <button
                    type="button"
                    onClick={() =>
                      isEditingNote
                        ? handleSaveKnowledgeNote()
                        : setIsEditingNote(true)
                    }
                    className="px-3 py-1 rounded-lg card-8d-interactive text-[#1E1916] border border-[#C9BBAE] text-xs font-bold inline-flex items-center gap-1"
                  >
                    <Edit3 className="w-3.5 h-3.5 text-[#D9382C]" />
                    <span>{isEditingNote ? 'Lưu ghi chú' : 'Sửa'}</span>
                  </button>
                </div>

                <div className="p-3.5 rounded-xl surface-8d-warm border border-[#E5DEC9] space-y-1.5">
                  <div className="text-xs font-extrabold text-[#1E1916]">
                    Máy thử độ bền kéo vải 03026A:
                  </div>
                  {isEditingNote ? (
                    <textarea
                      rows={3}
                      value={knowledgeNoteText}
                      onChange={(e) => setKnowledgeNoteText(e.target.value)}
                      aria-label="Nội dung ghi chú tri thức"
                      className="w-full p-2 rounded-lg bg-white border border-[#C9BBAE] text-xs text-[#1E1916] shadow-inner"
                    />
                  ) : (
                    <div className="text-xs text-[#3B302B] whitespace-pre-line leading-relaxed">
                      {knowledgeNoteText}
                    </div>
                  )}
                </div>
              </div>

              {/* CARD 2: Phiên bản chỉnh sửa */}
              <div className="card-8d-light rounded-2xl border border-[#DED4C8] p-4 space-y-3">
                <h2 className="text-sm font-extrabold text-[#1E1916] border-b border-[#EFE8DE] pb-2">
                  Phiên bản chỉnh sửa
                </h2>
                <div className="rounded-xl border border-[#DED4C8] overflow-hidden">
                  <table className="w-full text-xs border-collapse">
                    <thead>
                      <tr className="bg-[#EFE8DE] text-[#4A3B34] border-b border-[#DED4C8]">
                        <th className="py-2 px-3 text-left font-bold">Phiên bản</th>
                        <th className="py-2 px-3 text-left font-bold">
                          Nội dung thay đổi
                        </th>
                        <th className="py-2 px-3 text-left font-bold">Thời gian</th>
                        <th className="py-2 px-3 text-left font-bold">
                          Người chỉnh sửa
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#EFE8DE]">
                      <tr>
                        <td className="py-2.5 px-3 font-mono font-bold text-[#D9382C]">
                          v1.2
                        </td>
                        <td className="py-2.5 px-3 font-semibold text-[#1E1916]">
                          Cập nhật mô tả SEO (148 ký tự)
                        </td>
                        <td className="py-2.5 px-3 font-mono text-[#574B43]">
                          15/01 14:45
                        </td>
                        <td className="py-2.5 px-3 text-[#1E1916]">Minh Anh</td>
                      </tr>
                      <tr>
                        <td className="py-2.5 px-3 font-mono font-bold text-[#4A3B34]">
                          v1.1
                        </td>
                        <td className="py-2.5 px-3 text-[#1E1916]">
                          Bổ sung thông số kỹ thuật
                        </td>
                        <td className="py-2.5 px-3 font-mono text-[#574B43]">
                          15/01 14:32
                        </td>
                        <td className="py-2.5 px-3 text-[#1E1916]">Minh Anh</td>
                      </tr>
                      <tr>
                        <td className="py-2.5 px-3 font-mono font-bold text-[#4A3B34]">
                          v1.0
                        </td>
                        <td className="py-2.5 px-3 text-[#1E1916]">
                          Tạo mới sản phẩm
                        </td>
                        <td className="py-2.5 px-3 font-mono text-[#574B43]">
                          15/01 10:08
                        </td>
                        <td className="py-2.5 px-3 text-[#1E1916]">Minh Anh</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* CARD 3: Trạng thái đồng bộ (Honest Multi-System Sync Status Table) */}
              <div className="card-8d-light rounded-2xl border border-[#DED4C8] p-4 space-y-3">
                <div className="flex items-center justify-between border-b border-[#EFE8DE] pb-2">
                  <h2 className="text-sm font-extrabold text-[#1E1916]">
                    Trạng thái đồng bộ
                  </h2>
                  <span className="text-[11px] font-mono text-[#6E5D53]">
                    Hiển thị tách biệt từng dịch vụ (Không dùng 1 chấm xanh giả lập)
                  </span>
                </div>

                <div className="rounded-xl border border-[#DED4C8] overflow-hidden">
                  <table className="w-full text-xs border-collapse">
                    <thead>
                      <tr className="bg-[#EFE8DE] text-[#4A3B34] border-b border-[#DED4C8]">
                        <th className="py-2 px-3 text-left font-bold">Hệ thống</th>
                        <th className="py-2 px-3 text-left font-bold">Dữ liệu</th>
                        <th className="py-2 px-3 text-left font-bold">Trạng thái</th>
                        <th className="py-2 px-3 text-left font-bold">Thời gian</th>
                        <th className="py-2 px-3 text-right font-bold">Thao tác</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#EFE8DE]">
                      <tr>
                        <td className="py-2.5 px-3 font-bold text-[#1E1916]">
                          Haravan (nháp)
                        </td>
                        <td className="py-2.5 px-3 font-mono text-[#4A3B34]">
                          SKU 03026A
                        </td>
                        <td className="py-2.5 px-3">
                          <span className="inline-flex items-center gap-1 font-bold text-[#D97706]">
                            <Clock className="w-3.5 h-3.5" />
                            <span>Đang chờ</span>
                          </span>
                        </td>
                        <td className="py-2.5 px-3 font-mono text-[#574B43]">
                          15/01 15:18
                        </td>
                        <td className="py-2.5 px-3 text-right text-[#6E5D53]">—</td>
                      </tr>

                      <tr>
                        <td className="py-2.5 px-3 font-bold text-[#1E1916]">
                          CSDL nội bộ
                        </td>
                        <td className="py-2.5 px-3 text-[#4A3B34]">
                          Thông tin sản phẩm
                        </td>
                        <td className="py-2.5 px-3">
                          <span className="inline-flex items-center gap-1 font-bold text-[#16A34A]">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Đã đồng bộ</span>
                          </span>
                        </td>
                        <td className="py-2.5 px-3 font-mono text-[#574B43]">
                          15/01 15:20
                        </td>
                        <td className="py-2.5 px-3 text-right text-[#6E5D53]">—</td>
                      </tr>

                      <tr>
                        <td className="py-2.5 px-3 font-bold text-[#1E1916]">
                          Cloud Backup
                        </td>
                        <td className="py-2.5 px-3 text-[#4A3B34]">
                          Hồ sơ &amp; phiên bản
                        </td>
                        <td className="py-2.5 px-3">
                          {cloudBackupState === 'error' ? (
                            <span className="inline-flex items-center gap-1 font-bold text-[#DC2626]">
                              <XCircle className="w-3.5 h-3.5" />
                              <span>Lỗi đồng bộ</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 font-bold text-[#16A34A]">
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              <span>Đã đồng bộ</span>
                            </span>
                          )}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-[#574B43]">
                          15/01 15:21
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <button
                            type="button"
                            onClick={() =>
                              setCloudBackupState((s) =>
                                s === 'error' ? 'synced' : 'error'
                              )
                            }
                            className="px-2.5 py-1 rounded-lg bg-[#FAF6F0] hover:bg-[#EFE8DE] text-[#1E1916] border border-[#C9BBAE] font-bold text-xs"
                          >
                            Thử lại
                          </button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
