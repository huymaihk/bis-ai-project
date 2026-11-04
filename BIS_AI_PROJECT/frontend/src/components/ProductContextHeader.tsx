import React from 'react';
import {
  DepartmentId,
  ProductRecord,
  VerificationStatus,
} from '../types/bisTypes';
import { AgentRobotAvatar } from './AgentRobotAvatar';
import {
  Briefcase,
  Bell,
  User,
  AlertTriangle,
  CheckCircle2,
  Clock,
  SlidersHorizontal,
  Share2,
} from 'lucide-react';

interface ProductContextHeaderProps {
  products: ProductRecord[];
  activeProduct: ProductRecord;
  activeDepartment: DepartmentId;
  onSelectProduct: (sku: string) => void;
  onNavigateDepartment: (dept: DepartmentId) => void;
  onOpenDesignRationale: () => void;
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
  onSelectProduct,
  onOpenDesignRationale,
}) => {
  const statusInfo = renderStatusLabel(activeProduct.overallStatus);

  return (
    <header className="bg-[#1C1715] border-b border-[#382E29] px-4 lg:px-6 py-2.5">
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
          <div className="flex items-center gap-2 bg-[#261F1C] px-3 py-1 rounded-xl border border-[#433630]">
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

        {/* Right: Status Pill + Robot Assistant + Bell + Nguyễn Minh Anh Profile + Design Rationale */}
        <div className="flex items-center gap-2.5">
          {/* Status Dropdown Pill ("● Đang biên tập") */}
          <div className="px-3 py-1 rounded-full bg-[#2C231F] border border-[#4A3B34] flex items-center gap-2 text-xs font-semibold text-[#FAF6F0]">
            <span
              className={`w-2 h-2 rounded-full ${
                activeProduct.overallStatus === 'approved'
                  ? 'bg-[#22C55E]'
                  : 'bg-[#E03B2F]'
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
            className="relative p-2 rounded-full bg-[#261F1C] hover:bg-[#332924] text-[#E5D9CE] border border-[#3E322C]"
          >
            <Bell className="w-4 h-4" />
            <span className="w-2 h-2 rounded-full bg-[#E03B2F] absolute top-1.5 right-1.5" />
          </button>

          {/* Operator Profile ("Nguyễn Minh Anh · BIS Textile") */}
          <div className="hidden md:flex items-center gap-2 pl-1 pr-2.5 py-1 rounded-full bg-[#261F1C] border border-[#3E322C]">
            <div className="w-6 h-6 rounded-full bg-[#4A3B34] text-[#FAF6F0] flex items-center justify-center">
              <User className="w-3.5 h-3.5" />
            </div>
            <div className="text-left leading-tight">
              <div className="text-[11px] font-bold text-[#FAF6F0]">
                Nguyễn Minh Anh
              </div>
              <div className="text-[10px] text-[#B8AAA0]">BIS Textile</div>
            </div>
          </div>

          <button
            type="button"
            onClick={onOpenDesignRationale}
            className="px-2.5 py-1.5 text-xs font-semibold text-[#FAF6F0] bg-[#2C231F] hover:bg-[#D9382C] border border-[#4A3B34] rounded-lg transition-colors whitespace-nowrap"
          >
            Thiết kế &amp; Adapter
          </button>
        </div>
      </div>
    </header>
  );
};
