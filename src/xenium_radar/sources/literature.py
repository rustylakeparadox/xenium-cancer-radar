from urllib.parse import quote
import re
import feedparser
from .base import BaseSource
from ..models import DatasetRecord, Evidence
from ..extract import extract_identifiers

class EuropePMCSource(BaseSource):
 name="europe_pmc"
 def search(self,query):
  url=f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={quote(query)}&format=json&resultType=core&pageSize=100"
  data=self.http.get(url).json(); out=[]
  max_fulltext=self.config.get("enrichment",{}).get("max_fulltext_per_query",20)
  for index,x in enumerate(data.get("resultList",{}).get("result",[])):
   abstract=x.get("abstractText") or ""; evidence=extract_identifiers(abstract,"abstract")
   availability=""
   if x.get("pmcid") and index < max_fulltext:
    try:
     full_url=f"https://www.ebi.ac.uk/europepmc/webservices/rest/{x['pmcid']}/fullTextXML"
     xml=self.http.get(full_url).text
     sections=re.findall(r"<sec[^>]*>.*?<title[^>]*>(.*?(?:data|code) availability.*?)</title>(.*?)</sec>",xml,re.I|re.S)
     availability=" ".join(re.sub(r"<[^>]+>"," ",title+body) for title,body in sections)
     evidence += [Evidence(**(item.model_dump() | {"source_url": full_url})) for item in extract_identifiers(availability,"data_availability")]
    except Exception as exc: print(f"ENRICHMENT_ERROR source=europe_pmc id={x.get('pmcid')} error={exc}")
   text=" ".join(filter(None,[x.get("title"),abstract,availability]))
   out.append(DatasetRecord(title=x.get("title") or "Untitled",doi=x.get("doi"),pmid=x.get("pmid"),pmcid=x.get("pmcid"),journal=x.get("journalTitle"),issn=x.get("journalIssn"),publisher=x.get("publisherName"),first_author=x.get("firstAuthor"),publication_date=x.get("firstPublicationDate"),paper_url=f"https://europepmc.org/article/{x.get('source','MED')}/{x.get('id','')}",evidence=evidence,evidence_text=text,source=self.name,raw=x))
  return out

class CrossrefSource(BaseSource):
 name="crossref"
 def search(self,query):
  items=self.http.get("https://api.crossref.org/works",params={"query":query,"rows":100}).json()["message"]["items"]
  return [DatasetRecord(title=(x.get("title") or ["Untitled"])[0],doi=x.get("DOI"),journal=(x.get("container-title") or [None])[0],container_title=(x.get("container-title") or [None])[0],publisher=x.get("publisher"),issn=(x.get("ISSN") or [None])[0],paper_url=x.get("URL"),evidence_text=" ".join(filter(None,[(x.get("title") or [""])[0],x.get("abstract")])),source=self.name,raw=x) for x in items]
class PubMedSource(BaseSource):
 name="pubmed"
 def search(self,query):
  base="https://eutils.ncbi.nlm.nih.gov/entrez/eutils"; ids=self.http.get(base+"/esearch.fcgi",params={"db":"pubmed","term":query,"retmode":"json","retmax":100}).json()["esearchresult"]["idlist"]
  if not ids:return []
  data=self.http.get(base+"/esummary.fcgi",params={"db":"pubmed","id":",".join(ids),"retmode":"json"}).json()["result"]
  return [DatasetRecord(title=data[i].get("title","Untitled"),pmid=i,journal=data[i].get("fulljournalname"),publication_date=data[i].get("pubdate"),paper_url=f"https://pubmed.ncbi.nlm.nih.gov/{i}/",evidence_text=data[i].get("title"),source=self.name,raw=data[i]) for i in ids]
class OpenAlexSource(BaseSource):
 name="openalex"
 def search(self,query):
  rows=self.http.get("https://api.openalex.org/works",params={"search":query,"per-page":100}).json().get("results",[])
  return [DatasetRecord(title=x.get("title") or "Untitled",doi=x.get("doi"),paper_url=x.get("id"),publication_date=x.get("publication_date"),evidence_text=x.get("title"),source=self.name,raw=x) for x in rows]
class PreprintSource(BaseSource):
 server="biorxiv"; name="biorxiv"
 def search(self,query):
  rows=self.http.get(f"https://api.biorxiv.org/details/{self.server}/2020-01-01/2030-01-01/0").json().get("collection",[])
  terms=[term.strip('"').lower() for term in query.split() if len(term)>3]
  out=[]
  for x in rows:
   text=x.get("title","")+" "+x.get("abstract","")
   if any(term in text.lower() for term in terms): out.append(DatasetRecord(title=x["title"],doi=x.get("doi"),publication_date=x.get("date"),paper_url=f"https://doi.org/{x.get('doi')}",evidence_text=text,source=self.name,raw=x))
  return out
class BiorxivSource(PreprintSource): pass
class MedrxivSource(PreprintSource): server="medrxiv"; name="medrxiv"
class ArxivSource(BaseSource):
 name="arxiv"
 def search(self,query):
  feed=feedparser.loads(self.http.get("https://export.arxiv.org/api/query",params={"search_query":"all:"+query,"max_results":100}).text)
  return [DatasetRecord(title=e.title,doi=e.get("arxiv_doi"),publication_date=e.get("published"),paper_url=e.link,evidence_text=e.title+" "+e.get("summary",""),source=self.name,raw=dict(e)) for e in feed.entries]
