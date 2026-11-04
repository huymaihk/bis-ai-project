/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import {
  CandidateImage,
  DepartmentId,
  KnowledgeDoc,
  MarketingSection,
  MemoryEntry,
  PipelineStepId,
  ProcessedImageRender,
  ProductRecord,
  SeoMetadata,
  VerificationStatus,
} from './types/bisTypes';
import {
  AGENT_STATIONS,
  INITIAL_MEMORY_ENTRIES,
  INITIAL_PRODUCTS,
  KNOWLEDGE_DOCS,
} from './data/mockBisData';
import {
  deriveProductChecklist,
  mapDepartmentToStep,
  mapStepToDepartment,
} from './utils/workflowRules';
import { ProductContextHeader } from './components/ProductContextHeader';
import { CommandCenterView } from './components/CommandCenterView';
import { TechnicalView } from './components/TechnicalView';
import { MarketingView } from './components/MarketingView';
import { ImageStudioView } from './components/ImageStudioView';
import { OperationsView } from './components/OperationsView';
import { KnowledgeMemoryView } from './components/KnowledgeMemoryView';
import { VideoAnalysisModal } from './components/VideoAnalysisModal';
import { AuthenticatedStaffUser, LoginView } from './components/LoginView';
import { RobotEyeStyle, RobotFinishPreset } from './utils/agentOfficeSim';
import {
  Home,
  FlaskConical,
  Megaphone,
  Image as ImageIcon,
  Settings,
  BookOpen,
  Cpu,
  Menu,
  X,
  Info,
  FileText,
  AlignLeft,
  CheckCircle2,
  ChevronRight,
  Sparkles,
} from 'lucide-react';

const NAV_ITEMS: {
  id: DepartmentId;
  label: string;
  subLabel: string;
  agentCode: string;
  icon: React.FC<{ className?: string }>;
}[] = [
  {
    id: 'overview',
    label: 'Tổng quan',
    subLabel: '(Overview)',
    agentCode: 'COMMAND',
    icon: Home,
  },
  {
    id: 'technical',
    label: 'Kỹ thuật',
    subLabel: '(Technical)',
    agentCode: 'ATLAS-T1',
    icon: FlaskConical,
  },
  {
    id: 'marketing',
    label: 'Marketing',
    subLabel: '',
    agentCode: 'ARCHER-M2',
    icon: Megaphone,
  },
  {
    id: 'imagestudio',
    label: 'Image Studio',
    subLabel: '',
    agentCode: 'LUMEN-I3',
    icon: ImageIcon,
  },
  {
    id: 'operations',
    label: 'Vận hành',
    subLabel: '(Operations)',
    agentCode: 'SAGE-O4',
    icon: Settings,
  },
  {
    id: 'knowledge',
    label: 'Tri thức',
    subLabel: '(Knowledge)',
    agentCode: 'VERA-K5',
    icon: BookOpen,
  },
  {
    id: 'memory',
    label: 'Bộ nhớ',
    subLabel: '(Memory)',
    agentCode: 'CHRONO-V6',
    icon: Cpu,
  },
];

const BOTTOM_PIPELINE_STEPS: {
  id: PipelineStepId;
  num: number;
  title: string;
  subtitle: string;
  dept: DepartmentId;
  Icon: React.FC<{ className?: string }>;
}[] = [
  {
    id: 'source',
    num: 1,
    title: 'Nguồn',
    subtitle: 'PDF · Spec · Tài liệu',
    dept: 'technical',
    Icon: FileText,
  },
  {
    id: 'content',
    num: 2,
    title: 'Nội dung',
    subtitle: 'Mô tả · Thông tin bán hàng',
    dept: 'marketing',
    Icon: AlignLeft,
  },
  {
    id: 'images',
    num: 3,
    title: 'Ảnh',
    subtitle: 'Ảnh sản phẩm · Xử lý',
    dept: 'imagestudio',
    Icon: ImageIcon,
  },
  {
    id: 'approval',
    num: 4,
    title: 'Duyệt',
    subtitle: 'Kiểm tra · Phê duyệt',
    dept: 'operations',
    Icon: CheckCircle2,
  },
];

export default function App() {
  const [currentUser, setCurrentUser] = useState<AuthenticatedStaffUser | null>(() => {
    if (
      typeof window !== 'undefined' &&
      new URLSearchParams(window.location.search).get('autostart') === '1'
    ) {
      return {
        fullName: 'Nguyễn Minh Anh',
        email: 'minhanh.nguyen@bistextile.vn',
        roleLabel: 'Điều hành viên · BIS Textile',
        department: 'overview',
      };
    }
    return null;
  });
  const [products, setProducts] = useState<ProductRecord[]>(INITIAL_PRODUCTS);
  const [activeSku, setActiveSku] = useState<string>(INITIAL_PRODUCTS[0].sku);
  const [activeDepartment, setActiveDepartment] = useState<DepartmentId>('overview');
  const [knowledgeDocs] = useState<KnowledgeDoc[]>(KNOWLEDGE_DOCS);
  const [memoryEntries, setMemoryEntries] = useState<MemoryEntry[]>(INITIAL_MEMORY_ENTRIES);
  const [reduceMotion, setReduceMotion] = useState<boolean>(false);
  const [eyeStyle, setEyeStyle] = useState<RobotEyeStyle>('rounded');
  const [finishPreset, setFinishPreset] = useState<RobotFinishPreset>('anodized-metal');
  const [mobileNavOpen, setMobileNavOpen] = useState<boolean>(false);
  const [isAnalysisModalOpen, setIsAnalysisModalOpen] = useState<boolean>(false);

  const activeProduct =
    products.find((p) => p.sku === activeSku) || products[0];

  const handleNavigateDepartment = (dept: DepartmentId) => {
    setActiveDepartment(dept);
    setMobileNavOpen(false);
    const mappedStep = mapDepartmentToStep(dept);
    if (mappedStep) {
      setProducts((prev) =>
        prev.map((p) =>
          p.sku === activeSku
            ? {
                ...p,
                currentStep: mappedStep,
              }
            : p
        )
      );
    }
  };

  const handleSelectProductAndNavigate = (sku: string, dept: DepartmentId) => {
    setActiveSku(sku);
    setActiveDepartment(dept);
    setMobileNavOpen(false);
  };

  // Technical Handlers
  const handleUpdateSpecStatus = (
    sku: string,
    specId: string,
    newStatus: VerificationStatus,
    newVal?: string
  ) => {
    setProducts((prev) =>
      prev.map((p) => {
        if (p.sku !== sku) return p;
        const nextSpecs = p.specs.map((s) =>
          s.id === specId
            ? {
                ...s,
                status: newStatus,
                value: newVal !== undefined ? newVal : s.value,
                updatedBy:
                  newStatus === 'approved'
                    ? 'Nguyễn Minh Anh (Đã xác minh)'
                    : 'Đánh dấu xem lại',
              }
            : s
        );
        const updatedProduct = { ...p, specs: nextSpecs, lastUpdated: 'Vừa xong' };
        return {
          ...updatedProduct,
          checklist: deriveProductChecklist(updatedProduct),
        };
      })
    );
  };

  const handleChangePdfPage = (sku: string, page: number) => {
    setProducts((prev) =>
      prev.map((p) => (p.sku === sku ? { ...p, activePdfPage: page } : p))
    );
  };

  // Marketing Handlers
  const handleSaveMarketingAndSeo = (
    sku: string,
    sections: MarketingSection[],
    seo: SeoMetadata,
    versionNote: string
  ) => {
    setProducts((prev) =>
      prev.map((p) => {
        if (p.sku !== sku) return p;
        const nextVersionNumber = `v1.${p.marketingVersions.length + 1}`;
        const updatedProduct: ProductRecord = {
          ...p,
          marketingSections: sections,
          seo,
          lastUpdated: 'Vừa xong',
          marketingVersions: [
            {
              versionId: nextVersionNumber,
              timestamp: 'Vừa lưu xong',
              author: 'Minh Anh',
              note: versionNote,
              seoTitleVi: seo.titleVi,
            },
            ...p.marketingVersions,
          ],
        };
        return {
          ...updatedProduct,
          checklist: deriveProductChecklist(updatedProduct),
        };
      })
    );
  };

  // Image Studio Handlers
  const handleSelectSourceImage = (sku: string, candidateId: string) => {
    setProducts((prev) =>
      prev.map((p) =>
        p.sku === sku
          ? {
              ...p,
              selectedSourceImageId: candidateId,
              lastUpdated: 'Vừa xong',
            }
          : p
      )
    );
  };

  const handleSaveProcessedRender = (sku: string, render: ProcessedImageRender) => {
    setProducts((prev) =>
      prev.map((p) => {
        if (p.sku !== sku) return p;
        const updatedProduct: ProductRecord = {
          ...p,
          activeProcessedRender: render,
          renderHistory: [render, ...p.renderHistory],
          lastUpdated: 'Vừa xong',
        };
        return {
          ...updatedProduct,
          checklist: deriveProductChecklist(updatedProduct),
        };
      })
    );
  };

  const handleApproveRenderVersion = (sku: string, reviewerNote: string) => {
    setProducts((prev) =>
      prev.map((p) => {
        if (p.sku !== sku || !p.activeProcessedRender) return p;
        const approvedRender: ProcessedImageRender = {
          ...p.activeProcessedRender,
          status: 'approved',
          approvedBy: 'Nguyễn Minh Anh',
          approvedAt: 'Vừa duyệt xong',
          reviewerNote,
        };
        const updatedProduct: ProductRecord = {
          ...p,
          activeProcessedRender: approvedRender,
          lastUpdated: 'Vừa xong',
        };
        return {
          ...updatedProduct,
          checklist: deriveProductChecklist(updatedProduct),
        };
      })
    );
  };

  const handleRequestReworkRender = (sku: string) => {
    setProducts((prev) =>
      prev.map((p) => {
        if (p.sku !== sku || !p.activeProcessedRender) return p;
        const reworkRender: ProcessedImageRender = {
          ...p.activeProcessedRender,
          status: 'review',
        };
        const updatedProduct: ProductRecord = {
          ...p,
          activeProcessedRender: reworkRender,
          lastUpdated: 'Vừa xong',
        };
        return {
          ...updatedProduct,
          checklist: deriveProductChecklist(updatedProduct),
        };
      })
    );
  };

  const handleAddUploadedCandidate = (sku: string, newCandidate: CandidateImage) => {
    setProducts((prev) =>
      prev.map((p) =>
        p.sku === sku
          ? {
              ...p,
              candidateImages: [newCandidate, ...p.candidateImages],
            }
          : p
      )
    );
  };

  // Operations Handlers
  const handleResolveDuplicate = (
    sku: string,
    haravanId: string,
    resolution: 'confirmed_unique' | 'merged_draft'
  ) => {
    setProducts((prev) =>
      prev.map((p) => {
        if (p.sku !== sku) return p;
        const updatedProduct: ProductRecord = {
          ...p,
          duplicates: p.duplicates.map((d) =>
            d.haravanId === haravanId ? { ...d, resolution } : d
          ),
          lastUpdated: 'Vừa xong',
        };
        return {
          ...updatedProduct,
          checklist: deriveProductChecklist(updatedProduct),
        };
      })
    );
  };

  const handleCreatedHaravanDraft = (
    sku: string,
    draftId: string,
    previewUrl: string,
    createdAt: string
  ) => {
    setProducts((prev) =>
      prev.map((p) =>
        p.sku === sku
          ? {
              ...p,
              overallStatus: 'approved',
              haravanDraft: {
                draftId,
                sku,
                haravanPreviewUrl: previewUrl,
                createdAt,
                environment: 'DEMO_SANDBOX',
              },
            }
          : p
      )
    );
  };

  // Memory Handlers
  const handleAddCalibrationEntry = (
    title: string,
    content: string,
    skuContext: string
  ) => {
    const newEntry: MemoryEntry = {
      id: `mem-cal-${Date.now().toString().slice(-4)}`,
      type: 'calibration',
      title,
      department: activeDepartment,
      skuContext,
      content,
      version: 'v1.3',
      timestamp: 'Hôm nay, 15:25',
      actor: 'Minh Anh',
      syncState: 'pending',
    };
    setMemoryEntries((prev) => [newEntry, ...prev]);
  };

  const handleToggleRevokeMemory = (entryId: string) => {
    setMemoryEntries((prev) =>
      prev.map((m) =>
        m.id === entryId ? { ...m, isRevoked: !m.isRevoked } : m
      )
    );
  };

  if (!currentUser) {
    return (
      <LoginView
        onLoginSuccess={(user) => {
          setCurrentUser(user);
          setActiveDepartment(user.department);
          if (typeof document !== 'undefined') {
            document.body.dataset.state = 'playing';
          }
        }}
      />
    );
  }

  return (
    <div
      className={`min-h-screen bg-[#161210] text-[#FAF6F0] flex flex-col lg:flex-row ${
        reduceMotion ? 'reduce-motion' : ''
      }`}
    >
      {/* Mobile Header Bar */}
      <header className="lg:hidden bg-[#1C1715] border-b border-[#382E29] px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-black text-lg tracking-tight text-[#E03B2F] italic">
            BIS
          </span>
          <span className="font-bold text-xs tracking-wider text-[#FAF6F0]">
            TEXTILE AI
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setIsAnalysisModalOpen(true)}
            className="px-2.5 py-1.5 rounded bg-[#2C231F] text-xs text-[#FAF6F0] border border-[#4A3B34]"
          >
            Thiết kế
          </button>
          <button
            type="button"
            onClick={() => setMobileNavOpen((prev) => !prev)}
            aria-label={mobileNavOpen ? 'Đóng menu điều hướng' : 'Mở menu điều hướng'}
            className="p-2 rounded-lg bg-[#2C231F] text-[#FAF6F0] border border-[#4A3B34]"
          >
            {mobileNavOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </header>

      {/* Left Sidebar Navigation (Matches Image 1, 2, 3 Storyboard Sidebar) */}
      <aside
        aria-label="Điều hướng các bộ phận BIS TEXTILE AI"
        className={`${
          mobileNavOpen ? 'block' : 'hidden'
        } lg:flex lg:flex-col lg:w-56 xl:w-60 bg-gradient-to-b from-[#1D1714] via-[#181311] to-[#130F0D] border-r border-[#3A2E28] shadow-[6px_0_28px_-6px_rgba(0,0,0,0.65)] shrink-0 justify-between z-20`}
      >
        <div>
          {/* BIS TEXTILE AI Brand Lockup */}
          <div className="hidden lg:flex items-center justify-between px-5 py-4 border-b border-[#332823] bg-gradient-to-r from-[#241C18]/70 to-transparent">
            <div className="flex items-center gap-2.5">
              <span className="text-2xl font-black italic tracking-tighter text-[#E03B2F] leading-none drop-shadow-[0_2px_6px_rgba(224,59,47,0.35)]">
                BIS
              </span>
              <div className="leading-tight">
                <div className="text-xs font-bold tracking-widest text-[#FAF6F0]">
                  TEXTILE
                </div>
                <div className="text-xs font-bold tracking-widest text-[#D5C7BC]">
                  AI
                </div>
              </div>
            </div>
          </div>

          {/* 7 Department Navigation Tabs */}
          <nav className="p-3 space-y-1.5">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = activeDepartment === item.id;
              const stationMeta = AGENT_STATIONS.find((s) => s.id === item.id);

              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => handleNavigateDepartment(item.id)}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                    isActive
                      ? 'btn-8d-crimson text-white border border-[#F26B60]/40'
                      : 'text-[#D5C7BC] hover:text-white hover:bg-[#261F1C]/90 hover:shadow-[inset_0_1px_0_rgba(255,248,235,0.08),0_4px_10px_rgba(0,0,0,0.35)]'
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <Icon
                      className={`w-4 h-4 shrink-0 ${
                        isActive ? 'text-white' : 'text-[#C4B5AA]'
                      }`}
                    />
                    <div className="text-left leading-tight truncate">
                      <div className="font-bold truncate">{item.label}</div>
                      {item.subLabel && (
                        <div
                          className={`text-[10px] ${
                            isActive ? 'text-white/85' : 'text-[#9C8D84]'
                          }`}
                        >
                          {item.subLabel}
                        </div>
                      )}
                    </div>
                  </div>

                  {stationMeta && stationMeta.alertCount > 0 && (
                    <span
                      className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded-full ${
                        isActive
                          ? 'bg-white/20 text-white shadow-inner'
                          : 'bg-[#2E2520] text-[#FBBF24] border border-[#4A3B34]'
                      }`}
                    >
                      {stationMeta.alertCount}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Bottom Sidebar: Textile Fabric Rolls Accent & Project Path (Matches Storyboard Bottom-Left) */}
        <div className="p-3.5 m-2.5 rounded-2xl card-8d-dark border border-[#463831] space-y-2.5">
          {/* Colorful Textile Rolls Visual Accent */}
          <div className="flex items-center gap-1.5 pt-0.5">
            <span className="h-3.5 flex-1 rounded-full bg-gradient-to-b from-[#DC2626] to-[#991B1B] shadow-[inset_0_1px_0_rgba(255,255,255,0.35),0_2px_4px_rgba(0,0,0,0.4)]" title="Cuộn vải đỏ Crimson" />
            <span className="h-3.5 flex-1 rounded-full bg-gradient-to-b from-[#F59E0B] to-[#B45309] shadow-[inset_0_1px_0_rgba(255,255,255,0.35),0_2px_4px_rgba(0,0,0,0.4)]" title="Cuộn vải vàng Ochre" />
            <span className="h-3.5 flex-1 rounded-full bg-gradient-to-b from-[#F5F5F4] to-[#C7C2BC] shadow-[inset_0_1px_0_rgba(255,255,255,0.8),0_2px_4px_rgba(0,0,0,0.4)]" title="Cuộn vải trắng Kem" />
            <span className="h-3.5 flex-1 rounded-full bg-gradient-to-b from-[#64748B] to-[#334155] shadow-[inset_0_1px_0_rgba(255,255,255,0.3),0_2px_4px_rgba(0,0,0,0.4)]" title="Cuộn vải xám Slate" />
          </div>

          <div className="text-[11px] font-mono text-[#E5D9CE] truncate">
            G:\My Drive\BIS_AI_PROJECT
          </div>

          <div className="text-[11px] text-[#B8AAA0] leading-snug">
            Trạng thái: <span className="text-[#F59E0B] font-mono">Dữ liệu minh họa</span>
          </div>

          <button
            type="button"
            onClick={() => setIsAnalysisModalOpen(true)}
            className="w-full py-1.5 px-2.5 rounded-lg bg-gradient-to-b from-[#352A24] to-[#261E1A] hover:from-[#42352E] hover:to-[#2E241F] text-[11px] font-semibold text-[#FAF6F0] border border-[#524139] shadow-[inset_0_1px_0_rgba(255,248,235,0.12),0_3px_8px_rgba(0,0,0,0.4)] flex items-center justify-center gap-1.5 transition-all"
          >
            <Info className="w-3.5 h-3.5 text-[#E03B2F]" />
            <span>Xem Phân tích &amp; Adapter</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area: Top Header + Active Department Workspace + Bottom Cream Pipeline Dock */}
      <div className="flex-1 flex flex-col min-w-0 justify-between">
        <ProductContextHeader
          products={products}
          activeProduct={activeProduct}
          activeDepartment={activeDepartment}
          currentUser={currentUser}
          onSelectProduct={(sku) => setActiveSku(sku)}
          onNavigateDepartment={handleNavigateDepartment}
          onOpenDesignRationale={() => setIsAnalysisModalOpen(true)}
          onLogout={() => {
            setCurrentUser(null);
            if (typeof document !== 'undefined') {
              document.body.dataset.state = 'title';
            }
          }}
        />

        <main className="flex-1 overflow-y-auto agent-floor-grid">
          {activeDepartment === 'overview' && (
            <CommandCenterView
              products={products}
              activeProduct={activeProduct}
              reduceMotion={reduceMotion}
              eyeStyle={eyeStyle}
              finishPreset={finishPreset}
              onChangeEyeStyle={setEyeStyle}
              onChangeFinishPreset={setFinishPreset}
              onToggleReduceMotion={() => setReduceMotion((prev) => !prev)}
              onSelectProductAndNavigate={handleSelectProductAndNavigate}
              onNavigateDepartment={handleNavigateDepartment}
            />
          )}

          {activeDepartment === 'technical' && (
            <TechnicalView
              product={activeProduct}
              reduceMotion={reduceMotion}
              onUpdateSpecStatus={handleUpdateSpecStatus}
              onChangePdfPage={handleChangePdfPage}
              onProceedToMarketing={() => handleNavigateDepartment('marketing')}
            />
          )}

          {activeDepartment === 'marketing' && (
            <MarketingView
              product={activeProduct}
              reduceMotion={reduceMotion}
              onSaveMarketingAndSeo={handleSaveMarketingAndSeo}
              onProceedToImageStudio={() => handleNavigateDepartment('imagestudio')}
            />
          )}

          {activeDepartment === 'imagestudio' && (
            <ImageStudioView
              product={activeProduct}
              reduceMotion={reduceMotion}
              onSelectSourceImage={handleSelectSourceImage}
              onSaveProcessedRender={handleSaveProcessedRender}
              onApproveRenderVersion={handleApproveRenderVersion}
              onRequestReworkRender={handleRequestReworkRender}
              onAddUploadedCandidate={handleAddUploadedCandidate}
              onProceedToOperations={() => handleNavigateDepartment('operations')}
            />
          )}

          {activeDepartment === 'operations' && (
            <OperationsView
              product={activeProduct}
              reduceMotion={reduceMotion}
              onResolveDuplicate={handleResolveDuplicate}
              onCreatedHaravanDraft={handleCreatedHaravanDraft}
              onNavigateDepartment={handleNavigateDepartment}
            />
          )}

          {(activeDepartment === 'knowledge' || activeDepartment === 'memory') && (
            <KnowledgeMemoryView
              mode={activeDepartment}
              docs={knowledgeDocs}
              memoryEntries={memoryEntries}
              reduceMotion={reduceMotion}
              onAddCalibrationEntry={handleAddCalibrationEntry}
              onToggleRevokeMemory={handleToggleRevokeMemory}
              onSwitchMode={(m) => handleNavigateDepartment(m)}
            />
          )}
        </main>

        {/* Bottom Persistent Cream-Ivory Pipeline Dock (Matches Image 1 & Image 2 Footer Bar) */}
        <footer className="dock-8d-ivory text-[#1E1916] border-t border-[#D8CEC2] px-4 lg:px-6 py-2.5 relative z-10">
          <div className="max-w-[1520px] mx-auto flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="text-xs sm:text-sm font-extrabold text-[#1E1916] leading-tight">
                Quy trình xử lý
                <span className="block sm:inline sm:ml-1 font-medium text-[#574B43]">
                  sản phẩm dệt may
                </span>
              </div>
              <span className="hidden md:inline text-[#D0C4B6]" aria-hidden="true">
                |
              </span>
            </div>

            {/* 4 Pipeline Steps: Nguồn > Nội dung > Ảnh > Duyệt */}
            <div
              role="group"
              aria-label="Quy trình xử lý theo sản phẩm"
              className="flex flex-wrap items-center gap-1.5 sm:gap-2"
            >
              {BOTTOM_PIPELINE_STEPS.map((st, idx) => {
                const StepIcon = st.Icon;
                const isCurrent =
                  activeDepartment === st.dept ||
                  (activeDepartment === 'overview' &&
                    activeProduct.currentStep === st.id);

                return (
                  <React.Fragment key={st.id}>
                    <button
                      type="button"
                      onClick={() =>
                        handleNavigateDepartment(mapStepToDepartment(st.id))
                      }
                      className={`px-3 py-1.5 rounded-2xl border transition-all flex items-center gap-2.5 text-left ${
                        isCurrent
                          ? 'bg-gradient-to-b from-[#FFEFEB] to-[#FADCD9] border-[#D9382C] text-[#B91C1C] shadow-[inset_0_1px_0_#FFFFFF,0_4px_12px_-2px_rgba(217,56,44,0.28),0_2px_4px_rgba(0,0,0,0.08)]'
                          : 'card-8d-interactive border-[#D5C8B8] text-[#2B221E]'
                      }`}
                    >
                      <div
                        className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-xs font-bold shadow-xs ${
                          isCurrent
                            ? 'btn-8d-crimson text-white'
                            : 'bg-gradient-to-b from-[#EAE1D5] to-[#D8CEC0] text-[#3B302B] shadow-[inset_0_1px_0_rgba(255,255,255,0.7)]'
                        }`}
                      >
                        <StepIcon className="w-3.5 h-3.5" />
                      </div>
                      <div>
                        <div className="text-xs font-extrabold leading-none">
                          {st.num}. {st.title}
                        </div>
                        <div className="text-[10px] text-[#6E5D53] hidden xl:block mt-0.5">
                          {st.subtitle}
                        </div>
                      </div>
                    </button>

                    {idx < BOTTOM_PIPELINE_STEPS.length - 1 && (
                      <ChevronRight
                        className="w-4 h-4 text-[#8C7B70] hidden sm:block"
                        aria-hidden="true"
                      />
                    )}
                  </React.Fragment>
                );
              })}
            </div>

            {/* Right CTA Button: ✨ Tạo bản nháp */}
            <button
              type="button"
              onClick={() => handleNavigateDepartment('operations')}
              className="px-5 py-2.5 rounded-2xl btn-8d-crimson text-white text-xs sm:text-sm font-extrabold inline-flex items-center gap-2 transition-all shrink-0 cursor-pointer"
            >
              <Sparkles className="w-4 h-4" />
              <span>Tạo bản nháp</span>
            </button>
          </div>
        </footer>
      </div>

      {/* Video Analysis & Python Adapter Documentation Modal */}
      <VideoAnalysisModal
        isOpen={isAnalysisModalOpen}
        onClose={() => setIsAnalysisModalOpen(false)}
      />
    </div>
  );
}
