import React, { useState } from 'react';
import {
  AgentStationMeta,
  DepartmentId,
  ProductRecord,
} from '../types/bisTypes';
import { AGENT_STATIONS } from '../data/mockBisData';
import { AgentRobotAvatar } from './AgentRobotAvatar';
import { SceneBoundary } from './SceneBoundary';
import { AgentOffice3DCanvas } from './AgentOffice3DCanvas';
import { RobotEyeStyle, RobotFinishPreset } from '../utils/agentOfficeSim';
import {
  Gamepad2,
  Sparkles,
  ListChecks,
  Minimize2,
  Maximize2,
  EyeOff,
  ArrowRight,
  CheckCircle2,
  Clock,
  PauseCircle,
  FileText,
  Image as ImageIcon,
  FlaskConical,
  Megaphone,
  BookOpen,
  Settings,
  Users,
  Check,
} from 'lucide-react';

interface CommandCenterViewProps {
  products: ProductRecord[];
  activeProduct: ProductRecord;
  reduceMotion: boolean;
  eyeStyle: RobotEyeStyle;
  finishPreset: RobotFinishPreset;
  onChangeEyeStyle: (style: RobotEyeStyle) => void;
  onChangeFinishPreset: (preset: RobotFinishPreset) => void;
  onToggleReduceMotion: () => void;
  onSelectProductAndNavigate: (sku: string, dept: DepartmentId) => void;
  onNavigateDepartment: (dept: DepartmentId) => void;
}

export const CommandCenterView: React.FC<CommandCenterViewProps> = ({
  activeProduct,
  reduceMotion,
  eyeStyle,
  finishPreset,
  onChangeEyeStyle,
  onChangeFinishPreset,
  onToggleReduceMotion,
  onSelectProductAndNavigate,
  onNavigateDepartment,
}) => {
  const [viewMode, setViewMode] = useState<'3d_studio_room' | '3d_game_office' | 'compact_tasks'>('3d_studio_room');
  const [compactFloor, setCompactFloor] = useState<boolean>(false);
  const [selectedStation, setSelectedStation] = useState<AgentStationMeta>(AGENT_STATIONS[2]);
  const [activeSpeechToast, setActiveSpeechToast] = useState<string>(
    `Phiên làm việc ${activeProduct.sku}: Robot chỉ huy BIS đang điều phối 5 bộ phận quanh bàn họp trung tâm.`
  );

  // Current Meeting Cards (Exact match to Image 1 right-top panel)
  const currentMeetingCards = [
    {
      id: 'meet-1',
      title: `Cập nhật hồ sơ kỹ thuật ${activeProduct.sku} (v1.2)`,
      subtitle: `Nguồn: spec_${activeProduct.sku}.pdf · 12 trang`,
      status: 'running' as const,
      statusText: 'Đang chạy',
      dept: 'technical' as DepartmentId,
      iconType: 'pdf' as const,
    },
    {
      id: 'meet-2',
      title: `Duyệt ảnh sản phẩm bộ sưu tập ${activeProduct.sku}`,
      subtitle: 'Bằng chứng: studio_BIS · 7 ảnh',
      status: 'review' as const,
      statusText: 'Chờ duyệt',
      dept: 'imagestudio' as DepartmentId,
      iconType: 'image' as const,
    },
    {
      id: 'meet-3',
      title: 'Hoàn thiện nội dung sản phẩm (vi/EN)',
      subtitle: 'Bằng chứng: draft_v3.docx · 2.8 KB',
      status: 'idle' as const,
      statusText: 'Nhàn rỗi',
      dept: 'marketing' as DepartmentId,
      iconType: 'doc' as const,
    },
  ];

  // Session Timeline Steps (Exact match to Image 1 right-bottom panel)
  const sessionTimeline = [
    {
      time: '10:24',
      title: 'Nhập nguồn',
      detail: `Đã tải spec_${activeProduct.sku}.pdf (12 trang)`,
      state: 'done' as const,
      dept: 'technical' as DepartmentId,
    },
    {
      time: '10:31',
      title: 'Phân tích & tạo nội dung',
      detail: 'Đã tạo bản nháp mô tả sản phẩm (vi/EN)',
      state: 'done' as const,
      dept: 'marketing' as DepartmentId,
    },
    {
      time: '10:37',
      title: 'Xử lý ảnh tại Image Studio',
      detail: 'Đang chụp và xử lý 7 ảnh sản phẩm...',
      state: 'active' as const,
      dept: 'imagestudio' as DepartmentId,
    },
    {
      time: '10:50',
      title: 'Kiểm duyệt nội dung & ảnh',
      detail: 'Chờ duyệt bởi quản lý',
      state: 'pending' as const,
      dept: 'operations' as DepartmentId,
    },
    {
      time: '11:05',
      title: 'Xuất bản',
      detail: 'Chuẩn bị xuất lên cửa hàng (Bản nháp Haravan)',
      state: 'pending' as const,
      dept: 'operations' as DepartmentId,
    },
  ];

  // Interactive 3D Room Pod Hotspots aligned directly over the 5 stations in the cropped 3D Command Room
  const roomPodHotspots: {
    id: DepartmentId;
    title: string;
    subtitle: string;
    Icon: React.FC<{ className?: string }>;
    posClass: string;
    speech: string;
  }[] = [
    {
      id: 'technical',
      title: 'Technical',
      subtitle: 'Hồ sơ kỹ thuật · Spec · PDF',
      Icon: FlaskConical,
      posClass: 'top-[10%] left-[12%] w-[32%] h-[22%]',
      speech: `Technical Robot: Đã bóc tách bảng thông số trang 16 cho mã ${activeProduct.sku} (0.5 – 50 kN, ±0.5%).`,
    },
    {
      id: 'marketing',
      title: 'Marketing',
      subtitle: 'Nội dung sản phẩm · Truyền thông',
      Icon: Megaphone,
      posClass: 'top-[10%] right-[8%] w-[33%] h-[22%]',
      speech: `Marketing Robot: Đã biên tập mô tả song ngữ VI/EN và tối ưu SEO 148/160 ký tự cho ${activeProduct.sku}.`,
    },
    {
      id: 'knowledge',
      title: 'Knowledge',
      subtitle: 'Thư viện · Tri thức · Lưu trữ',
      Icon: BookOpen,
      posClass: 'top-[40%] left-[3%] w-[26%] h-[25%]',
      speech: 'Knowledge Robot: Đã đối chiếu tiêu chuẩn ISO 13934-1 (Trang 5, 8, 11) và ASTM D5034.',
    },
    {
      id: 'imagestudio',
      title: 'Image Studio',
      subtitle: 'Chụp · Xử lý · Ảnh sản phẩm',
      Icon: ImageIcon,
      posClass: 'top-[39%] right-[3%] w-[28%] h-[26%]',
      speech: `Image Studio Robot: Đang xử lý ảnh ${activeProduct.sku} trong buồng chụp BIS và đối chiếu chuẩn Benchmark.`,
    },
    {
      id: 'operations',
      title: 'Operations',
      subtitle: 'Quản lý tác vụ · Kiểm duyệt · Xuất bản',
      Icon: Settings,
      posClass: 'bottom-[9%] left-[29%] w-[42%] h-[24%]',
      speech: `Operations Robot: Đã kiểm tra 5 điều kiện duyệt & phát hiện mã tương tự 03026 (92%). Sẵn sàng tạo nháp Haravan!`,
    },
  ];

  return (
    <div className="p-3 lg:p-5 space-y-4 max-w-[1540px] mx-auto">
      {/* Top Control Strip: Switch between Live 3D Interactive Office (Walk/Run/Jump/Talk), 2D Concept Art, and Compact Mode */}
      <div className="flex flex-wrap items-center justify-between gap-3 card-8d-dark border border-[#4A3B34] rounded-2xl px-4 py-2.5">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="font-bold text-[#F5EFE6]">
            PHÒNG ĐIỀU HÀNH ĐA TÁC TỬ 3D
          </span>
          <span className="text-[#9C8D84]" aria-hidden="true">·</span>
          <span className="font-mono text-[#E03B2F] font-semibold">
            G:\My Drive\BIS_AI_PROJECT
          </span>
          <span className="text-[#9C8D84]" aria-hidden="true">·</span>
          <span className="font-mono text-[#F59E0B]">Dữ liệu minh họa</span>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div
            role="group"
            aria-label="Chế độ hiển thị Trung tâm điều hành"
            className="inline-flex items-center card-8d-dark-recessed p-1 rounded-xl border border-[#3E322C]"
          >
            <button
              type="button"
              onClick={() => setViewMode('3d_game_office')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
                viewMode === '3d_game_office'
                  ? 'btn-8d-crimson text-white'
                  : 'text-[#B8AAA0] hover:text-white'
              }`}
            >
              <Gamepad2 className="w-3.5 h-3.5" />
              <span>Phòng 3D Tương tác (Đi lại · Chạy nhảy · Trò chuyện)</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode('3d_studio_room')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
                viewMode === '3d_studio_room'
                  ? 'btn-8d-crimson text-white'
                  : 'text-[#B8AAA0] hover:text-white'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Phối cảnh 2D Mẫu (Bàn họp 03026A)</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode('compact_tasks')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
                viewMode === 'compact_tasks'
                  ? 'btn-8d-crimson text-white'
                  : 'text-[#B8AAA0] hover:text-white'
              }`}
            >
              <ListChecks className="w-3.5 h-3.5" />
              <span>Danh sách Tác vụ gọn</span>
            </button>
          </div>

          <button
            type="button"
            onClick={() => setCompactFloor((prev) => !prev)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium bg-gradient-to-b from-[#2A211D] to-[#1A1412] text-[#D8CEC5] border border-[#463831] shadow-[inset_0_1px_0_rgba(255,248,235,0.1),0_3px_8px_rgba(0,0,0,0.4)] hover:text-white transition-all"
          >
            {compactFloor ? (
              <>
                <Maximize2 className="w-3.5 h-3.5 text-[#F59E0B]" />
                <span>Mở rộng Không gian 3D</span>
              </>
            ) : (
              <>
                <Minimize2 className="w-3.5 h-3.5" />
                <span>Thu gọn để làm nhanh</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={onToggleReduceMotion}
            aria-pressed={reduceMotion}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium border transition-all shadow-[inset_0_1px_0_rgba(255,248,235,0.1),0_3px_8px_rgba(0,0,0,0.4)] ${
              reduceMotion
                ? 'bg-gradient-to-b from-[#3A2D26] to-[#261D18] text-[#FBBF24] border-[#F59E0B]/60'
                : 'bg-gradient-to-b from-[#2A211D] to-[#1A1412] text-[#D8CEC5] border-[#463831] hover:text-white'
            }`}
          >
            <EyeOff className="w-3.5 h-3.5" />
            <span>{reduceMotion ? 'Đã bật Giảm chuyển động' : 'Giảm chuyển động'}</span>
          </button>
        </div>
      </div>

      {/* MAIN GRID: LEFT 8 COLS (3D COMMAND ROOM / 3D GAME) + RIGHT 4 COLS (CUỘC HỌP HIỆN TẠI & TIẾN TRÌNH PHIÊN LÀM VIỆC) */}
      {compactFloor ? (
        <div className="card-8d-dark border border-[#4A3B34] rounded-2xl p-4">
          <div className="text-xs font-semibold text-[#F5EFE6] mb-3">
            Thanh Điều hướng Trạm Agent Thu gọn (Bấm chọn để mở ngay từng nghiệp vụ)
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {AGENT_STATIONS.map((station) => (
              <button
                key={station.id}
                type="button"
                onClick={() => onNavigateDepartment(station.id)}
                className="p-3 rounded-xl card-8d-dark-recessed border border-[#433630] hover:border-[#D9382C] text-left flex items-center gap-2.5 transition-all"
              >
                <AgentRobotAvatar
                  department={station.id}
                  size="sm"
                  isActive={activeProduct.assignedAgent === station.id}
                  reduceMotion={reduceMotion}
                  eyeStyle={eyeStyle}
                  finishPreset={finishPreset}
                />
                <div className="min-w-0">
                  <div className="text-xs font-bold text-[#F5EFE6] truncate">
                    {station.roleTitle}
                  </div>
                  <div className="text-[10px] font-mono text-[#B8AAA0] truncate">
                    {station.agentName}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
          {/* LEFT 8 COLS: 3D COMMAND ROOM OR INTERACTIVE 3D GAME CANVAS */}
          <div className="lg:col-span-8 flex flex-col gap-4">
            {viewMode === '3d_studio_room' ? (
              <div className="relative rounded-2xl overflow-hidden border border-[#5C473C] frame-8d-stage flex flex-col justify-between">
                {/* Cleanly Cropped Central 3D BIS Command Room Scene + Interactive Hotspots */}
                <div className="relative w-full aspect-[16/12] min-h-[460px] overflow-hidden select-none">
                  <img
                    src="assets/aistudio/image_bff76a11.png"
                    alt="Phòng điều hành 3D BIS TEXTILE AI"
                    className="absolute max-w-none pointer-events-none"
                    style={{
                      left: '-20.6%',
                      top: '-9.9%',
                      width: '165%',
                      height: '130%',
                    }}
                  />

                  {/* Top Interactive Speech & Live Action Bar inside the 3D Room */}
                  <div className="relative z-10 p-3.5 flex flex-wrap items-center justify-between gap-2">
                    <div className="bg-[#1C1613]/92 border border-[#6E5648] rounded-full px-3.5 py-1.5 text-xs text-[#FAF6F0] flex items-center gap-2 shadow-[0_8px_24px_rgba(0,0,0,0.65)]">
                      <span className="w-2 h-2 rounded-full bg-[#E03B2F]" />
                      <span className="font-semibold">{activeSpeechToast}</span>
                    </div>

                    <button
                      type="button"
                      onClick={() => setViewMode('3d_game_office')}
                      className="px-3.5 py-1.5 rounded-full btn-8d-crimson text-white text-xs font-bold flex items-center gap-1.5 transition-all"
                    >
                      <Gamepad2 className="w-3.5 h-3.5" />
                      <span>Chơi Game 3D (WASD)</span>
                    </button>
                  </div>

                  {/* Interactive Hotspot Zones directly aligned over the 5 rendered 3D department stations */}
                  {roomPodHotspots.map((pod) => {
                    const isCurrent = activeProduct.assignedAgent === pod.id;
                    return (
                      <button
                        key={pod.id}
                        type="button"
                        aria-label={`Mở khu vực ${pod.title}: ${pod.subtitle}`}
                        onClick={() => {
                          setActiveSpeechToast(pod.speech);
                          onNavigateDepartment(pod.id);
                        }}
                        onMouseEnter={() => setActiveSpeechToast(pod.speech)}
                        className={`hidden md:flex absolute ${pod.posClass} rounded-2xl transition-all items-start justify-end p-2 group cursor-pointer ${
                          isCurrent
                            ? 'ring-2 ring-[#E03B2F]/80 bg-[#E03B2F]/5'
                            : 'hover:ring-2 hover:ring-[#FAF6F0]/70 hover:bg-white/5'
                        }`}
                      >
                        <span className="px-2 py-0.5 rounded-full bg-[#1C1613]/90 border border-[#6E5648] text-[10px] font-bold text-[#FAF6F0] opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 shadow-md">
                          <span>Mở {pod.title}</span>
                          <ArrowRight className="w-2.5 h-2.5 text-[#E03B2F]" />
                        </span>
                      </button>
                    );
                  })}

                  {/* Central Oval Conference Table Interactive Step Hotspots ("Quy trình phiên 03026A") */}
                  <div className="hidden md:flex absolute top-[50%] left-[50%] -translate-x-1/2 -translate-y-1/2 w-[28%] h-[14%] rounded-full items-center justify-around px-3">
                    {[
                      { id: 'technical' as DepartmentId, label: 'Nguồn' },
                      { id: 'marketing' as DepartmentId, label: 'Nội dung' },
                      { id: 'imagestudio' as DepartmentId, label: 'Ảnh' },
                      { id: 'operations' as DepartmentId, label: 'Duyệt' },
                    ].map((st) => (
                      <button
                        key={st.id}
                        type="button"
                        title={`Mở bước ${st.label}`}
                        onClick={() => onNavigateDepartment(st.id)}
                        className="w-8 h-8 rounded-full hover:ring-2 hover:ring-[#E03B2F] hover:bg-[#E03B2F]/20 transition-all cursor-pointer"
                      >
                        <span className="sr-only">{st.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Bottom Quick Bar inside the 3D Room for Mobile & Fast Switching */}
                <div className="relative z-10 p-3 bg-gradient-to-b from-[#1F1815] to-[#15100E] border-t border-[#4A3B34] flex flex-wrap items-center justify-between gap-2">
                  <span className="text-xs text-[#D5C7BC]">
                    Bấm trực tiếp vào trạm Robot trên hình 3D hoặc chọn nhanh bộ phận:
                  </span>
                  <div className="flex flex-wrap items-center gap-1.5">
                    {AGENT_STATIONS.map((st) => (
                      <button
                        key={st.id}
                        type="button"
                        onClick={() => onNavigateDepartment(st.id)}
                        className="px-2.5 py-1 rounded-lg bg-gradient-to-b from-[#312722] to-[#221A17] hover:from-[#E03B2F] hover:to-[#B82D22] text-xs font-semibold text-[#FAF6F0] border border-[#4E3E36] shadow-[inset_0_1px_0_rgba(255,248,235,0.1),0_2px_6px_rgba(0,0,0,0.4)] transition-all"
                      >
                        {st.roleTitle}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : viewMode === '3d_game_office' ? (
              <SceneBoundary>
              <AgentOffice3DCanvas
                activeProduct={activeProduct}
                reduceMotion={reduceMotion}
                eyeStyle={eyeStyle}
                finishPreset={finishPreset}
                onChangeEyeStyle={onChangeEyeStyle}
                onChangeFinishPreset={onChangeFinishPreset}
                onSelectDepartment={onNavigateDepartment}
              />
              </SceneBoundary>
            ) : (
              /* Compact Task List Mode */
              <div className="card-8d-dark border border-[#4A3B34] rounded-2xl p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-[#3E322C] pb-3">
                  <div>
                    <h2 className="text-base font-bold text-[#FAF6F0]">
                      Danh sách Tác vụ Nghiệp vụ theo Phiên làm việc {activeProduct.sku}
                    </h2>
                    <p className="text-xs text-[#B8AAA0]">
                      Chế độ danh sách gọn giúp chuyển nhanh vào 6 tab nghiệp vụ chuẩn.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setViewMode('3d_studio_room')}
                    className="px-3 py-1.5 rounded-lg bg-gradient-to-b from-[#352A24] to-[#241C18] text-xs font-semibold text-[#FAF6F0] border border-[#524139] shadow-[inset_0_1px_0_rgba(255,248,235,0.12),0_3px_8px_rgba(0,0,0,0.4)]"
                  >
                    Quay lại Phòng 3D
                  </button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {AGENT_STATIONS.map((station) => (
                    <div
                      key={station.id}
                      className="p-3.5 rounded-xl card-8d-dark-recessed border border-[#433630] flex items-center justify-between gap-3"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <AgentRobotAvatar
                          department={station.id}
                          size="sm"
                          isActive={selectedStation.id === station.id}
                          reduceMotion={reduceMotion}
                        />
                        <div className="min-w-0">
                          <div className="text-sm font-bold text-[#FAF6F0] truncate">
                            {station.roleTitle}
                          </div>
                          <div className="text-xs text-[#B8AAA0] truncate">
                            {station.activeTaskLabel}
                          </div>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => onNavigateDepartment(station.id)}
                        className="px-3 py-1.5 rounded-lg btn-8d-crimson text-white text-xs font-semibold shrink-0"
                      >
                        Mở tab
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* RIGHT 4 COLS: EXACT STORYBOARD MATCH ("Cuộc họp hiện tại" & "Tiến trình phiên làm việc") */}
          <div className="lg:col-span-4 flex flex-col gap-4">
            {/* CARD 1: Cuộc họp hiện tại */}
            <div className="card-8d-dark border border-[#4E3E36] rounded-2xl p-4">
              <div className="flex items-center gap-2.5 pb-3 border-b border-[#3E322C]">
                <Users className="w-5 h-5 text-[#FDE68A]" />
                <h2 className="text-base font-bold text-[#FAF6F0]">
                  Cuộc họp hiện tại
                </h2>
              </div>

              <div className="mt-3.5 space-y-3">
                {currentMeetingCards.map((card) => (
                  <button
                    key={card.id}
                    type="button"
                    onClick={() => onSelectProductAndNavigate(activeProduct.sku, card.dept)}
                    className="w-full text-left p-3.5 rounded-xl card-8d-interactive text-[#1F1916] border border-[#E2D6C8] flex items-center justify-between gap-3 cursor-pointer"
                  >
                    <div className="flex items-start gap-3 min-w-0">
                      <div className="w-9 h-9 rounded-lg bg-gradient-to-b from-[#FCEAE6] to-[#F4D3CC] border border-[#E6B0A6] shadow-[inset_0_1px_0_#FFFFFF,0_2px_5px_rgba(185,28,28,0.12)] flex items-center justify-center shrink-0 mt-0.5">
                        {card.iconType === 'pdf' ? (
                          <span className="text-[10px] font-mono font-extrabold text-[#D9382C]">
                            PDF
                          </span>
                        ) : card.iconType === 'image' ? (
                          <ImageIcon className="w-4 h-4 text-[#A64B3B]" />
                        ) : (
                          <FileText className="w-4 h-4 text-[#6E5A4F]" />
                        )}
                      </div>
                      <div className="min-w-0">
                        <div className="text-xs sm:text-sm font-bold text-[#1C1613] leading-snug">
                          {card.title}
                        </div>
                        <div className="text-[11px] text-[#6E5D53] mt-0.5 truncate">
                          {card.subtitle}
                        </div>
                      </div>
                    </div>

                    {/* Status Badge */}
                    {card.status === 'running' && (
                      <span className="px-2.5 py-1 rounded-full bg-gradient-to-b from-[#E6FCEE] to-[#CFF7DE] text-[#15803D] border border-[#86EFAC] shadow-[inset_0_1px_0_#FFFFFF,0_2px_4px_rgba(22,163,74,0.14)] text-[11px] font-semibold inline-flex items-center gap-1 shrink-0">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>{card.statusText}</span>
                      </span>
                    )}
                    {card.status === 'review' && (
                      <span className="px-2.5 py-1 rounded-full bg-gradient-to-b from-[#FFF8DB] to-[#FDE68A] text-[#B45309] border border-[#FCD34D] shadow-[inset_0_1px_0_#FFFFFF,0_2px_4px_rgba(217,119,6,0.14)] text-[11px] font-semibold inline-flex items-center gap-1 shrink-0">
                        <Clock className="w-3 h-3" />
                        <span>{card.statusText}</span>
                      </span>
                    )}
                    {card.status === 'idle' && (
                      <span className="px-2.5 py-1 rounded-full bg-gradient-to-b from-[#EFECE6] to-[#E2DDD4] text-[#574B43] border border-[#D0C7BC] shadow-[inset_0_1px_0_#FFFFFF,0_2px_4px_rgba(0,0,0,0.06)] text-[11px] font-semibold inline-flex items-center gap-1 shrink-0">
                        <PauseCircle className="w-3 h-3" />
                        <span>{card.statusText}</span>
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* CARD 2: Tiến trình phiên làm việc */}
            <div className="card-8d-dark border border-[#4E3E36] rounded-2xl p-4 flex-1 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2.5 pb-3 border-b border-[#3E322C]">
                  <ListChecks className="w-5 h-5 text-[#FDE68A]" />
                  <h2 className="text-base font-bold text-[#FAF6F0]">
                    Tiến trình phiên làm việc
                  </h2>
                </div>

                <div className="mt-4 relative pl-3 space-y-3">
                  {/* Vertical connecting line */}
                  <div
                    className="absolute left-[21px] top-3 bottom-4 w-0.5 bg-gradient-to-b from-[#D9382C] via-[#785A4B] to-[#3E322C]"
                    aria-hidden="true"
                  />

                  {sessionTimeline.map((item, index) => {
                    const isDone = item.state === 'done';
                    const isActive = item.state === 'active';

                    return (
                      <button
                        key={index}
                        type="button"
                        onClick={() => onNavigateDepartment(item.dept)}
                        className={`w-full text-left relative flex items-start gap-3 p-2.5 rounded-xl transition-all cursor-pointer ${
                          isActive
                            ? 'bg-gradient-to-r from-[#462621] via-[#38201C] to-[#2B1916] border border-[#A8483E] shadow-[inset_0_1px_0_rgba(255,220,210,0.16),0_8px_20px_-4px_rgba(0,0,0,0.55)]'
                            : 'hover:bg-[#2C2420]/80 hover:shadow-[inset_0_1px_0_rgba(255,248,235,0.06)]'
                        }`}
                      >
                        {/* Step Node Circle */}
                        <div className="relative z-10 mt-0.5 shrink-0">
                          {isDone ? (
                            <div className="w-5 h-5 rounded-full btn-8d-crimson text-white flex items-center justify-center">
                              <Check className="w-3 h-3 stroke-[3]" />
                            </div>
                          ) : isActive ? (
                            <div className="w-5 h-5 rounded-full bg-[#D9382C]/35 border-2 border-[#EF4444] shadow-[0_0_10px_rgba(239,68,68,0.5)] flex items-center justify-center">
                              <div className="w-2 h-2 rounded-full bg-white" />
                            </div>
                          ) : (
                            <div className="w-5 h-5 rounded-full bg-[#1E1815] border-2 border-[#78665C] shadow-inner" />
                          )}
                        </div>

                        {/* Time & Description */}
                        <div className="flex items-baseline gap-2.5 min-w-0 flex-1">
                          <span className="text-xs font-mono text-[#B8AAA0] shrink-0">
                            {item.time}
                          </span>
                          <div className="min-w-0">
                            <div className="text-xs sm:text-sm font-bold text-[#FAF6F0]">
                              {item.title}
                            </div>
                            <div className="text-xs text-[#C4B5AA] mt-0.5 truncate">
                              {item.detail}
                            </div>
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
