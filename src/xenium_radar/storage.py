import csv,json,sqlite3
from pathlib import Path
from .models import DatasetRecord
class Store:
 def __init__(self,path):
  Path(path).parent.mkdir(parents=True,exist_ok=True); self.db=sqlite3.connect(path)
  self.db.execute("CREATE TABLE IF NOT EXISTS records (record_key TEXT PRIMARY KEY, data TEXT NOT NULL, first_seen_at TEXT NOT NULL, last_checked_at TEXT NOT NULL, source_updated_at TEXT)")
 def upsert(self,record,key):
  payload=record.model_dump_json()
  self.db.execute("INSERT INTO records VALUES(?,?,?,?,?) ON CONFLICT(record_key) DO UPDATE SET data=excluded.data,last_checked_at=excluded.last_checked_at,source_updated_at=excluded.source_updated_at",(str(key),payload,record.first_seen_at.isoformat(),record.last_checked_at.isoformat(),record.source_updated_at.isoformat() if record.source_updated_at else None)); self.db.commit()
 def all(self): return [DatasetRecord.model_validate_json(x[0]) for x in self.db.execute("SELECT data FROM records ORDER BY last_checked_at DESC")]
 def export(self,directory):
  p=Path(directory);p.mkdir(parents=True,exist_ok=True); rows=[r.model_dump(mode="json") for r in self.all()]
  (p/"records.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
  flat=[]
  for row in rows: row["file_manifest"]=json.dumps(row["file_manifest"]);row["evidence"]=json.dumps(row["evidence"]); flat.append(row)
  if flat:
   with (p/"records.csv").open("w",newline="",encoding="utf-8") as f: w=csv.DictWriter(f,fieldnames=flat[0]);w.writeheader();w.writerows(flat)
  else:(p/"records.csv").write_text("",encoding="utf-8")
  return p
