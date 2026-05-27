from __future__ import annotations
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Optional
import yaml

CONFIG_FILENAME = "das.config.yaml"
SPEC_VERSION = "1.0"
VALID_CONTEXT_TYPES = {"client", "project", "dept", "none"}


@dataclass
class DASConfig:
    version: str
    corpus: str
    initialized: str
    address_separator: str
    manifest: str
    org: Optional[str] = None
    context_type: Optional[str] = None
    date_format: Optional[str] = None

    def __post_init__(self):
        if self.address_separator != ".":
            raise ValueError("address_separator must be '.'")
        if self.context_type and self.context_type not in VALID_CONTEXT_TYPES:
            raise ValueError(
                f"context_type must be one of {sorted(VALID_CONTEXT_TYPES)}"
            )


def load_config(corpus_root: Path) -> DASConfig:
    path = corpus_root / CONFIG_FILENAME
    if not path.exists():
        raise FileNotFoundError(f"{CONFIG_FILENAME} not found at {corpus_root}")
    with open(path) as f:
        data = yaml.safe_load(f)
    known_fields = {f.name for f in fields(DASConfig)}
    data = {k: v for k, v in data.items() if k in known_fields}
    return DASConfig(**data)


def write_config(corpus_root: Path, config: DASConfig) -> None:
    path = corpus_root / CONFIG_FILENAME
    data = {k: v for k, v in vars(config).items() if v is not None}
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
