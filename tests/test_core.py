import requests,responses
from xenium_radar.extract import extract_identifiers,parse_size
from xenium_radar.classify import classify_xenium,biological_filter
from xenium_radar.models import DatasetRecord
from xenium_radar.dedupe import deduplicate
from xenium_radar.http import HttpClient
from xenium_radar.sources import GEOSource

def ids(s): return {x.identifier for x in extract_identifiers(s,"Data Availability")}
def test_geo_and_data_availability(): assert "GSE311609" in ids("Data Availability: deposited under GSE311609.")
def test_biostudies(): assert "S-BIAD2146" in ids("Files: S-BIAD2146")
def test_roles():
 assert classify_xenium("We profiled new patient sections using Xenium")[0]=="primary_dataset"
 assert classify_xenium("Xenium was used to validate the discovery cohort")[0]=="validation_dataset"
def test_species_and_tissue_filters():
 assert biological_filter("human patients with lung cancer")== (True,True)
 assert biological_filter("Mus musculus normal brain")==(False,False)
def test_size(): assert parse_size("1.5 GB")==1610612736
def test_doi_dedupe():
 a=DatasetRecord(title="A",doi="10.1/x");b=DatasetRecord(title="Other",doi="https://doi.org/10.1/x")
 assert len(deduplicate([a,b]))==1
@responses.activate
def test_retry_after_server_error():
 url="https://example.test/x";responses.get(url,status=500);responses.get(url,json={"ok":1})
 assert HttpClient({"network":{"timeout":.01,"retries":1,"backoff_factor":0,"user_agent":"test-agent"}}).get(url).json()["ok"]==1
 assert len(responses.calls)==2
@responses.activate
def test_geo_manifest_mock():
 html='<a href="cells.parquet">cells.parquet</a> 1.5 GB\n<a href="experiment.xenium">experiment.xenium</a> 2 KB'
 responses.get("https://ftp.ncbi.nlm.nih.gov/geo/series/GSE311nnn/GSE311609/suppl/",body=html)
 files=GEOSource({"network":{"timeout":1,"retries":0,"user_agent":"test"}}).file_manifest("GSE311609")
 assert [f.name for f in files]==["cells.parquet","experiment.xenium"]

def test_first_seen_is_preserved_on_upsert(tmp_path):
 from datetime import datetime, timezone
 from xenium_radar.storage import Store
 from xenium_radar.dedupe import key
 store=Store(str(tmp_path/"radar.sqlite3"))
 original=DatasetRecord(title="A",doi="10.1/history",first_seen_at=datetime(2024,1,1,tzinfo=timezone.utc))
 store.upsert(original,key(original))
 refreshed=DatasetRecord(title="A updated",doi="10.1/history",first_seen_at=datetime(2026,1,1,tzinfo=timezone.utc))
 store.upsert(refreshed,key(refreshed))
 assert store.all()[0].first_seen_at==datetime(2024,1,1,tzinfo=timezone.utc)

def test_export_snapshot_and_restore(tmp_path):
 from datetime import date
 from xenium_radar.storage import Store
 from xenium_radar.dedupe import key
 first=Store(str(tmp_path/"first.sqlite3")); record=DatasetRecord(title="Durable",doi="10.1/durable")
 first.upsert(record,key(record)); exports=first.export(tmp_path/"exports",date(2026,7,17))
 assert (exports/"records.json").exists()
 assert (exports/"records.csv").exists()
 assert (exports/"history"/"2026-07-17"/"records.json").exists()
 restored=Store(str(tmp_path/"second.sqlite3"))
 assert restored.import_json(exports/"records.json",key)==1
 assert restored.all()[0].doi=="10.1/durable"
