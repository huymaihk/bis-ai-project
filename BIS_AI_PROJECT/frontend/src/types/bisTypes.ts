export type DepartmentId =
  | 'overview'
  | 'technical'
  | 'marketing'
  | 'imagestudio'
  | 'operations'
  | 'knowledge'
  | 'memory';

export type PipelineStepId = 'source' | 'content' | 'images' | 'approval';

export type VerificationStatus = 'unchecked' | 'review' | 'approved' | 'error';

export type SyncState = 'synced' | 'pending' | 'error' | 'demo_offline';

export interface TechnicalSpecItem {
  id: string;
  labelVi: string;
  labelEn: string;
  value: string;
  unit: string;
  pdfPage: number;
  evidenceQuote: string;
  bbox: { x: number; y: number; w: number; h: number }; // percentage on PDF page
  status: VerificationStatus;
  updatedBy: string;
}

export interface MarketingSection {
  id: string;
  order: number;
  title: string;
  content: string;
  evidenceRef: string;
  hasMissingEvidence: boolean;
}

export interface SeoMetadata {
  titleVi: string;
  descVi: string;
  slugVi: string;
  titleEn: string;
  descEn: string;
  keywords: string[];
}

export interface MarketingVersion {
  versionId: string;
  timestamp: string;
  author: string;
  note: string;
  seoTitleVi: string;
}

export type ImageSourceType = 'pdf' | 'web' | 'upload';

export type BisBackgroundId = 'bis-pure-white' | 'bis-lab-neutral' | 'bis-warm-ivory' | 'bis-transparent';

export interface CandidateImage {
  id: string;
  sku: string;
  sourceType: ImageSourceType;
  label: string;
  pdfPage?: number;
  pdfDocument?: string;
  webUrl?: string;
  webDomain?: string;
  originalDimensions: string;
  aspectRatioNote: string;
  sharpnessScore: string;
  lightingNote: string;
  visualVariant: 'pdf-scan-front' | 'pdf-scan-detail' | 'web-angle' | 'web-front-clean' | 'upload-raw';
  isReferenceSample?: boolean;
}

export interface ProcessedImageRender {
  renderId: string;
  sourceImageId: string;
  backgroundId: BisBackgroundId;
  paddingPercent: number;
  shadowIntensity: number;
  contrastBoost: boolean;
  dimensions: '1254 × 1254 px';
  createdAt: string;
  status: VerificationStatus;
  approvedBy?: string;
  approvedAt?: string;
  reviewerNote?: string;
}

export interface DuplicateCandidate {
  haravanId: string;
  sku: string;
  title: string;
  brand: string;
  similarityPercent: number;
  matchReason: string;
  resolution: 'unresolved' | 'confirmed_unique' | 'merged_draft';
}

export interface OperationsChecklist {
  technicalEvidence: VerificationStatus;
  marketingContent: VerificationStatus;
  seoBilingual: VerificationStatus;
  imageStandard1254: VerificationStatus;
  duplicateCheck: VerificationStatus;
}

export interface HaravanDraftRecord {
  draftId: string;
  createdAt: string;
  sku: string;
  haravanPreviewUrl: string;
  environment: 'DEMO_SANDBOX';
}

export interface ProductRecord {
  sku: string;
  nameVi: string;
  nameEn: string;
  brand: string;
  originCountry: string;
  category: string;
  standardCode: string;
  catalogueFile: string;
  catalogueTotalPages: number;
  activePdfPage: number;
  currentStep: PipelineStepId;
  assignedAgent: DepartmentId;
  overallStatus: VerificationStatus;
  lastUpdated: string;
  specs: TechnicalSpecItem[];
  marketingSections: MarketingSection[];
  seo: SeoMetadata;
  marketingVersions: MarketingVersion[];
  candidateImages: CandidateImage[];
  selectedSourceImageId: string | null; // Strictly null initially for unapproved items if not chosen by user
  activeProcessedRender: ProcessedImageRender | null;
  renderHistory: ProcessedImageRender[];
  duplicates: DuplicateCandidate[];
  checklist: OperationsChecklist;
  haravanDraft: HaravanDraftRecord | null;
}

export interface AgentStationMeta {
  id: DepartmentId;
  agentName: string;
  roleTitle: string;
  shortDesc: string;
  colorHex: string;
  finishName: string;
  activeTaskLabel: string;
  queueCount: number;
  alertCount: number;
  floorCoords: { x: number; y: number };
}

export interface KnowledgeDoc {
  id: string;
  title: string;
  fileName: string;
  brand: string;
  totalPages: number;
  indexedSkus: string[];
  updatedAt: string;
  syncState: SyncState;
  pages: {
    pageNumber: number;
    heading: string;
    excerptEn: string;
    excerptVi: string;
    standardRefs: string[];
  }[];
}

export interface MemoryEntry {
  id: string;
  type: 'interaction' | 'knowledge_rule' | 'calibration';
  title: string;
  department: DepartmentId;
  skuContext?: string;
  content: string;
  previousContent?: string;
  version: string;
  timestamp: string;
  actor: string;
  syncState: SyncState;
  isRevoked?: boolean;
}
