import re
from .models import DatasetRecord
def norm(value): return re.sub(r"\W+","",(value or "").lower())
def key(record: DatasetRecord):
    # Accession remains in the key so distinct datasets attached to one paper survive.
    suffix=record.accession or ""
    if record.doi: return ("doi",record.doi.lower().removeprefix("https://doi.org/"),suffix)
    if record.pmid: return ("pmid",record.pmid,suffix)
    if record.accession: return ("accession",record.accession.upper())
    if record.title: return ("title",norm(record.title),suffix)
    return ("fallback",norm(record.title),norm(record.first_author),record.publication_date,suffix)
def deduplicate(records):
    out={}
    for record in records: out.setdefault(key(record),record)
    return list(out.values())
