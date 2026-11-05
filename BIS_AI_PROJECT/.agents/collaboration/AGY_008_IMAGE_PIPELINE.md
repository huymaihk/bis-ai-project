# AGY_008 Image pipeline and GitHub evaluation
Status: READY_FOR_REVIEW
Owner: Codex
Antigravity status: CLAIMED; independent report READY_FOR_REVIEW, Cloud review pending.
Codex file scope: studio_ai.py, studio_api.py, ImageSources.tsx, protocol loader/tests, optional benchmark tool, main report and handover/memory.
Antigravity file scope: AGY_008_ANTIGRAVITY_REVIEW.md and scratch evidence only. No concurrent code edits, push, real-product approval or Haravan calls.

## Verified changes
- Selected reference URL is resolved through the existing asset allowlist and passed exactly to initial generation, retry and download package; wrong/missing references rejected before provider call.
- Sanitized provider diagnostics distinguish 401/403/404/429/503/504, timeout and no-image response. Last result saved per SKU and shown next to results after reload; no raw provider bodies, keys or billing IDs saved/displayed.
- New previews timestamped and newest first. Legacy images retain their label; no silent successful replacement after a failed generation. Initial generation rechecks source hash before registering result.
- Gemini image model can be set via BIS_IMAGE_MODEL env or Streamlit Secrets. Source resolution warning reflects source dimensions, not invented success from output dimensions.
- ZIP download contains original, selected background, selected reference, prompt with last 8 same-SKU feedback and instructions for web editing when API quota unavailable. Local download only; no external upload/approval.
- Original book-cover geometry and all printed text are explicitly protected in prompt. Prompt is a request, not proof of preservation.
- Protocol workflow-v2-17 refreshes studio_ai and studio_api together.

## Real Gemini evidence (local, NOT proof of Cloud configuration)
- One real generation request using supplied strap photo + BIS background/reference: ClientError HTTP 429, 8.10 seconds. No generated image. Evidence: C:/Users/Dell/bis-image-lab/provider_result.json (local only).
- Read-only model lookup from BIS project context: models/gemini-3.1-flash-image is available, supports generateContent. No key printed. Running outside project context lacked configured key; this is not Cloud auth evidence.
- Therefore no claim image quality achieved or provider generation succeeded. 429 may be quota/rate/billing restriction; exact subcause not established. Do not hammer retries or change billing automatically.

## GitHub experiments (isolated C:/Users/Dell/bis-image-lab)
| Component | Pinned source | Actual result | Integration decision |
|---|---|---|---|
| rembg | e2c2e3f72701357b9bb3f2be32a4330d74ce8f47; u2netp 4.57 MB | Python 3.12.8 isolated env, ONNX CPU; two supplied images inferred. Trial runner: strap 0.750s, book 0.718s excluding initialization. Alpha range 0..255. Visual strap foreground mostly separated; white book cover erased, leaving colored fan. | Reject universal automatic masking. Keep optional reproducible benchmark only. MIT applies to code; audit specific model license before commercial packaging. |
| Real-ESRGAN | Python source a4abfb2979a7bbff3f69f58f58ae324608821e27; official NCNN bundle 20220424/v0.2.5.0 | Intel Iris Xe Vulkan, realesrgan-x4plus, 4x, tile64, one worker. Strap 200x112 ->800x448; book250x250 ->1000x1000; exit0 for both. Runner times13.657s/16.141s. Visual: smoother edges but strap still dark; book small text distorted/illegible. | Not accepted as text restoration or final quality. Optional benchmark only; no heavy models added to Cloud. Python BSD3, NCNN MIT; retain applicable notices if integrated. |
| IC-Light | bcf3f29ca85be8a4686215f477b546f5030be8b7 | Source inspection: example uses torch.device('cuda'); local GPU inventory Intel Iris Xe only. No inference performed. | GPU worker candidate, not validated on this host or Cloud. Code Apache2; model licenses must be checked separately. |
| AI-Product-Photo-Studio-Generator | c239281506ac12220127a655a1c8ed8977387306 | Checkout contains README, LICENSE.md and output media; no runnable application/package.json. LICENSE CC-BY-NC4.0. | Reference only; not a runnable solution, no commercial code copied. |

Official sources:
- https://github.com/danielgatis/rembg
- https://github.com/xinntao/Real-ESRGAN
- https://github.com/xinntao/Real-ESRGAN/releases/tag/v0.2.5.0
- https://github.com/lllyasviel/IC-Light
- https://github.com/alok-ahirrao/AI-Product-Photo-Studio-Generator

Reproduction: tools/benchmark_image_components.py --help. Use isolated Python3.12 with rembg[cpu], explicit fresh lab output directory, optional official NCNN binary with models. First JIT-enabled rembg import was stopped after long compilation; NUMBA_DISABLE_JIT=1 gave successful bounded CPU inference. No experiment output copied to product storage or approved. Logs/outputs remain local.

## Automated verification
82 tests PASS: python -m unittest test_bis_api test_quality_workflow test_gemini_fallback test_streamlit_react_host test_studio_ai -q
TypeScript lint and production frontend build PASS. Includes exact selected reference, invalid reference, persistent safe429 error, newest order, ZIP contents and feedback, source/hash safety, no-image failure and SDK image response boundary. Provider replies in these tests are mocked; real attempt described separately above.

## Cross-review required from Antigravity
- Correct unsupported numeric claims in independent report (95% aesthetic quality, exact RAM/time/VRAM/Cloud failure claims not measured). Do not equate code inspection with image or Cloud acceptance. Record specific source links for license claims; acknowledge Alok checkout has no runnable code and CC-BY-NC.
- After deployment, inspect selected reference, prominent failure state, legacy label, newest-first and ZIP download on Cloud. No real-product saves/approvals; no additional paid API attempts needed. If browser unavailable, explicitly report limitation without bypass.
- Evaluate lab outputs visually: white cover mask FAIL and small-text restoration FAIL; runtime success is not product acceptance.
- Return READY_FOR_REVIEW and a Codex prompt. Overall owner-quality acceptance remains OPEN until a real generated output is compared and owner approves.

Lesson: evaluate per product class (book/white objects vs equipment/straps), validate executable source and license, and separate inference success, API availability and final image quality. No Haravan operations.
