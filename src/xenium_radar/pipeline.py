from .classify import biological_filter, classify_xenium
from .dedupe import deduplicate, key
from .sources import (
    ArxivSource, BioStudiesSource, BiorxivSource, CrossrefSource,
    EuropePMCSource, FigshareSource, GEOSource, HuggingFaceSource,
    MedrxivSource, OpenAlexSource, PubMedSource, TenXSource, ZenodoSource,
)
from .storage import Store

LITERATURE = [
    EuropePMCSource, CrossrefSource, PubMedSource, OpenAlexSource,
    BiorxivSource, MedrxivSource, ArxivSource,
]
REPOSITORIES = [
    GEOSource, BioStudiesSource, ZenodoSource, FigshareSource,
    HuggingFaceSource, TenXSource,
]


def run(config: dict, kind: str = "all"):
    classes = (
        LITERATURE if kind == "literature"
        else REPOSITORIES if kind == "repositories"
        else LITERATURE + REPOSITORIES
    )
    store = Store(config["database"])
    # GitHub runners are ephemeral. Rehydrate history from the committed export.
    store.import_json(f'{config["exports"]}/records.json', key)
    records = []
    queries = ["Xenium cancer", "spatial transcriptomics cancer foundation model"]
    for source_class in classes:
        if not config.get("sources", {}).get(source_class.name, {}).get("enabled", True):
            continue
        for query in queries:
            try:
                records.extend(source_class(config).search(query))
            except Exception as exc:
                print(f"{source_class.name}: {exc}")
    for record in records:
        text = " ".join(filter(None, [record.title, record.evidence_text]))
        record.xenium_role, record.xenium_reason, record.confidence_score = classify_xenium(text)
        record.is_human, is_cancer = biological_filter(text, config["keywords"]["cancer"])
        record.manual_review_required = not (
            record.is_human and is_cancer and record.confidence_score >= 0.7
        )
    for record in deduplicate(records):
        store.upsert(record, key(record))
    return records
