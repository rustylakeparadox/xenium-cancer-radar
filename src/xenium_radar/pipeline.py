from .classify import triage_record
from .dedupe import deduplicate, key
from .sources import (
    ArxivSource, BioStudiesSource, BiorxivSource, CrossrefSource,
    EuropePMCSource, FigshareSource, GEOSource, HuggingFaceSource,
    MedrxivSource, OpenAlexSource, PubMedSource, TenXSource, ZenodoSource,
)
from .storage import Store

LITERATURE = [EuropePMCSource, CrossrefSource, PubMedSource, OpenAlexSource, BiorxivSource, MedrxivSource, ArxivSource]
REPOSITORIES = [GEOSource, BioStudiesSource, ZenodoSource, FigshareSource, HuggingFaceSource, TenXSource]


def build_queries(config: dict, kind: str) -> list[str]:
    if kind == "foundation":
        return [f'"{term}" cancer' for term in config["keywords"]["foundation_model"][:5]]
    return [
        '"Xenium" cancer human',
        '"Xenium In Situ" tumor patient',
        '"10x Xenium" carcinoma',
    ]


def run(config: dict, kind: str = "all"):
    classes = LITERATURE if kind == "literature" else REPOSITORIES if kind == "repositories" else LITERATURE + REPOSITORIES
    store = Store(config["database"])
    candidate_history = f'{config["exports"]}/candidates.json'
    restored = store.import_json(candidate_history, key)
    if not restored:
        # One-time migration from exports produced before candidate separation.
        store.import_json(f'{config["exports"]}/records.json', key)
    records = []
    queries = build_queries(config, "foundation" if kind == "foundation" else "xenium")
    if kind == "all": queries += build_queries(config, "foundation")
    for source_class in classes:
        if not config.get("sources", {}).get(source_class.name, {}).get("enabled", True): continue
        for query in queries:
            try: records.extend(source_class(config).search(query))
            except Exception as exc: print(f"SOURCE_ERROR source={source_class.name} query={query!r} error={exc}")
    for record in deduplicate(records):
        store.upsert(triage_record(record, config), key(record))
    return records
