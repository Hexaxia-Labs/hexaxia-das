import pytest
from pathlib import Path
from jdx.config import load_config
from jdx.manifest import (
    ManifestNode, load_manifest, add_node, write_manifest,
    infer_parent, infer_type,
)
from jdx.validator import validate_corpus


def _register(corpus, address, label, description):
    config = load_config(corpus)
    manifest_path = corpus / config.manifest
    manifest = load_manifest(manifest_path)
    node = ManifestNode(
        label=label,
        description=description,
        type=infer_type(address),
        parent=infer_parent(address),
    )
    add_node(manifest, address, node)
    write_manifest(manifest_path, manifest)


def test_empty_corpus_is_valid(corpus):
    errors = validate_corpus(corpus)
    assert errors == []


def test_registered_folder_is_valid(corpus):
    _register(corpus, "00", "Admin", "Company governance")
    (corpus / "00-Admin").mkdir()
    errors = validate_corpus(corpus)
    assert errors == []


def test_file_with_parent_address_is_valid(corpus):
    _register(corpus, "00", "Admin", "Company governance")
    folder = corpus / "00-Admin"
    folder.mkdir()
    (folder / "00-TST-some-doc.md").touch()
    errors = validate_corpus(corpus)
    assert errors == []


def test_folder_without_address_is_invalid(corpus):
    (corpus / "Admin").mkdir()
    errors = validate_corpus(corpus)
    assert any("No JDX address prefix" in e.message for e in errors)


def test_folder_not_in_manifest_is_invalid(corpus):
    (corpus / "00-Admin").mkdir()
    errors = validate_corpus(corpus)
    assert any("not in manifest" in e.message for e in errors)


def test_file_address_mismatch_is_invalid(corpus):
    _register(corpus, "00", "Admin", "Company governance")
    folder = corpus / "00-Admin"
    folder.mkdir()
    (folder / "01-TST-wrong-address.md").touch()
    errors = validate_corpus(corpus)
    assert any("does not match parent folder" in e.message for e in errors)


def test_deep_hierarchy_is_valid(corpus):
    _register(corpus, "00", "Admin", "Company governance")
    _register(corpus, "00.01", "Business-Registration", "Registration docs")
    _register(corpus, "00.01.01", "State-Filings", "State filing docs")
    deep = corpus / "00-Admin" / "00.01-Business-Registration" / "00.01.01-State-Filings"
    deep.mkdir(parents=True)
    (deep / "00.01.01-TST-articles-260527.md").touch()
    errors = validate_corpus(corpus)
    assert errors == []


def test_config_and_manifest_files_are_skipped(corpus):
    errors = validate_corpus(corpus)
    assert errors == []


def test_hidden_files_are_skipped(corpus):
    (corpus / ".DS_Store").touch()
    errors = validate_corpus(corpus)
    assert errors == []
