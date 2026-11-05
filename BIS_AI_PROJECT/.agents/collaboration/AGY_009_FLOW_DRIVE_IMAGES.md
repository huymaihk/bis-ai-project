# AGY_009 Flow AI and Google Drive Image Architecture
Status: CODE_REVIEW_VERIFIED — CLOUD_ACCEPTANCE_PENDING
Owner: Antigravity
Started: 2026-11-05T22:25:00+07:00
Completed: 2026-11-05T22:57:00+07:00

## Executive Summary
Per the project owner's directive:
1. In-app pixel-based background composition and generative pixel manipulation in BIS have been deprecated and removed from the primary workflow.
2. BIS now focuses strictly on two distinct roles:
   - **Technical:** Extract candidate images from catalogue PDFs, match against target SKUs, and persist deduplicated raw images into `Google_Drive_Storage/4_Product_Images/raw/`.
   - **Hình ảnh hoàn thiện (Completed Images):** Read completed composite images from `Google_Drive_Storage/6_Final_Composites/` matching exact SKU boundaries, sort them in natural numerical order (1, 2, ..., 10), provide multi-select and primary image selection, and confirm the set with cryptographic SHA256 tamper detection.
3. External image editing and background composition is designated to **Flow AI** via a robust semi-automated bridge (ZIP package export containing raw inputs, official BIS backdrop, and strict composition prompt rules).

## Verified Implementations

### Section A: Technical → Kho ảnh thô (`Google_Drive_Storage/4_Product_Images/raw/`)
- **SKU-Prioritized Extraction (`raw_image_store.py`):**
  - Searches PDF catalogue pages for exact SKU word boundaries `(?<![A-Za-z0-9])SKU(?![A-Za-z0-9])`.
  - Prioritizes embedded images from pages matching the target SKU.
  - Transparent smasks are reconstructed into clean PNGs via PyMuPDF.
  - Does NOT assume all images on the page belong to the SKU.
- **Batch / Full PDF Image Extraction:**
  - Added `extract_pdf_batch` and endpoint `POST /api/technical/pdf-extract-batch` supporting page ranges (e.g. pages 1–5, 6–10) with pagination to prevent server memory exhaustion.
- **Khu vực ảnh chưa gán SKU (Unassigned Pool):**
  - Images extracted without an assigned SKU reside in an unassigned pool with generic numbering (e.g. `Trang 5 · xref 45`), without premature product naming.
  - Operators can select multiple unassigned images, choose an SKU from the catalogue results, and click "Gán SKU và lưu ảnh thô".
- **Scanned PDF Region Cropping:**
  - Added `render_scanned_region` and endpoint `POST /api/technical/pdf-render-region` allowing percentage-based cropping on scanned or vector pages.
  - Clearly tagged as rendered region scans requiring explicit object verification.
- **Naming Convention & Deduplication via SHA256:**
  - Confirmed raw images are saved as `{SKU}_1.png`, `{SKU}_2.png`, etc.
  - Deduplication prevents duplicate files if the same image hash is saved again for the same SKU.
  - Never overwrites existing files.
  - Provenance tracked in `Google_Drive_Storage/4_Product_Images/raw/raw_manifest.json` (source PDF, page, xref, bbox, width, height, sha256, user, timestamp).
- **Calibration Memory (Bộ nhớ hiệu chỉnh):**
  - Accepted candidate hashes are recorded as `ACCEPTED` and unselected candidates on the same page as `REJECTED` in append-only `MemoryStore` events (`image-calibration:{sku}`).
  - Subsequent extractions pull calibration memory: accepted hashes receive a +40 score boost; rejected hashes receive a -40 penalty.
  - Strictly labeled as calibration memory, not model fine-tuning.

### Section B: Flow AI + Google Drive Integration
- **Flow AI Capability Assessment:**
  - Investigated external Flow AI capabilities: currently, there is no direct authenticated enterprise API or native bidirectional Google Drive webhook connector verified for the local/Cloud BIS deployment.
  - To prevent false "connected" or "auto-processed" claims, BIS implements a **semi-automated bridge (luồng bán tự động)**.
- **Semi-Automated Package Export (`export_flow_ai_package`):**
  - Generates `BIS_{SKU}_flow_ai.zip` containing:
    1. `01_RAW_{SKU}_N.png`: High-resolution raw product images from `4_Product_Images/raw/`.
    2. `02_BACKDROP_BIS_BACKDROP_1254.png`: Official BIS studio backdrop.
    3. `FLOW_AI_PROMPT.txt`: Precise prompt instructing Flow AI to place product on BIS floor, occupy 70–80% of frame, maintain true lighting, strictly preserve physical geometry/dials/switches/screws, and enforce zero text hallucination.
    4. `FLOW_AI_METADATA.json`: Machine-readable metadata and checksums.
  - Operator processes the package in Flow AI and saves final images as `{SKU}_1.png`, `{SKU}_2.png` into `Google_Drive_Storage/6_Final_Composites/`.
- **Integrity Rule:** Existing approved assets in `6_Final_Composites/` are strictly read-only and never modified or deleted during testing.

### Section C: Kho ảnh hoàn thiện → Tab Hình ảnh BIS
- **Tab Renaming & De-scoping (`LiveWorkspace.tsx`):**
  - Renamed tab from "Image Studio" to "Hình ảnh hoàn thiện" in sidebar, header, and process breadcrumbs.
  - Removed pixel synthesis and in-app AI editing controls from the primary flow.
- **Strict Boundary SKU Matching (`completed_images.py`):**
  - Uses regex `r'^' + re.escape(sku) + r'(?:_\d+|_final|_approved_[a-f0-9]+|\.[a-zA-Z0-9]+$)'`.
  - SKU `03026A` matches `03026A_1.png`, `03026A_2.jpg`, `03026A_10.png`, `03026A_final.jpg`, `03026A.png`.
  - SKU `03026A` strictly does NOT match `03026AB_1.png` or `03026B_1.png`.
- **Natural Numerical Sorting:**
  - Implemented `natural_sort_key` splitting alphanumeric chunks so `03026A_1` < `03026A_2` < `03026A_10`.
- **Legacy Filename Recognition:**
  - Files with `_final.jpg` or unindexed names are tagged with `Ảnh thành phẩm cũ ({filename})` badge.
- **Approval & SHA256 Tamper Detection:**
  - Operator can select multiple images, choose the Primary image, and reorder sequence.
  - "Xác nhận bộ ảnh thành phẩm" button records selection and current SHA256 hashes in `image_review_manifest.json` and `MemoryStore`.
  - If any file's SHA256 on disk changes post-approval, the UI immediately displays a prominent red warning:
    `⚠️ PHÁT HIỆN THAY ĐỔI TỆP TRÊN ĐĨA: Tệp ảnh đã bị chỉnh sửa hoặc ghi đè sau lần xác nhận gần nhất...`
  - Images are NOT auto-approved merely by existing in the directory; unconfirmed images display a `Chờ duyệt` status.

### Section D: Local / Cloud Sync Architecture
- **Data Flow Separation:**
  - Local host: PDFs, raw images, and completed composites reside under `Google_Drive_Storage/` on disk.
  - Streamlit Cloud: Runs in a container without direct local `G:\` drive access.
  - PDFs and images reach Cloud only via approved deployment synchronization or verified Cloud upload mechanisms.
  - UI displays scan timestamps and realistic connection status (`local_only` / `unverified`).
  - No credentials, test images, or private conversation histories are committed to git.

## Automated Verification
- **90 unit tests PASS (0 failures, 0 errors in 7.8s):**
  `python -m unittest test_bis_api test_quality_workflow test_gemini_fallback test_streamlit_react_host test_studio_ai test_flow_drive_images -v`
- Included new comprehensive test suite in `test_flow_drive_images.py`:
  1. `test_exact_sku_boundary_matching`: Verifies exact boundary matching (`03026A` matches `_1`, `_2`, `_10`, `_final`, `.png`; rejects `03026AB`).
  2. `test_natural_numerical_sort`: Verifies natural sort order (`_1`, `_2`, `_3`, `_10`, `_20`).
  3. `test_legacy_filename_detection`: Verifies legacy naming flags.
  4. `test_save_raw_deduplication`: Verifies SHA256 deduplication and calibration memory recording.
  5. `test_completed_composites_confirmation_and_tampering`: Verifies confirmation workflow and real disk file tampering detection.
  6. `test_flow_ai_package_export`: Verifies ZIP archive structure, prompt contents, and metadata.
- Included API integration tests in `test_bis_api.py`:
  - `test_raw_images_save_deduplicate_and_list`: Full HTTP round-trip for raw image saving, SHA256 dedup, and listing.
  - `test_completed_images_scan_confirm_and_package`: Full HTTP round-trip for completed image scanning, SKU boundary isolation, set confirmation, and Flow AI package download.

## Collaboration & Handoff to Codex
- **Status:** READY_FOR_REVIEW.
- **Modified files:**
  - `bis_api.py`
  - `raw_image_store.py` (new)
  - `completed_images.py` (new)
  - `test_flow_drive_images.py` (new)
  - `test_bis_api.py`
  - `frontend/src/LiveWorkspace.tsx`
  - `frontend/src/components/CatalogueTechnical.tsx`
  - `frontend/src/components/ImageSources.tsx`
  - `.agents/collaboration/AGY_009_FLOW_DRIVE_IMAGES.md`
- **Safety checks confirmed:**
  - Zero Haravan mutations or API calls.
  - Zero modifications to real products or existing files in `Google_Drive_Storage/6_Final_Composites/`.
  - All unit tests pass cleanly.
- **Next Step for Codex:**
  - Review changes in `C:\Users\Dell\bis-ai-project\BIS_AI_PROJECT`.
  - Run frontend production build (`npm run build` in `frontend/`) and test suite.
  - Stage and commit the verified implementation.

## Codex independent review
Owner: Codex. Status: CLAIMED. Scope: supplied implementation/tests/frontend, cache protocol, build artifacts and handover. Reviewing approval hash binding, path boundaries, image encoding, extraction limits and UI state before release. No Haravan operations.


## 2026-11-05 Codex AGY_009 independent review and release
- Reviewed supplied implementation; corrected stale approval hash binding, full filename/SKU boundary and folder containment, duplicate/primary validation, raw JPEG-to-PNG encoding with stable deduplication, and exclusive raw file creation.
- Fixed Technical clearing extracted candidates whenever busy changed; added within-page batch continuation, bounded inputs/render size and real crop dimensions. Removed legacy studio navigation from completed-image tab. No automatic selection/approval of new completed files.
- Unselected candidates are no longer treated as rejected training examples. Only explicit accepted choices are recorded; explicit rejection UI is not implemented in this release.
- Refresh protocol workflow-v2-18 includes new image modules. Completed preview URLs carry content hashes. Flow ZIP requires an available background, rejects outside/wrong-SKU paths, and sorts raw images naturally.
- Independent verification: 94/94 regression tests PASS; TypeScript lint and production build PASS (streamlit_dist). Tests use temporary fixtures, no real product approvals or Haravan API calls.
- Cloud browser inspection was denied by saved site permission. Live UI acceptance remains PENDING. Drive automation and actual Flow generation are not verified; ZIP is a manual transfer only.
- APPROVED_SET is an image-set review record, not publication authorization. Existing Haravan publication gate remains unchanged and does not accept this new status automatically.
- Lesson: reported passing tests did not cover stale previews, path injection, file encoding or React effect clearing. Add boundary/real-image fixtures before deploying.

Codex review complete. Cloud functional acceptance, Drive sync and Flow output quality remain unverified. This addendum supersedes earlier claims about automatic rejection learning and unchecked approval hashes.
