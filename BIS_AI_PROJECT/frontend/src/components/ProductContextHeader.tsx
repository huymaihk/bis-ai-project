import React from 'react';
import {
  DepartmentId,
  ProductRecord,
  VerificationStatus,
} from '../types/bisTypes';
import { AgentRobotAvatar } from './AgentRobotAvatar';
import { AuthenticatedStaffUser } from './LoginView';
import {
  Briefcase,
  Bell,
  User,
  AlertTriangle,
  CheckCircle2,
  Clock,
  SlidersHorizontal,
  Share2,
  LogOut,
} from 'lucide-react';

interface ProductContextHeaderProps {
  products: ProductRecord[];
  activeProduct: ProductRecord;
  activeDepartment: DepartmentId;
  currentUser: AuthenticatedStaffUser;
  onSelectProduct: (sku: string) => void;
  onNavigateDepartment: (dept: DepartmentId) => void;
  onOpenDesignRationale: () => void;
  onLogout: () => void;
}

export function renderStatusLabel(status: VerificationStatus) {
  switch (status) {
    case 'approved':
      return {
        text: 'Đã duyệt',
        colorClass: 'text-[#4ADE80]',
        Icon: CheckCircle2,
      };
    case 'review':
      return {
        text: 'Đang biên tập',
        colorClass: 'text-[#FBBF24]',
        Icon: Clock,
      };
    case 'error':
      return {
        text: 'Lỗi cần xử lý',
        colorClass: 'text-[#F87171]',
        Icon: AlertTriangle,
      };
    case 'unchecked':
    default:
      return {
        text: 'Chưa kiểm tra',
        colorClass: 'text-[#94A3B8]',
        Icon: SlidersHorizontal,
      };
  }
}

const DEPT_TITLES: Record<DepartmentId, string> = {
  overview: 'Phòng điều hành',
  technical: 'Kỹ thuật (TECHNICAL)',
  marketing: 'Marketing (MARKETING)',
  imagestudio: 'Image Studio',
  operations: 'Vận hành (OPERATIONS)',
  knowledge: 'Tri thức (KNOWLEDGE)',
  memory: 'Bộ nhớ (MEMORY)',
};

export const ProductContextHeader: React.FC<ProductContextHeaderProps> = ({
  products,
  activeProduct,
  activeDepartment,
  currentUser,
  onSelectProduct,
  onOpenDesignRationale,
  onLogout,
}) => {
  const statusInfo = renderStatusLabel(activeProduct.overallStatus);

  return (
    <header className="bg-gradient-to-b from-[#231C19] via-[#1C1614] to-[#171210] border-b border-[#3E322C] shadow-[inset_0_1px_0_rgba(255,248,235,0.08),0_8px_24px_-6px_rgba(0,0,0,0.65)] px-4 lg:px-6 py-2.5 relative z-10">
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Left: BIS TEXTILE AI · Department | Phiên làm việc · SKU Selector */}
        <div className="flex flex-wrap items-center gap-3 min-w-0">
          <div className="flex items-center gap-2">
            <Share2 className="w-4 h-4 text-[#E03B2F] shrink-0" />
            <span className="text-sm lg:text-base font-extrabold text-[#FAF6F0] tracking-tight whitespace-nowrap">
              BIS TEXTILE AI · {DEPT_TITLES[activeDepartment]}
            </span>
          </div>

          <span className="hidden sm:inline text-[#52433B] font-light text-lg" aria-hidden="true">
            |
          </span>

          {/* Active Session SKU Selector matching Image 1 & Image 2 */}
          <div className="flex items-center gap-2 card-8d-dark-recessed px-3 py-1.5 rounded-xl border border-[#4A3B34]">
            <Briefcase className="w-3.5 h-3.5 text-[#D5C7BC] shrink-0" />
            <label
              htmlFor="sku-context-select"
              className="text-xs text-[#D5C7BC] whitespace-nowrap"
            >
              Phiên làm việc ·
            </label>
            <select
              id="sku-context-select"
              aria-label="Chọn sản phẩm SKU đang xử lý"
              value={activeProduct.sku}
              onChange={(e) => onSelectProduct(e.target.value)}
              className="bg-transparent text-[#FAF6F0] font-mono text-sm font-black focus:outline-none cursor-pointer pr-1"
            >
              {products.map((p) => (
                <option
                  key={p.sku}
                  value={p.sku}
                  className="bg-[#1C1715] text-[#FAF6F0] font-mono"
                >
                  {p.sku} — {p.nameVi}
                </option>
              ))}
            </select>
          </div>

          <span className="hidden xl:inline text-xs text-[#C4B5AA] truncate max-w-[260px]">
            {activeProduct.nameVi} ({activeProduct.standardCode})
          </span>
        </div>

        {/* Right: Status Pill + Robot Assistant + Bell + Operator Profile + Logout */}
        <div className="flex items-center gap-2.5">
          {/* Status Dropdown Pill ("● Đang biên tập") */}
          <div className="px-3 py-1 rounded-full bg-gradient-to-b from-[#332924] to-[#241C19] border border-[#524139] shadow-[inset_0_1px_0_rgba(255,248,235,0.12),0_4px_10px_rgba(0,0,0,0.45)] flex items-center gap-2 text-xs font-semibold text-[#FAF6F0]">
            <span
              className={`w-2 h-2 rounded-full ${
                activeProduct.overallStatus === 'approved'
                  ? 'bg-[#22C55E] shadow-[0_0_6px_#22C55E]'
                  : 'bg-[#E03B2F] shadow-[0_0_6px_#E03B2F]'
              }`}
            />
            <span>{statusInfo.text}</span>
          </div>

          {/* Mini Robot Avatar in Top Bar (Matches Storyboard Header) */}
          <div className="hidden sm:block">
            <AgentRobotAvatar
              department={activeDepartment}
              size="sm"
              isActive={true}
              reduceMotion={true}
            />
          </div>

          {/* Notification Bell with Red Dot */}
          <button
            type="button"
            onClick={onOpenDesignRationale}
            aria-label="Thông báo & Phân tích thiết kế"
            className="relative p-2 rounded-full bg-gradient-to-b from-[#312722] to-[#221B18] hover:from-[#3D312B] hover:to-[#2B221E] text-[#E5D9CE] border border-[#4A3B34] shadow-[inset_0_1px_0_rgba(255,248,235,0.12),0_4px_10px_rgba(0,0,0,0.45)] transition-all"
          >
            <Bell className="w-4 h-4" />
            <span className="w-2 h-2 rounded-full bg-[#E03B2F] absolute top-1.5 right-1.5" />
          </button>

          {/* Operator Profile ("Nguyễn Minh Anh · BIS Textile") */}
          <div className="hidden md:flex items-center gap-2 pl-1 pr-3 py-1 rounded-full bg-gradient-to-b from-[#302621] to-[#211A17] border border-[#4A3B34] shadow-[inset_0_1px_0_rgba(255,248,235,0.12),0_4px_12px_rgba(0,0,0,0.45)]">
            <div className="w-6 h-6 rounded-full bg-gradient-to-b from-[#57463E] to-[#3B2F29] text-[#FAF6F0] flex items-center justify-center shadow-inner">
              <User className="w-3.5 h-3.5" />
            </div>
            <div className="text-left leading-tight">
              <div className="text-[11px] font-bold text-[#FAF6F0]">
                {currentUser.fullName}
              </div>
              <div className="text-[10px] text-[#B8AAA0]">{currentUser.roleLabel}</div>
            </div>
          </div>

          <button
            type="button"
            onClick={onLogout}
            aria-label="Đăng xuất khỏi phiên làm việc"
            className="px-2.5 py-1.5 text-xs font-semibold text-[#FAF6F0] bg-gradient-to-b from-[#332924] to-[#241C19] hover:from-[#E03B2F] hover:to-[#B82D22] border border-[#4A3B34] rounded-lg shadow-[inset_0_1px_0_rgba(255,248,235,0.12),0_4px_10px_rgba(0,0,0,0.4)] transition-all inline-flex items-center gap-1.5 whitespace-nowrap"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Đăng xuất</span>
          </button>
        </div>
      </div>
    </header>
  );
};
