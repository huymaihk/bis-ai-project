import {
  BisBackgroundId,
  HaravanDraftRecord,
  ProcessedImageRender,
  ProductRecord,
  SyncState,
} from '../types/bisTypes';

/**
 * BIS TEXTILE AI — Python & Streamlit Backend Adapter Layer
 * ---------------------------------------------------------
 * Thiết kế sẵn lớp Adapter chuẩn để kết nối với hệ thống Backend Python / Streamlit hiện có.
 * MẶC ĐỊNH TRONG BẢN MẪU: Chạy ở chế độ 'DEMO_SANDBOX' (không gọi API trả phí, không yêu cầu
 * khóa bí mật, không ghi/xóa dữ liệu thật trên Haravan, không tự tuyên bố agent chạy nền).
 */

export interface BackendConnectionConfig {
  mode: 'DEMO_SANDBOX' | 'PYTHON_FASTAPI_BRIDGE';
  pythonBaseUrl: string;
  streamlitSessionUrl: string;
  haravanTargetMode: 'DRAFT_ONLY_SAFE'; // Tuyệt đối không có quyền DELETE sản phẩm Haravan
}

export interface AdapterHealthReport {
  config: BackendConnectionConfig;
  nodes: {
    id: string;
    name: string;
    endpoint: string;
    state: SyncState;
    statusText: string;
    lastChecked: string;
  }[];
}

export const DEFAULT_BACKEND_CONFIG: BackendConnectionConfig = {
  mode: 'DEMO_SANDBOX',
  pythonBaseUrl: import.meta.env.VITE_BIS_PYTHON_API_URL || 'http://localhost:8501/api/v1',
  streamlitSessionUrl: import.meta.env.VITE_BIS_STREAMLIT_URL || 'http://localhost:8501',
  haravanTargetMode: 'DRAFT_ONLY_SAFE',
};

export const ADAPTER_ENDPOINTS = {
  extractPdfSku: 'POST /api/v1/technical/extract-sku',
  verifySpecEvidence: 'PATCH /api/v1/technical/specs/:specId/verify',
  saveMarketingContent: 'PUT /api/v1/marketing/products/:sku/content',
  renderStudio1254: 'POST /api/v1/imagestudio/render-1254x1254',
  approveStudioImage: 'POST /api/v1/imagestudio/approve-version',
  checkHaravanDuplicate: 'POST /api/v1/operations/reconcile-duplicates',
  createHaravanDraft: 'POST /api/v1/operations/haravan/create-draft',
  searchKnowledgeDocs: 'GET /api/v1/knowledge/catalogues',
  commitMemoryCalibration: 'POST /api/v1/memory/calibrations',
} as const;

export function getAdapterHealthReport(): AdapterHealthReport {
  return {
    config: DEFAULT_BACKEND_CONFIG,
    nodes: [
      {
        id: 'python-pdf-parser',
        name: 'Python PDF Extractor (PyMuPDF / OCR)',
        endpoint: `${DEFAULT_BACKEND_CONFIG.pythonBaseUrl}/technical/extract-sku`,
        state: 'demo_offline',
        statusText: 'Chế độ Mô phỏng (Chưa nối cổng 8501)',
        lastChecked: 'Vừa kiểm tra · Local Demo',
      },
      {
        id: 'image-pipeline-cv',
        name: 'Image Studio Processor (1254×1254 Canvas)',
        endpoint: `${DEFAULT_BACKEND_CONFIG.pythonBaseUrl}/imagestudio/render-1254x1254`,
        state: 'demo_offline',
        statusText: 'Chế độ Mô phỏng (Xử lý tại trình duyệt)',
        lastChecked: 'Vừa kiểm tra · Local Demo',
      },
      {
        id: 'knowledge-vector-index',
        name: 'Kho Tài liệu & Từ điển Dệt May (Knowledge)',
        endpoint: `${DEFAULT_BACKEND_CONFIG.pythonBaseUrl}/knowledge/catalogues`,
        state: 'synced',
        statusText: 'Đã nạp 4 bộ Catalogue mẫu (Dữ liệu minh họa)',
        lastChecked: '14:20 hôm nay',
      },
      {
        id: 'memory-version-store',
        name: 'Bộ nhớ Hiệu chỉnh & Phiên bản (Memory Store)',
        endpoint: `${DEFAULT_BACKEND_CONFIG.pythonBaseUrl}/memory/calibrations`,
        state: 'pending',
        statusText: 'Đang chờ đồng bộ 2 bản hiệu chỉnh cục bộ',
        lastChecked: '14:18 hôm nay',
      },
      {
        id: 'haravan-draft-gateway',
        name: 'Haravan Draft Gateway (Chỉ tạo nháp - Không xóa)',
        endpoint: `${DEFAULT_BACKEND_CONFIG.pythonBaseUrl}/operations/haravan/create-draft`,
        state: 'demo_offline',
        statusText: 'Sandbox An toàn (Không ghi dữ liệu thật)',
        lastChecked: 'Chế độ bảo vệ',
      },
    ],
  };
}

export async function simulateStudioRender1254(params: {
  sku: string;
  sourceImageId: string;
  backgroundId: BisBackgroundId;
  paddingPercent: number;
  shadowIntensity: number;
  contrastBoost: boolean;
}): Promise<ProcessedImageRender> {
  return {
    renderId: `RND-${params.sku}-${Date.now().toString().slice(-4)}`,
    sourceImageId: params.sourceImageId,
    backgroundId: params.backgroundId,
    paddingPercent: params.paddingPercent,
    shadowIntensity: params.shadowIntensity,
    contrastBoost: params.contrastBoost,
    dimensions: '1254 × 1254 px',
    createdAt: new Date().toLocaleTimeString('vi-VN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }),
    // Never mark approved automatically — strictly requires human review
    status: 'review',
  };
}

export async function simulateCreateHaravanDraft(
  product: ProductRecord
): Promise<HaravanDraftRecord> {
  return {
    draftId: `HRV-DRAFT-${product.sku}-${Math.floor(1000 + Math.random() * 9000)}`,
    createdAt: new Date().toLocaleString('vi-VN'),
    sku: product.sku,
    haravanPreviewUrl: `https://bis-textile-demo.myharavan.com/admin/products/draft-${product.sku.toLowerCase()}`,
    environment: 'DEMO_SANDBOX',
  };
}

export const createHaravanProductDraft = simulateCreateHaravanDraft;
