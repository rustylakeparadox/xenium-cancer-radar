from .sources import *
from .classify import classify_xenium,biological_filter
from .dedupe import deduplicate,key
from .storage import Store
LITERATURE=[EuropePMCSource,CrossrefSource,PubMedSource,OpenAlexSource,BiorxivSource,MedrxivSource,ArxivSource]
REPOSITORIES=[GEOSource,BioStudiesSource,ZenodoSource,FigshareSource,HuggingFaceSource,TenXSource]
def run(config,kind="all"):
 classes=(LITERATURE if kind=="literature" else REPOSITORIES if kind=="repositories" else LITERATURE+REPOSITORIES); records=[]
 queries=["Xenium cancer","spatial transcriptomics cancer foundation model"]
 for cls in classes:
  if not config.get("sources",{}).get(cls.name,{}).get("enabled",True): continue
  for query in queries:
   try: records.extend(cls(config).search(query))
   except Exception as exc: print(f"{cls.name}: {exc}")
 for r in records:
  text=" ".join(filter(None,[r.title,r.evidence_text])); r.xenium_role,r.xenium_reason,r.confidence_score=classify_xenium(text)
  r.is_human,is_cancer=biological_filter(text,config["keywords"]["cancer"]); r.manual_review_required=not (r.is_human and is_cancer and r.confidence_score>=.7)
 store=Store(config["database"])
 for r in deduplicate(records): store.upsert(r,key(r))
 return records
