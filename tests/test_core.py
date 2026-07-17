from datetime import date, datetime, timezone

import responses

from xenium_radar.classify import biological_filter, classify_xenium, triage_record
from xenium_radar.dedupe import deduplicate, key
from xenium_radar.extract import extract_identifiers, parse_size
from xenium_radar.http import HttpClient
from xenium_radar.models import DatasetRecord
from xenium_radar.sources import GEOSource
from xenium_radar.storage import Store


def identifiers(text: str) -> set[str]:
    return {item.identifier for item in extract_identifiers(text, "Data Availability")}


def test_geo_and_data_availability():
    assert "GSE311609" in identifiers("Data Availability: deposited under GSE311609.")


def test_biostudies():
    assert "S-BIAD2146" in identifiers("Files: S-BIAD2146")


def test_roles():
    assert classify_xenium("We profiled new patient sections using Xenium")[0] == "primary_dataset"
    assert classify_xenium("Xenium was used to validate the discovery cohort")[0] == "validation_dataset"


def test_species_and_tissue_filters():
    assert biological_filter("human patients with lung cancer") == (True, True)
    # Normal tissue is not cancer-negative evidence; it means cancer context is unknown.
    assert biological_filter("Mus musculus normal brain") == (False, None)


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


def test_first_seen_is_preserved_on_upsert(tmp_path):
    store = Store(str(tmp_path / "radar.sqlite3"))
    original = DatasetRecord(title="A", doi="10.1/history", first_seen_at=datetime(2024, 1, 1, tzinfo=timezone.utc))
    store.upsert(original, key(original))
    refreshed = DatasetRecord(title="A updated", doi="10.1/history", first_seen_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
    store.upsert(refreshed, key(refreshed))
    assert store.all()[0].first_seen_at == datetime(2024, 1, 1, tzinfo=timezone.utc)


def test_export_snapshot_and_restore(tmp_path):
    first = Store(str(tmp_path / "first.sqlite3"))
    record = DatasetRecord(title="Durable", doi="10.1/durable", record_status="accepted", record_kind="xenium_dataset")
    first.upsert(record, key(record))
    exports = first.export(tmp_path / "exports", date(2026, 7, 17))
    assert (exports / "records.json").exists()
    assert (exports / "records.csv").exists()
    assert (exports / "history" / "2026-07-17" / "records.json").exists()
    restored = Store(str(tmp_path / "second.sqlite3"))
    assert restored.import_json(exports / "candidates.json", key) == 1
    assert restored.all()[0].doi == "10.1/durable"


def test_low_quality_spatial_hit_is_rejected():
    config = {"keywords": {"cancer": ["cancer", "tumor"], "foundation_model": ["foundation model"]}}
    record = DatasetRecord(title="A spatial clustering framework", repository="BioStudies")
    triage_record(record, config)
    assert record.record_status == "rejected"
    assert record.is_human is None
    assert "no_xenium_or_foundation_model_evidence" in record.rejection_reasons


def test_high_quality_human_cancer_xenium_is_accepted():
    config = {"keywords": {"cancer": ["cancer", "tumor"], "foundation_model": ["foundation model"]}}
    record = DatasetRecord(title="Human lung cancer", evidence_text="We profiled patient tumor sections using Xenium.")
    triage_record(record, config)
    assert record.record_status == "accepted"
    assert record.record_kind == "xenium_dataset"
    assert record.is_human is True and record.is_cancer is True
