from pathlib import Path
import yaml

def load_config(path: str | Path = "config/settings.yaml") -> dict:
    with Path(path).open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)
