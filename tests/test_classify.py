from xenium_radar.classify import biological_filter, classify_xenium, triage_record
from xenium_radar.models import DatasetRecord

CONFIG = {"keywords": {"cancer": ["cancer", "tumor"], "foundation_model": ["foundation model"]}}


def test_roles():
    assert classify_xenium("We profiled new patient sections using Xenium")[0] == "primary_dataset"
    assert classify_xenium("Xenium was used to validate the discovery cohort")[0] == "validation_dataset"


def test_species_and_tissue_filters_use_three_states():
    assert biological_filter("human patients with lung cancer") == (True, True)
    assert biological_filter("Mus musculus normal brain") == (False, None)


def test_low_quality_spatial_hit_is_rejected():
    record = DatasetRecord(title="A spatial clustering framework", repository="BioStudies")
    triage_record(record, CONFIG)
    assert record.record_status == "rejected"
    assert record.is_human is None
    assert "no_xenium_or_foundation_model_evidence" in record.rejection_reasons


def test_high_quality_human_cancer_xenium_is_accepted():
    record = DatasetRecord(title="Human lung cancer", evidence_text="We profiled patient tumor sections using Xenium.")
    triage_record(record, CONFIG)
    assert record.record_status == "accepted"
    assert record.record_kind == "xenium_dataset"
    assert record.is_human is True
    assert record.is_cancer is True
