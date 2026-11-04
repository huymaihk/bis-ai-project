"""Small durable job journal. Exceptions never become success or learned facts."""
from datetime import datetime,timezone
import uuid
from persistent_memory import MemoryStore, atomic_json, clean
from product_quality import fingerprint

class JobRunner:
    def __init__(self,workspace):
        self.memory=MemoryStore(workspace)
        self.folder=self.memory.root/"jobs"
        self.folder.mkdir(exist_ok=True)

    def run(self,task,inputs,fn):
        job={"id":uuid.uuid4().hex,"task":task,"input_hash":fingerprint(inputs),
             "state":"RUNNING","started_at":datetime.now(timezone.utc).isoformat()}
        path=self.folder/(job["id"]+".json")
        atomic_json(path,job)
        try:
            output=fn()
        except Exception as exc:
            job.update(state="FAILED",error=type(exc).__name__,detail=clean(str(exc))[:400])
            atomic_json(path,job)
            self.memory.append("update",f'{task}: FAILED ({type(exc).__name__}); chưa có kết quả.',
                               source="job:"+job["id"])
            raise
        job.update(state="COMPLETED",finished_at=datetime.now(timezone.utc).isoformat(),
                   output_hash=fingerprint(output))
        atomic_json(path,job)
        self.memory.append("update",f'{task}: hoàn tất bước xử lý, không thay cho nghiệm thu chất lượng.',
                           source="job:"+job["id"])
        return output

    def list_jobs(self):
        import json
        rows=[]
        for p in self.folder.glob("*.json"):
            try:
                rows.append(json.loads(p.read_text(encoding="utf-8")))
            except (ValueError,OSError):
                continue
        return sorted(rows,key=lambda x:x["started_at"],reverse=True)

