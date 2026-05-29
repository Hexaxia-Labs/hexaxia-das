from __future__ import annotations
from datetime import date
from pathlib import Path
from typing import List, Optional
import typer

from das.config import (
    DASConfig, load_config, write_config,
    SCHEMA_VERSION, CONFIG_FILENAME,
)
from das.manifest import (
    DASManifest, ManifestNode, load_manifest, add_node,
    write_manifest, search_nodes, infer_parent, infer_type,
    MANIFEST_FILENAME,
)
from das.validator import validate_corpus

app = typer.Typer(help="Hexaxia DAS: Document Addressing Standard corpus tool")


@app.command()
def init(
    corpus: str = typer.Argument(..., help="Corpus slug (e.g. hexaxia-technologies)"),
    org: Optional[str] = typer.Option(None, help="Org code (e.g. HXT)"),
    tag: List[str] = typer.Option(
        [],
        "--tag",
        help="Tag vocabulary entry as CODE=description (repeatable)",
    ),
    path: Path = typer.Option(Path("."), help="Corpus root directory"),
):
    """Initialize a new DAS corpus."""
    config_path = path / CONFIG_FILENAME
    if config_path.exists():
        typer.echo(
            f"Error: {CONFIG_FILENAME} already exists. "
            "Corpus already initialized.",
            err=True,
        )
        raise typer.Exit(1)

    tags: Optional[dict[str, str]] = None
    if tag:
        tags = {}
        for entry in tag:
            if "=" not in entry:
                typer.echo(
                    f"Error: invalid --tag '{entry}'. Expected CODE=description.",
                    err=True,
                )
                raise typer.Exit(1)
            code, description = entry.split("=", 1)
            tags[code.strip()] = description.strip()

    try:
        config = DASConfig(
            version=SCHEMA_VERSION,
            corpus=corpus,
            initialized=str(date.today()),
            address_separator=".",
            manifest=MANIFEST_FILENAME,
            org=org,
            tags=tags,
        )
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    manifest = DASManifest(
        version=SCHEMA_VERSION,
        corpus=corpus,
        updated=str(date.today()),
    )
    write_config(path, config)
    write_manifest(path / MANIFEST_FILENAME, manifest)
    typer.echo(f"Initialized DAS corpus '{corpus}' at {path}")
    typer.echo(f"  {CONFIG_FILENAME}")
    typer.echo(f"  {MANIFEST_FILENAME}")


@app.command()
def add(
    address: str = typer.Argument(..., help="DAS address (e.g. 00.01)"),
    label: str = typer.Argument(..., help="Folder label (e.g. Business-Registration)"),
    description: str = typer.Argument(..., help="One-sentence description"),
    agent_hint: Optional[str] = typer.Option(None, help="Agent routing hint"),
    path: Path = typer.Option(Path("."), help="Corpus root directory"),
):
    """Add a node to the manifest."""
    try:
        config = load_config(path)
    except FileNotFoundError:
        typer.echo(f"Error: no DAS corpus found at {path}. Run 'das init' first.", err=True)
        raise typer.Exit(1)
    manifest_path = path / config.manifest
    try:
        manifest = load_manifest(manifest_path)
    except FileNotFoundError:
        typer.echo(f"Error: manifest file not found. Corpus may be corrupted.", err=True)
        raise typer.Exit(1)
    node = ManifestNode(
        label=label,
        description=description,
        type=infer_type(address),
        parent=infer_parent(address),
        agent_hint=agent_hint,
    )
    try:
        add_node(manifest, address, node)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    write_manifest(manifest_path, manifest)
    typer.echo(f"Added [{address}] {label}")


@app.command()
def ls(
    address: Optional[str] = typer.Argument(
        None, help="Show node and its children (omit for all)"
    ),
    path: Path = typer.Option(Path("."), help="Corpus root directory"),
):
    """List manifest nodes."""
    try:
        config = load_config(path)
    except FileNotFoundError:
        typer.echo(f"Error: no DAS corpus found at {path}. Run 'das init' first.", err=True)
        raise typer.Exit(1)
    try:
        manifest = load_manifest(path / config.manifest)
    except FileNotFoundError:
        typer.echo(f"Error: manifest file not found. Corpus may be corrupted.", err=True)
        raise typer.Exit(1)
    items = list(manifest.nodes.items())
    if address:
        items = [
            (a, n)
            for a, n in items
            if a == address or n.parent == address
        ]
    for addr, node in sorted(items):
        deprecated = " [deprecated]" if node.deprecated else ""
        typer.echo(
            f"  {addr:<20} {node.label:<30} {node.description}{deprecated}"
        )


@app.command()
def find(
    query: str = typer.Argument(..., help="Search term (label or description)"),
    path: Path = typer.Option(Path("."), help="Corpus root directory"),
):
    """Search manifest by label or description."""
    try:
        config = load_config(path)
    except FileNotFoundError:
        typer.echo(f"Error: no DAS corpus found at {path}. Run 'das init' first.", err=True)
        raise typer.Exit(1)
    try:
        manifest = load_manifest(path / config.manifest)
    except FileNotFoundError:
        typer.echo(f"Error: manifest file not found. Corpus may be corrupted.", err=True)
        raise typer.Exit(1)
    results = search_nodes(manifest, query)
    if not results:
        typer.echo(f"No results for '{query}'")
        return
    for addr, node in results:
        typer.echo(f"  {addr:<20} {node.label:<30} {node.description}")


@app.command()
def validate(
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Enforce the full v0.3 filename format, including the {type} slug",
    ),
    path: Path = typer.Option(Path("."), help="Corpus root directory"),
):
    """Validate corpus naming convention compliance."""
    try:
        errors = validate_corpus(path, strict=strict)
    except FileNotFoundError:
        typer.echo(f"Error: no DAS corpus found at {path}. Run 'das init' first.", err=True)
        raise typer.Exit(1)
    if not errors:
        typer.echo("Corpus is valid.")
        return
    typer.echo(f"{len(errors)} validation error(s):", err=True)
    for e in errors:
        typer.echo(f"  {e.path}: {e.message}", err=True)
    raise typer.Exit(1)
