from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from das.config import load_config, CONFIG_FILENAME, TAG_CODE_RE
from das.manifest import (
    load_manifest, MANIFEST_FILENAME,
    ADDRESS_RE, FILE_ADDRESS_RE, FOLDER_NAME_RE, LOOSE_PREFIX_RE,
)

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


def _extract_tag(name: str, address: str) -> Optional[str]:
    # Per spec 5.2 the filename is {address}-[{TAG}-]{type}-{descriptor}.ext.
    # The TAG, when present, is the first '-'-delimited token after the
    # address and is 2-5 uppercase letters. A lowercase first token is the
    # {type} slug, which means the file carries no tag.
    remainder = name[len(address) + 1:]  # drop the address and its trailing '-'
    first = remainder.split("-", 1)[0]
    if first and TAG_CODE_RE.match(first):
        return first
    return None


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

        # Skip root-level non-corpus files (shell scripts, repo docs, etc.).
        # Address-bearing files are corpus files and are not skipped here - they
        # are cross-checked against the manifest in the file branch below.
        if item.parent == corpus_root and item.is_file():
            if _extract_address(item.name) is None and (
                item.name in ROOT_SKIP_NAMES or item.suffix in ROOT_SKIP_SUFFIXES
            ):
                continue

        address = _extract_address(item.name)

        if address is None:
            if LOOSE_PREFIX_RE.match(item.name):
                errors.append(ValidationError(
                    str(rel),
                    "Invalid address format (malformed numeric prefix)",
                ))
            else:
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
            if parent_address:
                if address != parent_address:
                    errors.append(ValidationError(
                        str(rel),
                        f"File address '{address}' does not match "
                        f"parent folder address '{parent_address}'",
                    ))
            else:
                if address not in manifest.nodes:
                    errors.append(
                        ValidationError(str(rel), f"Address '{address}' not in manifest")
                    )

            # Tag-vocabulary enforcement applies only when the corpus config
            # defines a tags vocabulary. Without one there is nothing to be
            # "unknown" against, so existing corpora are not flagged.
            if config.tags:
                tag = _extract_tag(item.name, address)
                if tag and tag not in config.tags:
                    errors.append(ValidationError(
                        str(rel),
                        f"Unknown tag '{tag}' not in config vocabulary",
                    ))

    return errors
