from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import yaml

CONFIG_FILENAME = "jdx.config.yaml"
SPEC_VERSION = "1.0"
VALID_CONTEXT_TYPES = {"client", "project", "dept", "none"}


@dataclass
class JDXConfig:
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


def load_config(corpus_root: Path) -> JDXConfig:
    path = corpus_root / CONFIG_FILENAME
    if not path.exists():
        raise FileNotFoundError(f"{CONFIG_FILENAME} not found at {corpus_root}")
    with open(path) as f:
        data = yaml.safe_load(f)
    return JDXConfig(**data)


def write_config(corpus_root: Path, config: JDXConfig) -> None:
    path = corpus_root / CONFIG_FILENAME
    data = {k: v for k, v in vars(config).items() if v is not None}
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
