"""
BIS Textile AI - Main Pipeline Runner (Multi-Agent Team Architecture)
Coordinates Agent_Leader, Agent_Technical, Agent_Operations.
"""
import sys
import os
import argparse
from pathlib import Path

# Unbuffered output
try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

PROJECT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_DIR))

from agent_leader import AgentLeader

def parse_args():
    parser = argparse.ArgumentParser(description="BIS Textile Multi-Agent Team Pipeline")
    parser.add_argument("--pdf", default=str(PROJECT_DIR / "catalogue_sample.pdf"), help="Đường dẫn file PDF catalogue")
    parser.add_argument("--sync-haravan", action="store_true", help="Ủy quyền đẩy các sản phẩm APPROVED lên Haravan")
    parser.add_argument("--max-pages", type=int, default=None, help="Giới hạn số trang xử lý")
    return parser.parse_args()

def main():
    args = parse_args()
    leader = AgentLeader(PROJECT_DIR)

    if args.sync_haravan:
        leader.request_haravan_sync()
    else:
        leader.run_catalogue_pipeline(args.pdf, max_pages=args.max_pages)

if __name__ == "__main__":
    main()
