import pytest
from pathlib import Path
from das.config import load_config
from das.manifest import (
    ManifestNode, load_manifest, add_node, write_manifest,
    infer_parent, infer_type,
)
from das.validator import validate_corpus


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
    assert any("No address prefix" in e.message for e in errors)


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


def test_underscore_prefixed_paths_are_skipped(corpus):
    # Underscore-prefixed file at root, plus an underscore-prefixed folder
    # containing a file that would otherwise be invalid. Both must be skipped.
    (corpus / "_draft-notes.md").touch()
    private = corpus / "_private"
    private.mkdir()
    (private / "no-address-here.txt").touch()
    errors = validate_corpus(corpus)
    assert errors == []


def test_zone_identifier_files_are_skipped(corpus):
    # A Windows ADS sidecar inside an otherwise-valid registered folder.
    # The :Zone.Identifier skip must fire even though the name has no address.
    _register(corpus, "00", "Admin", "Company governance")
    folder = corpus / "00-Admin"
    folder.mkdir()
    (folder / "00-TST-some-doc.md:Zone.Identifier").touch()
    errors = validate_corpus(corpus)
    assert errors == []


def test_root_repo_files_are_skipped(corpus):
    # Root-level files with repo suffixes (.sh, .md, .txt) are skipped,
    # even though they carry no address prefix.
    (corpus / "setup.sh").touch()
    (corpus / "notes.md").touch()
    (corpus / "todo.txt").touch()
    errors = validate_corpus(corpus)
    assert errors == []


def test_named_root_skips_are_skipped(corpus):
    # The explicitly named root skips. These carry repo suffixes already,
    # so they exercise the ROOT_SKIP_NAMES / suffix skip at root level.
    (corpus / "GOOGLE-DRIVE-SYNC.md").touch()
    (corpus / "drive-sync.sh").touch()
    errors = validate_corpus(corpus)
    assert errors == []


def test_root_address_file_must_be_in_manifest(corpus):
    # A root-level address-bearing file with no address-bearing parent folder
    # must have its address registered in the manifest, else it is an error.
    (corpus / "00-orphan.md").touch()
    errors = validate_corpus(corpus)
    assert any("not in manifest" in e.message for e in errors)


def test_root_address_file_registered_is_valid(corpus):
    # Once the address is registered, the same root-level file validates clean.
    _register(corpus, "00", "Admin", "Company governance")
    (corpus / "00-orphan.md").touch()
    assert validate_corpus(corpus) == []


def test_root_suffix_skip_does_not_apply_in_subfolders(corpus):
    # The root-suffix skip only applies to files whose parent IS the corpus
    # root. A .txt with no address nested in a registered folder is invalid.
    _register(corpus, "00", "Admin", "Company governance")
    folder = corpus / "00-Admin"
    folder.mkdir()
    (folder / "notes.txt").touch()
    errors = validate_corpus(corpus)
    assert any("No address prefix" in e.message for e in errors)
