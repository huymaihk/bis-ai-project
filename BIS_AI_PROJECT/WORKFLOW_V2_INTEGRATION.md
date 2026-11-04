# Workflow V2 integration

The React workspace now opens the existing business tool for its current department and selected SKU in the authenticated Streamlit session. A return button restores the selected SKU. PDF extraction, content/HTML editing, PDF/web image selection, studio drafts, image approvals, knowledge indexing and trial translation use the existing native tools. Only the requested step renders.

The new “Kiểm tra hồ sơ đã lưu” action performs a local evidence review. It checks source text/content, SEO length, approved image dimensions/hash and content approval hash. Duplicate evidence is explicitly a local snapshot, not a live scan. Reports are saved separately, timestamped and bound to a product revision; edits invalidate their currentness. Re-run to detect later image/source changes. A successful diagnostic job does not approve a product or authorize publication.

Haravan: safe_publish.py, agent_operations.py and configuration are unchanged. No new publishing API route. Native Operations retains existing gates. No live shop mutation was performed.

Validation: 68 regression tests passed in the full local run plus an additional authenticated tool routing / return-SKU test passed separately; TypeScript and production Vite build passed. Tests use temporary workspaces; no live Gemini/Google/Haravan validation.

This release connects tools, not a background worker. Autonomous orchestration, retries/budget management and durable cloud storage remain follow-up work. Google service-account sync is still unverified. Public rendering needs browser acceptance.
