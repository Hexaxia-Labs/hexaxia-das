import pytest
from das.config import load_config
from das.manifest import (
    ManifestNode, DASManifest, load_manifest, add_node,
    write_manifest, search_nodes, infer_parent, infer_type,
)


def test_infer_parent_root():
    assert infer_parent("00") is None


def test_infer_parent_category():
    assert infer_parent("00.01") == "00"


def test_infer_parent_deep():
    assert infer_parent("00.01.02") == "00.01"


def test_infer_type_area():
    assert infer_type("00") == "area"


def test_infer_type_category():
    assert infer_type("00.01") == "category"


def test_infer_type_subcategory():
    assert infer_type("00.01.01") == "subcategory"


def test_infer_type_context():
    assert infer_type("00.01.01.01") == "context"


def test_infer_type_deep_stays_context():
    assert infer_type("00.01.01.01.01") == "context"


def test_add_node(corpus):
    config = load_config(corpus)
    manifest = load_manifest(corpus / config.manifest)
    node = ManifestNode(label="Admin", description="Company governance", type="area")
    add_node(manifest, "00", node)
    assert "00" in manifest.nodes
    assert manifest.nodes["00"].label == "Admin"


def test_add_node_sets_updated_date(corpus):
    from datetime import date
    config = load_config(corpus)
    manifest = load_manifest(corpus / config.manifest)
    node = ManifestNode(label="Admin", description="Company governance", type="area")
    add_node(manifest, "00", node)
    assert manifest.updated == str(date.today())


def test_add_node_rejects_invalid_address(corpus):
    config = load_config(corpus)
    manifest = load_manifest(corpus / config.manifest)
    node = ManifestNode(label="Foo", description="bar", type="area")
    with pytest.raises(ValueError, match="[Aa]ddress format"):
        add_node(manifest, "abc", node)


def test_add_node_duplicate_raises(corpus):
    config = load_config(corpus)
    manifest = load_manifest(corpus / config.manifest)
    node = ManifestNode(label="Admin", description="Company governance", type="area")
    add_node(manifest, "00", node)
    with pytest.raises(ValueError, match="already exists"):
        add_node(manifest, "00", node)


def test_add_node_missing_parent_raises(corpus):
    config = load_config(corpus)
    manifest = load_manifest(corpus / config.manifest)
    node = ManifestNode(
        label="Finance", description="Financial records",
        type="category", parent="01"
    )
    with pytest.raises(ValueError, match="Parent address"):
        add_node(manifest, "01.01", node)


def test_write_manifest_roundtrip(corpus):
    config = load_config(corpus)
    manifest_path = corpus / config.manifest
    manifest = load_manifest(manifest_path)
    node = ManifestNode(label="Admin", description="Company governance", type="area")
    add_node(manifest, "00", node)
    write_manifest(manifest_path, manifest)
    reloaded = load_manifest(manifest_path)
    assert "00" in reloaded.nodes
    assert reloaded.nodes["00"].label == "Admin"


def test_deprecated_node_roundtrip(corpus):
    config = load_config(corpus)
    manifest_path = corpus / config.manifest
    manifest = load_manifest(manifest_path)
    node = ManifestNode(
        label="OldArea", description="Retired area",
        type="area", deprecated=True
    )
    add_node(manifest, "99", node)
    write_manifest(manifest_path, manifest)
    reloaded = load_manifest(manifest_path)
    assert reloaded.nodes["99"].deprecated is True


def test_search_by_label(corpus):
    config = load_config(corpus)
    manifest = load_manifest(corpus / config.manifest)
    add_node(manifest, "00", ManifestNode(label="Admin", description="Company governance", type="area"))
    add_node(manifest, "01", ManifestNode(label="Finance", description="Financial records", type="area"))
    results = search_nodes(manifest, "admin")
    assert len(results) == 1
    assert results[0][0] == "00"


def test_search_by_description(corpus):
    config = load_config(corpus)
    manifest = load_manifest(corpus / config.manifest)
    add_node(manifest, "00", ManifestNode(label="Admin", description="Company governance", type="area"))
    results = search_nodes(manifest, "governance")
    assert len(results) == 1


def test_search_no_results(corpus):
    config = load_config(corpus)
    manifest = load_manifest(corpus / config.manifest)
    results = search_nodes(manifest, "nonexistent")
    assert results == []


def test_valid_type_slugs_are_the_spec_5_4_vocabulary():
    from das.manifest import VALID_TYPE_SLUGS
    assert VALID_TYPE_SLUGS == {
        "runbook", "plan", "spec", "design", "strategy", "playbook",
        "proposal", "contract", "report", "catalog", "lead", "post",
        "template", "reference", "procedure",
    }
    assert len(VALID_TYPE_SLUGS) == 15
