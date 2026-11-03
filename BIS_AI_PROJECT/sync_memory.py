"""Run after code/document updates: python sync_memory.py --record-update "what changed"."""
import argparse
import json
from pathlib import Path
from persistent_memory import MemoryStore, sync_configured


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--record-update", help="Verified change summary, limitations and next steps")
    parser.add_argument("--local-only", action="store_true")
    args = parser.parse_args()
    store = MemoryStore(Path(__file__).parent)
    # Pull remote state before refreshing local documents, preserving concurrent revisions.
    first = {"state": "local"} if args.local_only else sync_configured(store)
    changed = store.refresh_sources()
    if args.record_update:
        store.append("update", args.record_update, actor="developer", source="release notes")
    output = store.root / "CURRENT_MEMORY.md"
    output.write_text(store.export_markdown(), encoding="utf-8")
    result = first if args.local_only else sync_configured(store)
    print(json.dumps({"sources_updated": changed, "events": len(store.events()),
                      "sync": result, "read_errors": len(store.read_errors)}, ensure_ascii=False))
    return 0 if result["state"] in {"local", "synced"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

