from datetime import date, datetime, timezone

from xenium_radar.dedupe import key
from xenium_radar.models import DatasetRecord
from xenium_radar.storage import Store


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
