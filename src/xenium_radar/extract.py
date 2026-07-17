import re
from .models import Evidence
PATTERNS = {
 "GEO": r"\b(?:GSE|GSM|GDS)\d+\b", "BioStudies": r"\bS-BIAD\d+\b", "ENA": r"\b(?:PRJNA|PRJEB|SRP|ERP)\d+\b",
 "ArrayExpress": r"\bE-MTAB-\d+\b", "EGA": r"\bEGAS\d+\b", "dbGaP": r"\bphs\d+(?:\.v\d+\.p\d+)?\b",
 "China": r"\b(?:HRA|CRA)\d+\b", "Synapse": r"\bsyn\d+\b", "DOI": r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+"
}
def extract_identifiers(text: str, location="text") -> list[Evidence]:
    found=[]
    for pattern in PATTERNS.values():
        for match in re.finditer(pattern, text or "", re.I):
            start=max(0,match.start()-80); end=min(len(text),match.end()+80)
            found.append(Evidence(identifier=match.group(), location=location, text=text[start:end]))
    return found

def parse_size(value):
    if value is None or isinstance(value, int): return value
    match=re.match(r"\s*([\d.]+)\s*(B|KB|MB|GB|TB)?", str(value), re.I)
    if not match: return None
    return int(float(match.group(1))*1024**({"B":0,"KB":1,"MB":2,"GB":3,"TB":4}.get((match.group(2) or "B").upper(),0)))
