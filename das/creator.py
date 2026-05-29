from __future__ import annotations
from datetime import date as date_type
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
