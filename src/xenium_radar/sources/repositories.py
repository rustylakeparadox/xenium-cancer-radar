from .base import BaseSource
from ..models import DatasetRecord,FileEntry
from ..extract import parse_size, extract_identifiers
class GEOSource(BaseSource):
 name="geo"
 def search(self,query):
  base="https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
  ids=self.http.get(base+"/esearch.fcgi",params={"db":"gds","term":query,"retmode":"json","retmax":100}).json()["esearchresult"]["idlist"]
  if not ids:return []
  rows=self.http.get(base+"/esummary.fcgi",params={"db":"gds","id":",".join(ids),"retmode":"json"}).json()["result"]
  return [DatasetRecord(title=rows[i].get("title","Untitled"),accession=rows[i].get("accession"),repository="GEO",dataset_url=f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={rows[i].get('accession')}",species=rows[i].get("taxon"),source=self.name,raw=rows[i]) for i in ids]
 def file_manifest(self,accession):
  url=f"https://ftp.ncbi.nlm.nih.gov/geo/series/{accession[:-3]}nnn/{accession}/suppl/"
  text=self.http.get(url).text
  import re
  matches = re.findall(
   r'href="([^"]+)"[^\n]*?(\d+(?:\.\d+)?)\s*([KMGTPE]?B)\b',
   text,
   re.I,
  )
  return [
   FileEntry(name=name, url=url + name, size_bytes=parse_size(number + " " + unit))
   for name, number, unit in matches
  ]
class BioStudiesSource(BaseSource):
 name="biostudies"
 def search(self,query):
  rows=self.http.get("https://www.ebi.ac.uk/biostudies/api/v1/search",params={"query":query,"pageSize":100}).json().get("hits",[])
  limit=self.config.get("enrichment",{}).get("max_details_per_source",50); out=[]
  for index,hit in enumerate(rows):
   accession=hit.get("accession"); url=f"https://www.ebi.ac.uk/biostudies/studies/{accession}"
   detail={}; text=" ".join(str(value) for value in hit.values() if value)
   files=[]
   if accession and index < limit:
    try:
     detail=self.http.get(f"https://www.ebi.ac.uk/biostudies/api/v1/studies/{accession}").json()
     text += " " + self._flatten_text(detail)
     files=self._files(detail)
    except Exception as exc: print(f"ENRICHMENT_ERROR source=biostudies id={accession} error={exc}")
   evidence=extract_identifiers(text,"repository_detail")
   out.append(DatasetRecord(title=hit.get("title") or accession or "Untitled",accession=accession,repository="BioStudies",dataset_url=url,file_manifest=files,file_count=len(files),total_size_bytes=sum(f.size_bytes or 0 for f in files) or None,downloadable=True if files else None,evidence=evidence,evidence_text=text,source=self.name,raw={"hit":hit,"detail":detail}))
  return out
 @staticmethod
 def _flatten_text(value):
  if isinstance(value,dict): return " ".join(BioStudiesSource._flatten_text(v) for v in value.values())
  if isinstance(value,list): return " ".join(BioStudiesSource._flatten_text(v) for v in value)
  return str(value) if value is not None else ""
 @staticmethod
 def _files(value):
  found=[]
  def visit(node):
   if isinstance(node,dict):
    path=node.get("path") or node.get("name")
    if path and any(key in node for key in ("size","sizeBytes","fileSize")):
     size=parse_size(node.get("sizeBytes") or node.get("fileSize") or node.get("size"))
     link=node.get("url") or node.get("downloadUrl") or ""
     found.append(FileEntry(name=str(path),url=str(link),size_bytes=size))
    for child in node.values(): visit(child)
   elif isinstance(node,list):
    for child in node: visit(child)
  visit(value); return found
class JsonRepositorySource(BaseSource):
 endpoint=""; repository=""; name=""
 def search(self,query):
  data=self.http.get(self.endpoint,params={"q":query}).json(); rows=data.get("hits",data.get("items",data if isinstance(data,list) else []))
  return [DatasetRecord(title=x.get("title") or x.get("name") or "Untitled",accession=str(x.get("id",x.get("name",""))),repository=self.repository,dataset_url=x.get("html_url") or x.get("url"),source=self.name,raw=x) for x in rows]
class ZenodoSource(JsonRepositorySource): endpoint="https://zenodo.org/api/records"; repository="Zenodo"; name="zenodo"
class FigshareSource(JsonRepositorySource): endpoint="https://api.figshare.com/v2/articles"; repository="Figshare"; name="figshare"
class HuggingFaceSource(JsonRepositorySource): endpoint="https://huggingface.co/api/datasets"; repository="Hugging Face"; name="huggingface"
class TenXSource(JsonRepositorySource):
 endpoint="https://www.10xgenomics.com/api/resources"; repository="10x Genomics"; name="tenx"
