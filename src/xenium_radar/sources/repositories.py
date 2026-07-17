from .base import BaseSource
from ..models import DatasetRecord,FileEntry
from ..extract import parse_size
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
  return [FileEntry(name=n,url=url+n,size_bytes=parse_size(s)) for n,s in re.findall(r'href="([^"]+)"[^\n]*?\s([\d.]+[KMG]?B)',text,re.I)]
class BioStudiesSource(BaseSource):
 name="biostudies"
 def search(self,query):
  rows=self.http.get("https://www.ebi.ac.uk/biostudies/api/v1/search",params={"query":query,"pageSize":100}).json().get("hits",[])
  return [DatasetRecord(title=x.get("title") or x.get("accession","Untitled"),accession=x.get("accession"),repository="BioStudies",dataset_url=f"https://www.ebi.ac.uk/biostudies/studies/{x.get('accession')}",source=self.name,raw=x) for x in rows]
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
