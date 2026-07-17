import responses

from xenium_radar.dedupe import deduplicate
from xenium_radar.extract import extract_identifiers, parse_size
from xenium_radar.http import HttpClient
from xenium_radar.models import DatasetRecord
from xenium_radar.sources import GEOSource


def identifiers(text: str) -> set[str]:
    return {item.identifier for item in extract_identifiers(text, "Data Availability")}


def test_geo_and_data_availability():
    assert "GSE311609" in identifiers("Data Availability: deposited under GSE311609.")


def test_biostudies():
    assert "S-BIAD2146" in identifiers("Files: S-BIAD2146")


def test_size():
    assert parse_size("1.5 GB") == 1610612736


def test_doi_dedupe():
    first = DatasetRecord(title="A", doi="10.1/x")
    second = DatasetRecord(title="Other", doi="https://doi.org/10.1/x")
    assert len(deduplicate([first, second])) == 1


@responses.activate
def test_retry_after_server_error():
    url = "https://example.test/x"
    responses.get(url, status=500)
    responses.get(url, json={"ok": 1})
    client = HttpClient({"network": {"timeout": 0.01, "retries": 1, "backoff_factor": 0, "user_agent": "test-agent"}})
    assert client.get(url).json()["ok"] == 1
    assert len(responses.calls) == 2


@responses.activate
def test_geo_manifest_mock():
    html = '<a href="cells.parquet">cells.parquet</a> 1.5 GB\n<a href="experiment.xenium">experiment.xenium</a> 2 KB'
    responses.get("https://ftp.ncbi.nlm.nih.gov/geo/series/GSE311nnn/GSE311609/suppl/", body=html)
    files = GEOSource({"network": {"timeout": 1, "retries": 0, "user_agent": "test"}}).file_manifest("GSE311609")
    assert [item.name for item in files] == ["cells.parquet", "experiment.xenium"]
