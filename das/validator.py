from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from das.config import load_config, resolve_naming, CONFIG_FILENAME, TAG_CODE_RE
from das.manifest import (
    load_manifest, MANIFEST_FILENAME,
    ADDRESS_RE, FILE_ADDRESS_RE, FOLDER_NAME_RE, LOOSE_PREFIX_RE,
    VALID_TYPE_SLUGS, DESCRIPTOR_RE, STRICT_LABEL_WORD_RE,
)
from das.naming import compile_pattern

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
    # address: a 2-5 char code starting with an uppercase letter, then
    # uppercase letters and/or digits (ACME, NW7, M365). A lowercase first
    # token is the {type} slug; an all-digit token is part of the address - in
    # either case the file carries no tag.
    remainder = name[len(address) + 1:]  # drop the address and its trailing '-'
    first = remainder.split("-", 1)[0]
    if first and TAG_CODE_RE.match(first):
        return first
    return None


def _extract_type(name: str, address: str) -> Optional[str]:
    # Per spec 5.2: {address}-[{TAG}-]{type}-{descriptor}.ext. The {type} is the
    # first '-'-delimited token after the address, or the second when a TAG (a
    # 2-5 char uppercase-alphanumeric first token) is present. Returns the candidate with any file
    # extension stripped, or None if there is no candidate.
    remainder = name[len(address) + 1:]  # drop the address and its trailing '-'
    tokens = remainder.split("-")
    if not tokens or not tokens[0]:
        return None
    idx = 1 if TAG_CODE_RE.match(tokens[0]) else 0
    if idx >= len(tokens):
        return None
    candidate = tokens[idx]
    if "." in candidate:  # strip a trailing file extension on the type token
        candidate = candidate.rsplit(".", 1)[0]
    return candidate or None


def _extract_descriptor(name: str, address: str) -> Optional[str]:
    # Per spec 5.2: {address}-[{TAG}-]{type}-{descriptor}.ext. The descriptor is
    # everything after the {type} token, joined by '-'. Returns None if there is
    # no token after the type position (i.e. the descriptor is missing).
    remainder = name[len(address) + 1:]  # drop the address and its trailing '-'
    tokens = remainder.split("-")
    if not tokens or not tokens[0]:
        return None
    if "." in tokens[-1]:  # strip a trailing file extension from the last token
        tokens[-1] = tokens[-1].rsplit(".", 1)[0]
    idx = 1 if TAG_CODE_RE.match(tokens[0]) else 0  # skip an uppercase tag token
    descriptor_tokens = tokens[idx + 1:]  # everything after the type token
    if not descriptor_tokens:
        return None
    return "-".join(descriptor_tokens)


def _label_words(folder_name: str, address: str) -> List[str]:
    # The label is the part of the folder name after '{address}-'; return its
    # hyphen-separated words.
    return folder_name[len(address) + 1:].split("-")


def validate_corpus(corpus_root: Path, strict: bool = False) -> List[ValidationError]:
    config = load_config(corpus_root)
    manifest = load_manifest(corpus_root / config.manifest)
    errors: List[ValidationError] = []

    # Resolve the corpus's declared naming convention. The default address-first
    # style ('das-address', and whenever no 'naming' block is present) applies
    # the historic rules below unchanged. A non-address style ('slug-date' /
    # 'custom') validates FILE names against the declared pattern(s) instead;
    # folders stay address-based regardless (the address jump-table is a corpus
    # structure property, not a file-naming one). See docs/corpus-conventions.md.
    naming = resolve_naming(config)
    file_patterns = None
    if naming.style != "das-address":
        templates = [naming.pattern_draft]
        if naming.pattern_published:
            templates.append(naming.pattern_published)
        file_patterns = [compile_pattern(t) for t in templates if t]

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

        # Non-address naming style: validate FILE names against the declared
        # pattern(s) rather than the address-first rules. Folders fall through to
        # the address rules below (they are not affected by file conventions).
        if file_patterns is not None and item.is_file():
            if any(rx.match(item.name) for rx in file_patterns):
                continue
            errors.append(ValidationError(
                str(rel),
                f"File name does not match the declared "
                f"'{naming.style}' naming convention",
            ))
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
            if strict:
                for word in _label_words(item.name, address):
                    if not STRICT_LABEL_WORD_RE.match(word):
                        errors.append(ValidationError(
                            str(rel),
                            f"Folder label word '{word}' is not Title-Cased "
                            "(must start with an uppercase letter or digit)",
                        ))
                        break  # one finding per folder is enough

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

            # Strict mode enforces the required {type} slug (spec 5.2 / 5.4).
            # Off by default so legacy corpora are not newly-failed.
            if strict:
                type_slug = _extract_type(item.name, address)
                if type_slug not in VALID_TYPE_SLUGS:
                    shown = type_slug if type_slug is not None else ""
                    errors.append(ValidationError(
                        str(rel),
                        f"Invalid or missing type slug '{shown}' "
                        "(not in the spec 5.4 vocabulary)",
                    ))

                descriptor = _extract_descriptor(item.name, address)
                if descriptor is None:
                    errors.append(
                        ValidationError(str(rel), "Missing descriptor (spec 5.2)")
                    )
                elif not DESCRIPTOR_RE.match(descriptor):
                    errors.append(ValidationError(
                        str(rel),
                        f"Invalid descriptor '{descriptor}' "
                        "(lowercase words separated by single hyphens)",
                    ))

    return errors
