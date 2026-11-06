Owner: Codex
Status: READY_FOR_REVIEW
Scope: readonly_duplicates.py, bis_api.py, frontend/src/LiveWorkspace.tsx, protocol loaders, tests, built assets, handover and lessons.
Goal: Read-only Haravan + public catalogue duplicate checks, independent source completeness, fail-closed unknown status. Preserve all publication guards, no shop writes and no draft status changes.


## 2026-11-06 CODEX015 dual-source duplicate evidence
- Marketing/Operations live duplicate check independently reads paginated Haravan API (including hidden products) and public https://bistextile.com/collections/all/products.json. Per-source count, state, time and matching link shown. Exact SKU identity MATCH; related mentions/names REVIEW. Failed/incomplete source never yields clean NO_MATCH; confirmed positive still shown when another source fails. No product status/cache mutations or automatic approval.
- Live GET-only verification: Haravan209 products, public203; against97 local records each source found21 MATCH,9 REVIEW,67 NO_MATCH. These are point-in-time checks, not publication authorization; no snapshot/draft writes from live test. Counts do not prove the sources are interchangeable.
-80 automated API/quality/bridge/read-only tests PASS incl pagination repetition, source failure sanitization, partial-positive and related-code boundaries. TypeScript check/build PASS. Cloud visual acceptance pending. Protocolv2-24.
- All existing Haravan creation guards unchanged, including push-enable, protected existing products/date, exact revision/image approval, durable ledger, fresh live duplicate check and published:false. No Haravan POST/PUT/PATCH/DELETE, no secrets changes. Website/public data is corroborating evidence, not authority to publish.
- Lesson: show source completeness independently; an unavailable source must never be summarized as no duplicates. Public web cannot establish absence of hidden Haravan products.
