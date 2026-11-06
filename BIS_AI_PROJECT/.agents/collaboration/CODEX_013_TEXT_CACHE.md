Owner: Codex
Status: READY_FOR_REVIEW — implementation tested, Cloud acceptance pending
Scope: pdf_analysis_cache.py, agent_technical.py, bis_api.py, frontend Technical, cache protocol/tests/docs. Text-first quality gate and exact page cache; no Haravan.


## 2026-11-06 CODEX013 text-first and page cache deployment
- Implemented pdf_analysis_cache.py using existing PyMuPDF; no new production dependencies. Sorted original page text retained, no lossy SKU/spec compression. Basic text/encoding/multi-column gate chooses text-only or image+text. Text-first missing Item SKUs attempts image recovery, except quota/auth errors; gate is heuristic, not certified for every PDF/table.
- Exact page cache bound to PDF SHA256, page, parser/source-code/PyMuPDF version, prompt+source context hash and input mode. Valid successful/EMPTY_VALID/NEEDS_REVIEW entries only; checksum mismatch recomputes. Cache does not confer product approval or overwrite drafts. Explicit force-refresh UI and SKU reanalysis bypass cache.
- Live local page7 result: text-only PARSED, SKUs03026A/03026B/03017C. Second request cache hit, equal rows and no additional provider attempts. Temporary cache only; production drafts untouched during trial. No claim of full production prompt token savings percentage.
- 104 full regression tests PASS, followed by added HTTP cache/force-refresh test and 34 API/cache tests PASS (105 cases now). TypeScript lint/build PASS. Protocol v2-22 reloads new module.
- Owner-approved next step from CODEX012: lightweight PyMuPDF/cache adopted. Docling remains optional local research, not a Cloud dependency; LLMLingua/LiteLLM not installed into production. Live Cloud visual acceptance pending; cache is local filesystem and not verified durable across Cloud rebuilds. No Haravan calls or mutations.
