from __future__ import annotations
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Optional
import re
import yaml

CONFIG_FILENAME = "das.config.yaml"
SPEC_VERSION = "1.0"
TAG_CODE_RE = re.compile(r"^[A-Z]{2,5}$")


@dataclass
class DASConfig:
    version: str
    corpus: str
    initialized: str
    address_separator: str
    manifest: str
    org: Optional[str] = None
    tags: Optional[dict[str, str]] = None

    def __post_init__(self):
        if self.address_separator != ".":
            raise ValueError("address_separator must be '.'")
        if self.tags:
            for code, description in self.tags.items():
                if not TAG_CODE_RE.match(code):
                    raise ValueError(
                        f"tags code '{code}' must be 2-5 uppercase letters"
                    )
                if not isinstance(description, str) or not description.strip():
                    raise ValueError(
                        f"tags code '{code}' must have a non-empty description"
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
