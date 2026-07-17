"""Evidence-based triage for high-precision radar records."""

import re
from pathlib import PurePosixPath

XENIUM_FILE_MARKERS = (
    "experiment.xenium", "transcripts.parquet", "transcripts.csv.gz",
    "cells.parquet", "cells.csv.gz", "cell_feature_matrix.h5",
    "cell_boundaries.parquet", "morphology.ome.tif", "gene_panel.json",
)


def contains_any(text: str, terms: list[str]) -> bool:
    lowered = (text or "").lower()
    return any(term.lower() in lowered for term in terms)


def classify_xenium(text: str, file_names: list[str] | None = None):
    lowered = (text or "").lower()
    file_names = [PurePosixPath(name).name.lower() for name in (file_names or [])]
    file_evidence = [name for name in file_names if any(marker in name for marker in XENIUM_FILE_MARKERS)]
    if "xenium" not in lowered and not file_evidence:
        return "uncertain", "No Xenium text or characteristic Xenium files found", 0.0, False
    if re.search(r"validat(?:e|ed|ion).{0,100}xenium|xenium.{0,100}validat", lowered):
        return "validation_dataset", "Xenium is explicitly used for validation", 0.82, True
    if re.search(r"download(?:ed)?|publicly available|previously published|re-?used", lowered):
        return "reused_public_dataset", "Text indicates reuse of public Xenium data", 0.78, True
    if re.search(r"(?:generated|profiled|performed|assayed).{0,100}(?:using|with)?\s*xenium|xenium.{0,100}(?:generated|profil)", lowered):
        return "primary_dataset", "New profiling/generation with Xenium is stated", 0.90, True
    if file_evidence:
        return "uncertain", f"Characteristic Xenium files found: {', '.join(file_evidence[:3])}", 0.72, True
    return "mentioned_only", "Xenium is mentioned without evidence of dataset generation or reuse", 0.40, True


def biological_filter(text: str, cancer_keywords=None):
    lowered = (text or "").lower()
    cancers = cancer_keywords or ["cancer", "tumor", "tumour", "carcinoma", "sarcoma", "lymphoma", "leukemia", "melanoma", "glioma", "neoplasm", "metastasis"]
    human_positive = bool(re.search(r"\bhuman(?:s)?\b|homo sapiens|\bpatients?\b|patient-derived", lowered))
    non_human = bool(re.search(r"\bmouse\b|\bmice\b|mus musculus|\brat\b|rattus norvegicus|zebrafish", lowered))
    is_human = True if human_positive else False if non_human else None
    is_cancer = True if contains_any(lowered, cancers) else None
    return is_human, is_cancer


def triage_record(record, config: dict):
    """Mutate a record with transparent evidence scores and a review status."""
    evidence_text = " ".join(e.text for e in record.evidence)
    text = " ".join(filter(None, [record.title, record.evidence_text, evidence_text, record.species, record.tissue]))
    files = [entry.name for entry in record.file_manifest]
    role, reason, xenium_score, is_xenium = classify_xenium(text, files)
    is_human, is_cancer = biological_filter(text, config["keywords"]["cancer"])
    foundation = contains_any(text, config["keywords"]["foundation_model"])

    record.xenium_role = role
    record.xenium_reason = reason
    record.is_xenium_related = is_xenium
    record.is_human = is_human
    record.is_cancer = is_cancer
    record.foundation_model_related = foundation
    record.xenium_confidence = xenium_score
    record.human_confidence = 0.9 if is_human is True else 0.9 if is_human is False else 0.0
    record.cancer_confidence = 0.8 if is_cancer is True else 0.0
    record.confidence_score = round((xenium_score + record.human_confidence + record.cancer_confidence) / 3, 3)

    reasons = []
    if not is_xenium and not foundation:
        record.record_status = "rejected"
        reasons.append("no_xenium_or_foundation_model_evidence")
    elif foundation:
        record.record_kind = "foundation_model"
        record.record_status = "accepted" if contains_any(text, ["cancer", "pathology", "single-cell", "spatial transcriptomics", "histology", "h&e"]) else "manual_review"
        if record.record_status != "accepted": reasons.append("foundation_model_domain_uncertain")
    elif is_human is True and is_cancer is True and xenium_score >= 0.70:
        record.record_kind = "xenium_dataset"
        record.record_status = "accepted"
    else:
        record.record_kind = "xenium_dataset"
        record.record_status = "manual_review"
        if is_human is None: reasons.append("human_species_unconfirmed")
        if is_human is False: reasons.append("non_human_evidence")
        if is_cancer is None: reasons.append("cancer_context_unconfirmed")
        if xenium_score < 0.70: reasons.append("xenium_dataset_role_uncertain")
    record.rejection_reasons = reasons
    record.manual_review_required = record.record_status == "manual_review"
    return record
