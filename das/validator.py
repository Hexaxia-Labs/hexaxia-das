from __future__ import annotations
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from das.config import load_config, CONFIG_FILENAME
from das.manifest import load_manifest, MANIFEST_FILENAME

ADDRESS_RE = re.compile(r"^\d{2}(\.\d{2})*$")
FILE_ADDRESS_RE = re.compile(r"^(\d{2}(\.\d{2})*)-")
FOLDER_NAME_RE = re.compile(r"^\d{2}(\.\d{2})*-[A-Z][a-zA-Z0-9-]*$")

SKIP_NAMES = {
    CONFIG_FILENAME,
    MANIFEST_FILENAME,
    "das.migration.md",
    "README.md",
    "AGENT_CONTEXT.md",
    "CLAUDE.md",
    ".git",
}

# Root-level files that belong to the repo, not the DAS corpus
ROOT_SKIP_SUFFIXES = {".sh", ".md", ".txt"}
ROOT_SKIP_NAMES = {"GOOGLE-DRIVE-SYNC.md", "drive-sync.sh"}


@dataclass
class ValidationError:
    path: str
    message: str


def _extract_address(name: str) -> Optional[str]:
    m = FILE_ADDRESS_RE.match(name)
    return m.group(1) if m else None


def validate_corpus(corpus_root: Path) -> List[ValidationError]:
    config = load_config(corpus_root)
    manifest = load_manifest(corpus_root / config.manifest)
    errors: List[ValidationError] = []

    for item in sorted(corpus_root.rglob("*")):
        rel = item.relative_to(corpus_root)

        # Skip hidden paths and known special filenames anywhere in tree
        if any(
            part.startswith(".") or part in SKIP_NAMES
            for part in rel.parts
        ):
            continue

        # Skip underscore-prefixed items (drafts, logs, private folders)
        if any(part.startswith("_") for part in rel.parts):
            continue

        # Skip Windows Zone.Identifier ADS files
        if ":Zone.Identifier" in item.name:
            continue

        # Skip root-level non-corpus files (shell scripts, repo docs, etc.)
        if item.parent == corpus_root and item.is_file():
            if item.name in ROOT_SKIP_NAMES or item.suffix in ROOT_SKIP_SUFFIXES:
                continue

        address = _extract_address(item.name)

        if address is None:
            errors.append(ValidationError(str(rel), "No address prefix found"))
            continue

        if not ADDRESS_RE.match(address):
            errors.append(
                ValidationError(str(rel), f"Invalid address format: '{address}'")
            )
            continue

        if item.is_dir():
            if not FOLDER_NAME_RE.match(item.name):
                errors.append(ValidationError(
                    str(rel),
                    "Folder label must be Title-Cased and hyphenated (e.g. '00-Admin')",
                ))
            if address not in manifest.nodes:
                errors.append(
                    ValidationError(str(rel), f"Address '{address}' not in manifest")
                )

        if item.is_file():
            parent_address = _extract_address(item.parent.name)
            if parent_address and address != parent_address:
                errors.append(ValidationError(
                    str(rel),
                    f"File address '{address}' does not match "
                    f"parent folder address '{parent_address}'",
                ))

    return errors
