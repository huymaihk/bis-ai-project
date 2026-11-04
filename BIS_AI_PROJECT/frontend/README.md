# BIS React workspace

The AI Studio export is preserved at the owner's original AI folder. This copy adds
an authenticated live workspace backed by `bis_api.py`. Original prototype components
remain accessible only through the explicitly labelled 3D demo button.

## Build on a local disk

Use Node 22.12+ and npm. Prefer the C: Git checkout rather than Google Drive's virtual
filesystem for `node_modules` (Drive returned TAR_ENTRY_ERROR during installation).

```
npm ci
npm run lint
npm run build
```

From the BIS project folder, install the existing Python dependencies plus
`pip install -r requirements-bridge.txt`, then `python bis_api.py`.
Open http://127.0.0.1:8765. The API serves the built frontend from frontend/dist.
It uses the project's existing BIS_ACCESS_PIN configuration. No API keys belong in
frontend environment variables or browser JavaScript.

For development: run the Python bridge, then `npm run dev`; Vite proxies /api to
127.0.0.1:8765 and keeps the browser on one origin.

## Connected now

- Real cached products and persisted product drafts; optimistic revision check;
  edits invalidate approval and create versioned memory events.
- Allowlisted PDF/image library, PDF page images, authenticated original downloads.
- Knowledge retrieval from MemoryStore, notes/history/withdrawal with conflict checks.
- Existing job records; explicit Google sync request with actual returned state.

## Not connected yet

The prototype's 3D characters/conversation, extraction, web image search, generation,
image approval, live agent meetings and Haravan publishing are not connected in this
release. Live workspace disables publishing; the demo contains only simulated actions.
Do not remove that boundary or treat demo claims as completed work.

## Runtime limits

Run one API worker and use one editing interface at a time (Streamlit and React do not
share a cross-process editing lock). Sessions are in memory and restart requires login.
Default listener is loopback only. Public hosting requires HTTPS, persistent storage,
configured PIN and a reviewed deployment setup. This is not deployed by Streamlit Cloud
automatically. Browser appearance has not been visually verified due to denied access.
