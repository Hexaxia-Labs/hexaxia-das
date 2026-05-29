import pytest
from pathlib import Path
from das.config import load_config, write_config
from das.manifest import (
    ManifestNode, load_manifest, add_node, write_manifest,
    infer_parent, infer_type,
)
from das.validator import validate_corpus


def _set_tags(corpus, tags):
    # Rewrite the corpus config with an explicit tags vocabulary.
    config = load_config(corpus)
    config.tags = tags
    write_config(corpus, config)


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


def test_malformed_prefix_reports_invalid_format(corpus):
    # A name that HAS a numeric prefix but it is malformed (not two-digit
    # segments) should report an invalid format, not a missing prefix.
    (corpus / "123-Weird").mkdir()
    errors = validate_corpus(corpus)
    assert any("invalid address format" in e.message.lower() for e in errors)
    assert not any("No address prefix" in e.message for e in errors)


def test_truly_unprefixed_still_reports_no_prefix(corpus):
    # A name with no leading digit at all still reports a missing prefix.
    (corpus / "JustText").mkdir()
    errors = validate_corpus(corpus)
    assert any("No address prefix" in e.message for e in errors)


def test_root_suffix_skip_does_not_apply_in_subfolders(corpus):
    # The root-suffix skip only applies to files whose parent IS the corpus
    # root. A .txt with no address nested in a registered folder is invalid.
    _register(corpus, "00", "Admin", "Company governance")
    folder = corpus / "00-Admin"
    folder.mkdir()
    (folder / "notes.txt").touch()
    errors = validate_corpus(corpus)
    assert any("No address prefix" in e.message for e in errors)


def test_known_filename_tag_is_valid(corpus):
    # A file carrying a tag that is in the config vocabulary validates clean.
    _set_tags(corpus, {"ULS": "Unilever Solutions"})
    _register(corpus, "00", "Admin", "Company governance")
    _register(corpus, "00.01", "Sub", "Subcategory")
    _register(corpus, "00.01.04", "Leaf", "Leaf folder")
    folder = corpus / "00-Admin" / "00.01-Sub" / "00.01.04-Leaf"
    folder.mkdir(parents=True)
    (folder / "00.01.04-ULS-runbook-foo.md").touch()
    errors = validate_corpus(corpus)
    assert errors == []


def test_unknown_filename_tag_is_invalid(corpus):
    # A file carrying a tag NOT in the config vocabulary is an error.
    _set_tags(corpus, {"ULS": "Unilever Solutions"})
    _register(corpus, "00", "Admin", "Company governance")
    _register(corpus, "00.01", "Sub", "Subcategory")
    _register(corpus, "00.01.04", "Leaf", "Leaf folder")
    folder = corpus / "00-Admin" / "00.01-Sub" / "00.01.04-Leaf"
    folder.mkdir(parents=True)
    (folder / "00.01.04-XYZ-runbook-foo.md").touch()
    errors = validate_corpus(corpus)
    assert any("Unknown tag 'XYZ'" in e.message for e in errors)


def test_file_without_tag_is_not_tag_checked(corpus):
    # A file whose first post-address token is a lowercase type slug carries
    # no tag and must not raise a tag error, even with a vocabulary defined.
    _set_tags(corpus, {"ULS": "Unilever Solutions"})
    _register(corpus, "00", "Admin", "Company governance")
    _register(corpus, "00.01", "Sub", "Subcategory")
    _register(corpus, "00.01.04", "Leaf", "Leaf folder")
    folder = corpus / "00-Admin" / "00.01-Sub" / "00.01.04-Leaf"
    folder.mkdir(parents=True)
    (folder / "00.01.04-runbook-foo.md").touch()
    errors = validate_corpus(corpus)
    assert not any("Unknown tag" in e.message for e in errors)


def test_tag_enforcement_off_when_no_vocabulary(corpus):
    # The default fixture config has no tags vocabulary. A tagged file must
    # NOT be flagged - there is nothing to be unknown against.
    _register(corpus, "00", "Admin", "Company governance")
    _register(corpus, "00.01", "Sub", "Subcategory")
    _register(corpus, "00.01.04", "Leaf", "Leaf folder")
    folder = corpus / "00-Admin" / "00.01-Sub" / "00.01.04-Leaf"
    folder.mkdir(parents=True)
    (folder / "00.01.04-ULS-runbook-foo.md").touch()
    errors = validate_corpus(corpus)
    assert errors == []


def test_type_slug_is_not_mistaken_for_tag(corpus):
    # 'contract' is a lowercase type slug, not a tag, so no tag check applies.
    _set_tags(corpus, {"ULS": "Unilever Solutions"})
    _register(corpus, "00", "Admin", "Company governance")
    folder = corpus / "00-Admin"
    folder.mkdir()
    (folder / "00-contract-msa.pdf").touch()
    errors = validate_corpus(corpus)
    assert not any("Unknown tag" in e.message for e in errors)


def test_folder_with_uppercase_label_is_not_tag_checked(corpus):
    # Folders carry no tag. An uppercase-looking label component must never
    # trigger a tag error even when a vocabulary is defined.
    _set_tags(corpus, {"ULS": "Unilever Solutions"})
    _register(corpus, "00", "ABC", "Folder whose label looks like a tag")
    (corpus / "00-ABC").mkdir()
    errors = validate_corpus(corpus)
    assert not any("Unknown tag" in e.message for e in errors)


def test_default_mode_does_not_enforce_type(corpus):
    _register(corpus, "00", "Admin", "gov")
    (corpus / "00-Admin").mkdir()
    (corpus / "00-Admin" / "00-frobnicate-foo.md").touch()
    errors = validate_corpus(corpus)  # default strict=False
    assert not any("type slug" in e.message for e in errors)


def test_strict_valid_type_slug_passes(corpus):
    _register(corpus, "00", "Admin", "gov")
    (corpus / "00-Admin").mkdir()
    (corpus / "00-Admin" / "00-reference-company-profile.md").touch()
    errors = validate_corpus(corpus, strict=True)
    assert not any("type slug" in e.message for e in errors)


def test_strict_invalid_type_slug_errors(corpus):
    _register(corpus, "00", "Admin", "gov")
    (corpus / "00-Admin").mkdir()
    (corpus / "00-Admin" / "00-frobnicate-foo.md").touch()
    errors = validate_corpus(corpus, strict=True)
    assert any("type slug 'frobnicate'" in e.message for e in errors)


def test_strict_missing_type_errors(corpus):
    _register(corpus, "00", "Admin", "gov")
    (corpus / "00-Admin").mkdir()
    (corpus / "00-Admin" / "00-orphan.md").touch()  # 'orphan' is not a type
    errors = validate_corpus(corpus, strict=True)
    assert any("type slug" in e.message for e in errors)


def test_strict_tag_then_type_passes(corpus):
    _set_tags(corpus, {"ULS": "United Life Services"})
    _register(corpus, "00", "Admin", "gov")
    (corpus / "00-Admin").mkdir()
    (corpus / "00-Admin" / "00-ULS-runbook-foo.md").touch()
    errors = validate_corpus(corpus, strict=True)
    assert not any("type slug" in e.message for e in errors)


def test_strict_folder_is_not_type_checked(corpus):
    _register(corpus, "00", "Admin", "gov")
    (corpus / "00-Admin").mkdir()  # a folder, no type slug
    errors = validate_corpus(corpus, strict=True)
    assert not any("type slug" in e.message for e in errors)
