# CODEX_012 — BIS token optimization trials
Owner: Codex
Status: EXPERIMENT_COMPLETED; production adoption NOT_APPROVED_BY_TESTS
Date: 2026-11-06

## Scope and reproducibility
Isolated Python3.12.8 CPU environment C:/Users/Dell/bis-token-lab/venv. No production requirements, code paths, product drafts or Haravan data changed. Installed upstream packages from PyPI and PyTorch CPU registry. Versions: PyMuPDF/PyMuPDF4LLM2.1, Docling2.148.0, LLMLingua0.2.2, LiteLLM1.108.1. Full lock, input hashes, model snapshot refs and measurements in lab results/reproducibility.json and requirements-lock.txt. Sources: official repos linked by owner. PyMuPDF4LLM current package delegates to PyMuPDF2.x; do not assume old1.x behavior.

Read-only fixture: current catalogue_sample.pdf pages7,10,15,31. Rendered7 and31 visually inspected. Page31 CURRENT source is proficiency test-method list (not previously described gray-scale SKUs); no product SKU there. Other pages contain3+5+4=12 unique SKU codes. This experiment does not certify every page of the catalogue or other PDFs.

## Local execution
| Tool | Proxy input tokens, four pages | Change vs raw text | Process peak RAM | Observation |
|---|---:|---:|---:|---|
| Raw PyMuPDF text |1577|baseline|162MiB|Source baseline|
| PyMuPDF4LLM2.1 |1526|-3.23%|530MiB|All12 SKU substrings preserved; layout improved, OCR adds imperfect picture text|
| Docling2.148 |1678|+6.40%|1176MiB|All12 SKU substrings preserved; layout/table parsing, not compression|
| LLMLingua2 rate0.7 |922|-41.53%|1261MiB|SKU force_tokens helped; page31 lost TM35 and TM16.3|
| LLMLingua2 rate0.5 |658|-58.28%|same process|Page15 lost REPLACE ANNUALLY; page31 lost all complete TM codes|
| LiteLLM |unchanged text|0% compression|258MiB|Token counter and mock completion executed; gateway/provider routing not proven by mock|

Proxy tokens use cl100k_base for consistent comparison, not Gemini billing. Peak RAM from Windows peak_wset, process totals incl imports. End-to-end cold durations: baseline13.0s, PyMuPDF4LLM20.9s, Docling194.1s, LLMLingua248.6s, LiteLLM54.5s. Runs overlapped and include startup/model downloads: NOT warmed throughput comparisons. LLMLingua warmed per-item compression approx0.58–0.81s. No inference sent to external model services by local parsing/compression; HuggingFace used for model downloads.

Docling tested CPU with OCR disabled on text PDFs and table structure enabled. PyMuPDF4LLM default layout/OCR behavior enabled. Scanned PDF OCR accuracy not evaluated. Numeric coverage is substring heuristic, not field-level quality; full SKU retention does not prove correct SKU/product mapping.

## Real Gemini API comparison
Same compact extraction prompt, page7 text only, gemini-3.5-flash-lite temperature0, max output1500. Raw provider usage below; production's longer prompt and image are excluded. 8 generation calls total (first three repeated after correcting experiment output-file collision; no unreported failed requests). Text-only baseline, Markdown and Docling obtained3 products. Markdown SKU values contained Item# prefixes, so strict raw SKU comparison fails until verified normalization. Model also varied Online subscription format/edition fields. No claim of complete downstream accuracy.

| Input | Real prompt tokens | Real output tokens | Returned SKU fields |
|---|---:|---:|---|
| baseline_7 | 469 | 270 | 03017C, 03026A, 03026B |
| markdown_7 | 456 | 254 | Item #03017C, Item #03026A, Item #03026B |
| docling_7 | 419 | 265 | 03017C, 03026A, 03026B |
| compressed_7_0.7 | 271 | 240 | 03017C, 03026A, 03026B |
| compressed_7_0.5 | 209 | 248 | 03017C, 03026A, 03026B |

LLMLingua kept the3 SKU fields on page7, but quotes come from compressed text and are not verbatim original evidence. page15 and31 content loss is a rejection criterion even when page7 SKU check passes. These live tests used local API configuration; Cloud credentials/quotas not verified here. Output JSON stored only in isolated lab, never written into real product drafts.

## Decision
1. Do not install all four into Streamlit. Trial succeeded in running them, not proving all suitable.
2. First pilot plain PyMuPDF text plus SHA256/page/parser-version cache. Add a quality gate for layouts/scans; retain original text/coordinates for evidence. Text-only vs image+text savings still require controlled multimodal comparison.
3. PyMuPDF4LLM promising for reading order; marginal text token savings in this fixture. Verify AGPL/commercial licensing before distribution; installed metadata dual AGPL/commercial. Existing PyMuPDF license still applies.
4. Docling MIT code useful as an optional LOCAL preprocessing worker for difficult tables. Model licenses separately applicable. Measured >1GiB process RAM means Cloud capacity must be measured before adoption.
5. LLMLingua MIT code should not compress authoritative SKU/spec/standards/evidence. Potential later trial only for noncritical instruction/history with protected factual blocks. Model licensing separately applicable. Current whole-page compression FAILS BIS requirements.
6. LiteLLM MIT core useful if multiple providers need a gateway. Current trial does not justify replacing existing bounded fallback; no direct token reduction.
7. Token savings do not restore exhausted RPD/RPM; reducing calls via exact cache and rate scheduling is a separate task.

## Evidence locations
C:/Users/Dell/bis-token-lab/benchmark.py
C:/Users/Dell/bis-token-lab/provider_compare.py
C:/Users/Dell/bis-token-lab/provider_compressed.py
C:/Users/Dell/bis-token-lab/results/ (JSON metrics, source/converted/compressed text, provider output)
C:/Users/Dell/bis-token-lab/requirements-lock.txt
Official upstream: https://github.com/pymupdf/pymupdf4llm ; https://github.com/docling-project/docling ; https://github.com/microsoft/LLMLingua ; https://github.com/BerriAI/litellm

No production deploy or Haravan operations performed. No API keys, model weights, private history or fixture PDFs committed.
