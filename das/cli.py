from __future__ import annotations
from datetime import date
from pathlib import Path
from typing import List, Optional
import typer

from das.config import (
    DASConfig, NamingConvention, load_config, write_config,
    SCHEMA_VERSION, CONFIG_FILENAME,
    DEFAULT_PATTERN_DRAFT, DEFAULT_PATTERN_PUBLISHED, VALID_NAMING_STYLES,
)
from das.manifest import (
    DASManifest, ManifestNode, load_manifest, add_node,
    write_manifest, search_nodes, infer_parent, infer_type,
    MANIFEST_FILENAME,
)
from das.validator import validate_corpus
from das.creator import create_document
from das import __version__

app = typer.Typer(help="Hexaxia DAS: Document Addressing Standard corpus tool")

# Sensible default templates per naming style, written into the 'naming' block
# at init. das-address composes the address jump-table with a slug and an
# optional publish date; slug-date is the legacy slug-first marketing form.
# 'custom' is seeded with the composed pattern as a starting point to edit.
_NAMING_DEFAULTS = {
    "das-address": (DEFAULT_PATTERN_DRAFT, DEFAULT_PATTERN_PUBLISHED),
    "slug-date": ("{slug}.{ext}", "{slug}-{YYMMDD}.{ext}"),
    "custom": ("{address}-{type}-{slug}.{ext}", "{address}-{type}-{slug}-{YYMMDD}.{ext}"),
}


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", callback=_version_callback, is_eager=True,
        help="Show the das version and exit.",
    ),
) -> None:
    """Hexaxia DAS: Document Addressing Standard corpus tool."""


@app.command()
def init(
    corpus: str = typer.Argument(..., help="Corpus slug (e.g. atlas-technologies)"),
    org: Optional[str] = typer.Option(None, help="Org code (e.g. ATL)"),
    tag: List[str] = typer.Option(
        [],
        "--tag",
        help="Tag vocabulary entry as CODE=description (repeatable)",
    ),
    naming_style: str = typer.Option(
        "das-address",
        "--naming-style",
        help="Filename convention: das-address (default) | slug-date | custom",
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

    if naming_style not in VALID_NAMING_STYLES:
        valid = ", ".join(sorted(VALID_NAMING_STYLES))
        typer.echo(
            f"Error: invalid --naming-style '{naming_style}'. "
            f"Choose one of: {valid}.",
            err=True,
        )
        raise typer.Exit(1)
    draft, published = _NAMING_DEFAULTS[naming_style]
    naming = NamingConvention(
        style=naming_style,
        pattern_draft=draft,
        pattern_published=published,
    )

    try:
        config = DASConfig(
            version=SCHEMA_VERSION,
            corpus=corpus,
            initialized=str(date.today()),
            address_separator=".",
            manifest=MANIFEST_FILENAME,
            org=org,
            tags=tags,
            naming=naming,
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
def new(
    address: str = typer.Argument(..., help="DAS address (e.g. 02.01.04)"),
    type: str = typer.Argument(..., help="Type slug (see spec 5.4)"),
    descriptor: str = typer.Argument(..., help="Lowercase-hyphenated descriptor"),
    tag: Optional[str] = typer.Option(
        None, help="Tag code (must be in the config tags vocabulary)"
    ),
    ext: str = typer.Option("md", help="File extension (default md)"),
    published: bool = typer.Option(
        False,
        "--published",
        help="Use the corpus pattern_published template (adds the publish date).",
    ),
    date_str: Optional[str] = typer.Option(
        None,
        "--date",
        help="Publish date as YYMMDD for --published files (defaults to today).",
    ),
    path: Path = typer.Option(Path("."), help="Corpus root directory"),
):
    """Create a new spec-conformant document file at an address."""
    try:
        created = create_document(
            path, address, type, descriptor,
            tag=tag, ext=ext, published=published, date_str=date_str,
        )
    except FileNotFoundError:
        typer.echo(
            f"Error: no DAS corpus found at {path}. Run 'das init' first.", err=True
        )
        raise typer.Exit(1)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    rel = created.relative_to(path)
    if created.suffix == ".md":
        typer.echo(
            f"Created {rel}. Write the passport summary - it is the entire RAG signal."
        )
    else:
        typer.echo(
            f"Created {rel}. Note: {created.suffix.lstrip('.')} files cannot embed a "
            "passport block - record its passport separately.",
            err=True,
        )


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
