Owner: Codex
Status: READY_FOR_REVIEW — Drive automation still pending
Scope: Technical next SKU, Marketing SEO suggestion accessibility, read-only duplicate endpoint/UI, raw image download/storage status. No Haravan mutations. Automatic Drive sync not configured.


## 2026-11-06 CODEX014 workflow gaps
- Technical name approval now advances to next unapproved SKU after successful revision-bound save. This remains name approval, not overall product approval.
- Marketing SEO fill-empty suggestions remain usable during unsaved editing; existing manual SEO fields preserved. Copy suggestions also no longer disabled solely by dirty state. All three SEO fields already existed; previously remained empty until suggestion applied.
- Exposed duplicate snapshot and live read-only Haravan GET scan in Marketing/Operations. No product/cache mutation by scan. Failed or missing snapshot reports UNVERIFIED/502, not clean. Tests mock remote scan; real store read not performed in this release.
- Raw images are server-local on Cloud, not Google Drive. Added explicit storage notice, correctly named individual downloads and per-SKU ZIP for manual transfer to raw folder. Automatic Drive upload remains NOT IMPLEMENTED/unverified, requires authorized cloud folder and working service credentials.
- 106 tests PASS incl duplicate boundary/error and raw ZIP names; frontend lint/build PASS. Protocol v2-23. Cloud visual acceptance pending; no Haravan mutations, publication, product approvals or Google permission changes.
