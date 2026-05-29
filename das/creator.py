from __future__ import annotations
from datetime import date, date as date_type
from pathlib import Path
from typing import Optional
import re

from das.config import load_config
from das.manifest import ADDRESS_RE, FILE_ADDRESS_RE, VALID_TYPE_SLUGS

DESCRIPTOR_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def _titleize(descriptor: str) -> str:
    return " ".join(word.capitalize() for word in descriptor.split("-"))


def _passport_stub(
    address: str,
    type_slug: str,
    descriptor: str,
    tag: Optional[str],
    created: date_type,
) -> str:
    title = _titleize(descriptor)
    lines = [
        "<!--",
        "passport:",
        f'  title: "{title}"',
        f"  type: {type_slug}",
        "  status: draft",
    ]
    if tag:
        lines.append(f"  tags: [{tag}]")
    lines += [
        f'  das_address: "{address}"',
        f'  created: "{created.isoformat()}"',
        '  summary: ""',
        "-->",
        "",
        f"# {title}",
        "",
    ]
    return "\n".join(lines)


def _resolve_folder(corpus_root: Path, address: str) -> Path:
    matches = [
        d
        for d in corpus_root.rglob(f"{address}-*")
        if d.is_dir()
        and (_m := FILE_ADDRESS_RE.match(d.name)) is not None
        and _m.group(1) == address
    ]
    if not matches:
        raise ValueError(f"no folder found for address '{address}'")
    if len(matches) > 1:
        rels = ", ".join(sorted(str(d.relative_to(corpus_root)) for d in matches))
        raise ValueError(f"ambiguous: multiple folders for address '{address}': {rels}")
    return matches[0]


def create_document(
    corpus_root: Path,
    address: str,
    type_slug: str,
    descriptor: str,
    tag: Optional[str] = None,
    ext: str = "md",
) -> Path:
    if not ADDRESS_RE.match(address):
        raise ValueError(
            f"Invalid address format: '{address}' "
            "(expected two-digit segments separated by dots, e.g. '00.01')"
        )
    if type_slug not in VALID_TYPE_SLUGS:
        valid = ", ".join(sorted(VALID_TYPE_SLUGS))
        raise ValueError(f"Invalid type '{type_slug}'. Valid types: {valid}")
    if not DESCRIPTOR_RE.match(descriptor):
        raise ValueError(
            f"Invalid descriptor '{descriptor}' (use lowercase words separated by "
            "single hyphens, e.g. 'netbird-ztna')"
        )
    if tag is not None:
        config = load_config(corpus_root)
        if not config.tags:
            raise ValueError("no tags vocabulary defined in das.config.yaml")
        if tag not in config.tags:
            raise ValueError(f"unknown tag '{tag}' not in config vocabulary")

    ext = ext.lstrip(".").lower()
    folder = _resolve_folder(corpus_root, address)
    tag_part = f"{tag}-" if tag else ""
    filename = f"{address}-{tag_part}{type_slug}-{descriptor}.{ext}"
    target = folder / filename
    if target.exists():
        raise ValueError(f"file already exists: {target.relative_to(corpus_root)}")

    if ext == "md":
        target.write_text(
            _passport_stub(address, type_slug, descriptor, tag, date.today())
        )
    else:
        target.touch()
    return target
