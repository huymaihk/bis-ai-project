Owner: Codex
Status: READY_FOR_REVIEW
Scope: bis_api.py, agent_technical.py, CatalogueTechnical.tsx, cache protocol, tests. Durable per-version page progress, resume and explicit reanalysis; stop on quota failure. No Haravan.


## 2026-11-06 PDF progress and resume
- Persist unique successful page numbers per PDF SHA256; show count/percent and current-run progress; resume only missing pages in selected range. Legacy page-number counters migrated using original start/end. Changed PDFs require confirmation; repeated processed ranges require confirm. SKU-only extraction does not mark a whole page complete.
- Stop immediately on Gemini 429 instead of retrying the same model twice. Does not restore provider quota or claim live API success. Completed drafts preserved.
- 96 tests PASS including failure/resume/changed PDF and single-call 429; frontend lint/build PASS. Protocol v2-20. Live Cloud UI and provider recovery pending; local progress is not verified durable Drive/Cloud sync. No Haravan operations.
