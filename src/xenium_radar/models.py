from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, Field

def now(): return datetime.now(timezone.utc)

class Evidence(BaseModel):
    identifier: str
    location: str = "unknown"
    text: str
    source_url: str | None = None

class FileEntry(BaseModel):
    name: str
    url: str
    size_bytes: int | None = None
    format: str | None = None
    http_status: int | None = None
    content_type: str | None = None
    supports_range: bool | None = None
    last_modified: str | None = None
    login_required: bool = False
    publicly_downloadable: bool | None = None

class DatasetRecord(BaseModel):
    title: str
    doi: str | None = None
    pmid: str | None = None
    pmcid: str | None = None
    journal: str | None = None
    issn: str | None = None
    publisher: str | None = None
    container_title: str | None = None
    first_author: str | None = None
    publication_date: str | None = None
    publication_tier: str | None = None
    paper_url: str | None = None
    accession: str | None = None
    repository: str | None = None
    dataset_url: str | None = None
    downloadable: bool | None = None
    download_status: str | None = None
    total_size_bytes: int | None = None
    file_count: int = 0
    file_manifest: list[FileEntry] = Field(default_factory=list)
    species: str | None = None
    is_human: bool | None = None
    is_cancer: bool | None = None
    is_xenium_related: bool | None = None
    cancer_type_raw: str | None = None
    cancer_type: str | None = None
    cancer_subtype: str | None = None
    tissue: str | None = None
    patient_count: int | None = None
    sample_count: int | None = None
    section_count: int | None = None
    cell_count: int | None = None
    gene_panel_size: int | None = None
    fresh_frozen_or_ffpe: str | None = None
    xenium_panel: str | None = None
    xenium_role: Literal["primary_dataset", "validation_dataset", "reused_public_dataset", "mentioned_only", "uncertain"] = "uncertain"
    xenium_reason: str | None = None
    paired_scrna: bool = False
    paired_snrna: bool = False
    paired_histology: bool = False
    paired_protein: bool = False
    paired_clinical: bool = False
    foundation_model_related: bool = False
    model_name: str | None = None
    model_task: str | None = None
    training_sample_count: int | None = None
    training_cell_count: int | None = None
    model_code_url: str | None = None
    model_weights_url: str | None = None
    training_data_public: bool | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    evidence_text: str | None = None
    confidence_score: float = 0.0
    xenium_confidence: float = 0.0
    human_confidence: float = 0.0
    cancer_confidence: float = 0.0
    record_kind: Literal["xenium_dataset", "foundation_model", "candidate"] = "candidate"
    record_status: Literal["accepted", "manual_review", "rejected"] = "manual_review"
    rejection_reasons: list[str] = Field(default_factory=list)
    manual_review_required: bool = True
    source_updated_at: datetime | None = None
    first_seen_at: datetime = Field(default_factory=now)
    last_checked_at: datetime = Field(default_factory=now)
    source: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict, exclude=True)
