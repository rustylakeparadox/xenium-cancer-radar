"""SQLite persistence and durable CSV/JSON exports."""

import csv
import json
import sqlite3
from datetime import date, datetime
from pathlib import Path

from .models import DatasetRecord


class Store:
    def __init__(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute(
            """CREATE TABLE IF NOT EXISTS records (
                record_key TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                first_seen_at TEXT NOT NULL,
                last_checked_at TEXT NOT NULL,
                source_updated_at TEXT
            )"""
        )
        self.db.commit()

    def upsert(self, record: DatasetRecord, record_key: object) -> None:
        serialized_key = str(record_key)
        existing = self.db.execute(
            "SELECT first_seen_at FROM records WHERE record_key = ?", (serialized_key,)
        ).fetchone()
        if existing:
            # Preserve the authoritative historical value in both the SQL column and JSON.
            record.first_seen_at = datetime.fromisoformat(existing[0])
        payload = record.model_dump_json()
        self.db.execute(
            """INSERT INTO records VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(record_key) DO UPDATE SET
                 data = excluded.data,
                 last_checked_at = excluded.last_checked_at,
                 source_updated_at = excluded.source_updated_at""",
            (
                serialized_key,
                payload,
                record.first_seen_at.isoformat(),
                record.last_checked_at.isoformat(),
                record.source_updated_at.isoformat() if record.source_updated_at else None,
            ),
        )
        self.db.commit()

    def all(self) -> list[DatasetRecord]:
        return [
            DatasetRecord.model_validate_json(row[0])
            for row in self.db.execute("SELECT data FROM records ORDER BY last_checked_at DESC")
        ]

    def import_json(self, path: str | Path, key_function) -> int:
        """Restore the SQLite cache from the versioned aggregate JSON export."""
        source = Path(path)
        if not source.exists() or self.db.execute("SELECT 1 FROM records LIMIT 1").fetchone():
            return 0
        records = json.loads(source.read_text(encoding="utf-8"))
        for item in records:
            record = DatasetRecord.model_validate(item)
            self.upsert(record, key_function(record))
        return len(records)

    def export(self, directory: str | Path, snapshot_date: date | None = None) -> Path:
        output = Path(directory)
        output.mkdir(parents=True, exist_ok=True)
        all_rows = [record.model_dump(mode="json") for record in self.all()]
        accepted = [row for row in all_rows if row["record_status"] == "accepted"]
        review = [row for row in all_rows if row["record_status"] == "manual_review"]
        datasets = [row for row in accepted if row["record_kind"] == "xenium_dataset"]
        models = [row for row in accepted if row["record_kind"] == "foundation_model"]

        self._write_json(output / "records.json", accepted)
        self._write_json(output / "candidates.json", all_rows)
        self._write_json(output / "manual_review.json", review)
        self._write_json(output / "xenium_datasets.json", datasets)
        self._write_json(output / "foundation_models.json", models)
        self._write_csv(output / "records.csv", self._csv_rows(accepted))
        self._write_csv(output / "manual_review.csv", self._csv_rows(review))

        snapshot = output / "history" / (snapshot_date or date.today()).isoformat()
        snapshot.mkdir(parents=True, exist_ok=True)
        self._write_json(snapshot / "records.json", accepted)
        self._write_json(snapshot / "candidates.json", all_rows)
        self._write_csv(snapshot / "records.csv", self._csv_rows(accepted))
        report = {
            "total_candidates": len(all_rows), "accepted": len(accepted),
            "manual_review": len(review),
            "rejected": sum(row["record_status"] == "rejected" for row in all_rows),
            "xenium_datasets": len(datasets), "foundation_models": len(models),
        }
        self._write_json(output / "quality_report.json", report)
        return output

    @staticmethod
    def _write_json(path: Path, value) -> None:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _csv_rows(rows: list[dict]) -> list[dict]:
        result = []
        for source in rows:
            row = dict(source)
            row["file_manifest"] = json.dumps(row["file_manifest"], ensure_ascii=False)
            row["evidence"] = json.dumps(row["evidence"], ensure_ascii=False)
            row["rejection_reasons"] = json.dumps(row["rejection_reasons"], ensure_ascii=False)
            result.append(row)
        return result

    @staticmethod
    def _write_csv(path: Path, rows: list[dict]) -> None:
        if not rows:
            path.write_text("", encoding="utf-8")
            return
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0])
            writer.writeheader()
            writer.writerows(rows)
