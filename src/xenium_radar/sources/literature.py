from urllib.parse import quote
import feedparser
from .base import BaseSource
from ..models import DatasetRecord
from ..extract import extract_identifiers

class EuropePMCSource(BaseSource):
 name="europe_pmc"
 def search(self,query):
  data=self.http.get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={quote(query)}&format=json&pageSize=100").json()
  out=[]
  for x in data.get("resultList",{}).get("result",[]):
   text=" ".join(filter(None,[x.get("title"),x.get("authorString")]))
   out.append(DatasetRecord(title=x.get("title") or "Untitled",doi=x.get("doi"),pmid=x.get("pmid"),pmcid=x.get("pmcid"),journal=x.get("journalTitle"),issn=x.get("journalIssn"),publication_date=x.get("firstPublicationDate"),paper_url=f"https://europepmc.org/article/{x.get('source','MED')}/{x.get('id','')}",evidence=extract_identifiers(text,"metadata"),source=self.name,raw=x))
  return out
class CrossrefSource(BaseSource):
 name="crossref"
 def search(self,query):
  items=self.http.get("https://api.crossref.org/works",params={"query":query,"rows":100}).json()["message"]["items"]
  return [DatasetRecord(title=(x.get("title") or ["Untitled"])[0],doi=x.get("DOI"),journal=(x.get("container-title") or [None])[0],container_title=(x.get("container-title") or [None])[0],publisher=x.get("publisher"),issn=(x.get("ISSN") or [None])[0],paper_url=x.get("URL"),source=self.name,raw=x) for x in items]
class PubMedSource(BaseSource):
 name="pubmed"
 def search(self,query):
  base="https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
  ids=self.http.get(base+"/esearch.fcgi",params={"db":"pubmed","term":query,"retmode":"json","retmax":100}).json()["esearchresult"]["idlist"]
  if not ids:return []
  data=self.http.get(base+"/esummary.fcgi",params={"db":"pubmed","id":",".join(ids),"retmode":"json"}).json()["result"]
  return [DatasetRecord(title=data[i].get("title","Untitled"),pmid=i,journal=data[i].get("fulljournalname"),publication_date=data[i].get("pubdate"),paper_url=f"https://pubmed.ncbi.nlm.nih.gov/{i}/",source=self.name,raw=data[i]) for i in ids]
class OpenAlexSource(BaseSource):
 name="openalex"
 def search(self,query):
  rows=self.http.get("https://api.openalex.org/works",params={"search":query,"per-page":100}).json().get("results",[])
  return [DatasetRecord(title=x.get("title") or "Untitled",doi=x.get("doi"),paper_url=x.get("id"),publication_date=x.get("publication_date"),source=self.name,raw=x) for x in rows]
class PreprintSource(BaseSource):
 server="biorxiv"; name="biorxiv"
 def search(self,query):
  rows=self.http.get(f"https://api.biorxiv.org/details/{self.server}/2020-01-01/2030-01-01/0").json().get("collection",[])
  return [DatasetRecord(title=x["title"],doi=x.get("doi"),publication_date=x.get("date"),paper_url=f"https://doi.org/{x.get('doi')}",source=self.name,raw=x) for x in rows if query.lower() in (x.get("title","")+x.get("abstract","")).lower()]
class BiorxivSource(PreprintSource): pass
class MedrxivSource(PreprintSource): server="medrxiv"; name="medrxiv"
class ArxivSource(BaseSource):
 name="arxiv"
 def search(self,query):
  response=self.http.get("https://export.arxiv.org/api/query",params={"search_query":"all:"+query,"max_results":100})
  feed=feedparser.loads(response.text)
  return [DatasetRecord(title=e.title,doi=e.get("arxiv_doi"),publication_date=e.get("published"),paper_url=e.link,source=self.name,raw=dict(e)) for e in feed.entries]
