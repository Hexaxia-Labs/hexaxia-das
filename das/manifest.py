from __future__ import annotations
from dataclasses import dataclass, field, fields
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
import yaml

MANIFEST_FILENAME = "das.manifest.yaml"
LEVEL_TYPES = ["area", "category", "subcategory", "context"]
VALID_TYPES = set(LEVEL_TYPES) | {"file"}

ADDRESS_RE = re.compile(r"^\d{2}(\.\d{2})*$")
FILE_ADDRESS_RE = re.compile(r"^(\d{2}(\.\d{2})*)-")
FOLDER_NAME_RE = re.compile(r"^\d{2}(\.\d{2})*-[A-Z][a-zA-Z0-9-]*$")


@dataclass
class ManifestNode:
    label: str
    description: str
    type: str
    parent: Optional[str] = None
    agent_hint: Optional[str] = None
    deprecated: bool = False


@dataclass
class DASManifest:
    version: str
    corpus: str
    updated: str
    nodes: Dict[str, ManifestNode] = field(default_factory=dict)


def infer_parent(address: str) -> Optional[str]:
    parts = address.rsplit(".", 1)
    return parts[0] if len(parts) > 1 else None


def infer_type(address: str) -> str:
    depth = address.count(".")
    return LEVEL_TYPES[depth] if depth < len(LEVEL_TYPES) else "context"


def load_manifest(path: Path) -> DASManifest:
    with open(path) as f:
        data = yaml.safe_load(f)
    known_node_fields = {f.name for f in fields(ManifestNode)}
    nodes = {
        addr: ManifestNode(**{k: v for k, v in node_data.items() if k in known_node_fields})
        for addr, node_data in (data.get("nodes") or {}).items()
    }
    return DASManifest(
        version=data["version"],
        corpus=data["corpus"],
        updated=data["updated"],
        nodes=nodes,
    )


def add_node(manifest: DASManifest, address: str, node: ManifestNode) -> None:
    if not ADDRESS_RE.match(address):
        raise ValueError(
            f"Invalid address format: '{address}' "
            "(expected two-digit segments separated by dots, e.g. '00.01')"
        )
    if address in manifest.nodes:
        raise ValueError(f"Address '{address}' already exists in manifest")
    parent = infer_parent(address)
    if parent and parent not in manifest.nodes:
        raise ValueError(
            f"Parent address '{parent}' not in manifest - add it first"
        )
    manifest.nodes[address] = node
    manifest.updated = str(date.today())


def search_nodes(
    manifest: DASManifest, query: str
) -> List[Tuple[str, ManifestNode]]:
    q = query.lower()
    return [
        (addr, node)
        for addr, node in manifest.nodes.items()
        if q in node.label.lower() or q in node.description.lower()
    ]


def write_manifest(path: Path, manifest: DASManifest) -> None:
    nodes_data: Dict = {}
    for addr, node in sorted(manifest.nodes.items()):
        entry: Dict = {
            "label": node.label,
            "description": node.description,
            "type": node.type,
        }
        if node.parent:
            entry["parent"] = node.parent
        if node.agent_hint:
            entry["agent_hint"] = node.agent_hint
        if node.deprecated:
            entry["deprecated"] = True
        nodes_data[addr] = entry
    data = {
        "version": manifest.version,
        "corpus": manifest.corpus,
        "updated": manifest.updated,
        "nodes": nodes_data,
    }
    with open(path, "w") as f:
        yaml.dump(
            data, f, default_flow_style=False,
            sort_keys=False, allow_unicode=True
        )
