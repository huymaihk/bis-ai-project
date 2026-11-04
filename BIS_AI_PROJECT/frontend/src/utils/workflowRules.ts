import {
  DepartmentId,
  OperationsChecklist,
  PipelineStepId,
  ProductRecord,
  SeoMetadata,
  VerificationStatus,
} from '../types/bisTypes';

export const SEO_LIMITS = {
  TITLE_MIN: 20,
  TITLE_MAX: 70,
  DESC_MIN: 70,
  DESC_MAX: 160,
} as const;

export function mapStepToDepartment(step: PipelineStepId): DepartmentId {
  switch (step) {
    case 'source':
      return 'technical';
    case 'content':
      return 'marketing';
    case 'images':
      return 'imagestudio';
    case 'approval':
      return 'operations';
  }
}

export function mapDepartmentToStep(dept: DepartmentId): PipelineStepId | null {
  switch (dept) {
    case 'technical':
      return 'source';
    case 'marketing':
      return 'content';
    case 'imagestudio':
      return 'images';
    case 'operations':
      return 'approval';
    default:
      return null;
  }
}

export interface SeoEvaluationResult {
  titleViLength: number;
  descViLength: number;
  titleEnLength: number;
  descEnLength: number;
  isValid: boolean;
  warnings: string[];
}

export function evaluateSeoMetadata(seo: SeoMetadata): SeoEvaluationResult {
  const titleViLength = seo.titleVi.trim().length;
  const descViLength = seo.descVi.trim().length;
  const titleEnLength = seo.titleEn.trim().length;
  const descEnLength = seo.descEn.trim().length;
  const warnings: string[] = [];

  if (titleViLength === 0 || titleViLength > SEO_LIMITS.TITLE_MAX) {
    warnings.push(`Tiêu đề SEO Tiếng Việt (${titleViLength}/${SEO_LIMITS.TITLE_MAX} ký tự) vượt giới hạn hoặc đang trống.`);
  }
  if (descViLength < SEO_LIMITS.DESC_MIN || descViLength > SEO_LIMITS.DESC_MAX) {
    warnings.push(`Mô tả SEO Tiếng Việt (${descViLength}/${SEO_LIMITS.DESC_MAX} ký tự) nên từ ${SEO_LIMITS.DESC_MIN}–${SEO_LIMITS.DESC_MAX} ký tự.`);
  }
  if (titleEnLength === 0 || titleEnLength > SEO_LIMITS.TITLE_MAX) {
    warnings.push(`SEO Title Tiếng Anh (${titleEnLength}/${SEO_LIMITS.TITLE_MAX} ký tự) vượt giới hạn hoặc đang trống.`);
  }
  if (descEnLength < SEO_LIMITS.DESC_MIN || descEnLength > SEO_LIMITS.DESC_MAX) {
    warnings.push(`SEO Description Tiếng Anh (${descEnLength}/${SEO_LIMITS.DESC_MAX} ký tự) nên từ ${SEO_LIMITS.DESC_MIN}–${SEO_LIMITS.DESC_MAX} ký tự.`);
  }

  return {
    titleViLength,
    descViLength,
    titleEnLength,
    descEnLength,
    isValid: warnings.length === 0,
    warnings,
  };
}

export function toggleCompareCandidateSelection(
  currentIds: string[],
  candidateId: string,
  maxSelection = 3
): { nextIds: string[]; limitReached: boolean } {
  if (currentIds.includes(candidateId)) {
    return {
      nextIds: currentIds.filter((id) => id !== candidateId),
      limitReached: false,
    };
  }
  if (currentIds.length >= maxSelection) {
    return {
      nextIds: currentIds,
      limitReached: true,
    };
  }
  return {
    nextIds: [...currentIds, candidateId],
    limitReached: false,
  };
}

export function deriveProductChecklist(product: ProductRecord): OperationsChecklist {
  // 1. Technical Evidence
  const hasErrorSpec = product.specs.some((s) => s.status === 'error');
  const hasUnverifiedSpec = product.specs.some(
    (s) => s.status === 'unchecked' || s.status === 'review'
  );
  const technicalEvidence: VerificationStatus = hasErrorSpec
    ? 'error'
    : hasUnverifiedSpec
    ? 'review'
    : 'approved';

  // 2. Marketing 7-part content
  const hasMissingEvidenceSection = product.marketingSections.some(
    (sec) => sec.hasMissingEvidence || sec.content.trim().length < 20
  );
  const marketingContent: VerificationStatus =
    product.marketingSections.length === 7 && !hasMissingEvidenceSection
      ? 'approved'
      : 'review';

  // 3. SEO Bilingual
  const seoEval = evaluateSeoMetadata(product.seo);
  const seoBilingual: VerificationStatus = seoEval.isValid ? 'approved' : 'review';

  // 4. Image Studio 1254x1254 (Human approval strictly required)
  let imageStandard1254: VerificationStatus = 'unchecked';
  if (product.activeProcessedRender) {
    imageStandard1254 = product.activeProcessedRender.status;
  }

  // 5. Duplicate check
  const hasUnresolvedDuplicate = product.duplicates.some(
    (d) => d.resolution === 'unresolved'
  );
  const duplicateCheck: VerificationStatus =
    product.duplicates.length === 0
      ? 'approved'
      : hasUnresolvedDuplicate
      ? 'review'
      : 'approved';

  return {
    technicalEvidence,
    marketingContent,
    seoBilingual,
    imageStandard1254,
    duplicateCheck,
  };
}

export interface HaravanDraftReadiness {
  canCreateDraft: boolean;
  blockingReasons: string[];
  checklist: OperationsChecklist;
}

export function evaluateHaravanDraftReadiness(
  product: ProductRecord
): HaravanDraftReadiness {
  const checklist = deriveProductChecklist(product);
  const blockingReasons: string[] = [];

  if (checklist.technicalEvidence !== 'approved') {
    blockingReasons.push('Còn thông số kỹ thuật chưa xác minh chứng cứ trang PDF.');
  }
  if (checklist.marketingContent !== 'approved') {
    blockingReasons.push('Nội dung 7 phần còn mục thiếu dẫn chứng hoặc chưa hoàn thiện.');
  }
  if (checklist.seoBilingual !== 'approved') {
    blockingReasons.push('SEO song ngữ Việt/Anh chưa đạt chuẩn độ dài ký tự.');
  }
  if (checklist.imageStandard1254 !== 'approved') {
    blockingReasons.push('Ảnh thành phẩm 1254 × 1254 chưa được người phụ trách duyệt.');
  }
  if (checklist.duplicateCheck !== 'approved') {
    blockingReasons.push('Chưa hoàn tất đối soát mã SKU nghi ngờ trùng lặp.');
  }

  return {
    canCreateDraft: blockingReasons.length === 0,
    blockingReasons,
    checklist,
  };
}
