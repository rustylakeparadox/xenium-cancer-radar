import re

def classify_xenium(text: str):
    t=(text or "").lower()
    if not "xenium" in t: return "mentioned_only", "Xenium is not substantively described", .2
    if re.search(r"validat(?:e|ed|ion).{0,80}xenium|xenium.{0,80}validat", t): return "validation_dataset", "Xenium is explicitly used for validation", .82
    if re.search(r"download(?:ed)?|publicly available|previously published|re-?used", t) and re.search(r"xenium",t): return "reused_public_dataset", "Text indicates reuse of public Xenium data", .78
    if re.search(r"(?:generated|profiled|performed|assayed|analy[sz]ed).{0,80}(?:using|with)?\s*xenium|xenium.{0,80}(?:generated|profil)",t): return "primary_dataset", "New profiling/generation with Xenium is stated", .9
    return "uncertain", "Xenium context is insufficient", .45

def biological_filter(text: str, cancer_keywords=None):
    t=(text or "").lower(); cancers=cancer_keywords or ["cancer","tumor","tumour","carcinoma","sarcoma","lymphoma","leukemia","melanoma","glioma","neoplasm","metastasis"]
    human=bool(re.search(r"\bhuman\b|homo sapiens|patient",t)); mouse=bool(re.search(r"\bmouse\b|\bmice\b|mus musculus",t))
    return (human and not (mouse and not human)), any(k in t for k in cancers)
