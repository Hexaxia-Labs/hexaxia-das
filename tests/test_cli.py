import pytest
from typer.testing import CliRunner
from das.cli import app

runner = CliRunner()


def test_init_creates_config_and_manifest(tmp_path):
    result = runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "das.config.yaml").exists()
    assert (tmp_path / "das.manifest.yaml").exists()


def test_init_output_names_files(tmp_path):
    result = runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    assert "das.config.yaml" in result.output
    assert "das.manifest.yaml" in result.output


def test_init_rejects_removed_context_type_option(tmp_path):
    result = runner.invoke(
        app, ["init", "c", "--context-type", "client", "--path", str(tmp_path)]
    )
    assert result.exit_code != 0  # Typer exit code 2: no such option


def test_init_with_org(tmp_path):
    runner.invoke(app, ["init", "my-corpus", "--org", "HXT", "--path", str(tmp_path)])
    from das.config import load_config
    config = load_config(tmp_path)
    assert config.org == "HXT"


def test_init_with_tags(tmp_path):
    result = runner.invoke(
        app,
        [
            "init", "my-corpus",
            "--tag", "ULS=United Life Services",
            "--tag", "PN=Pax Nocturna",
            "--path", str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    from das.config import load_config
    config = load_config(tmp_path)
    assert config.tags == {
        "ULS": "United Life Services",
        "PN": "Pax Nocturna",
    }


def test_init_without_tags_writes_no_tags_block(tmp_path):
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    import yaml
    raw = yaml.safe_load((tmp_path / "das.config.yaml").read_text())
    assert "tags" not in raw


def test_init_invalid_tag_code_exits_1(tmp_path):
    result = runner.invoke(
        app, ["init", "my-corpus", "--tag", "bad=x", "--path", str(tmp_path)]
    )
    assert result.exit_code == 1


def test_init_malformed_tag_exits_1(tmp_path):
    result = runner.invoke(
        app, ["init", "my-corpus", "--tag", "NOEQUALS", "--path", str(tmp_path)]
    )
    assert result.exit_code == 1


def test_init_already_initialized_exits_1(tmp_path):
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    result = runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    assert result.exit_code == 1


def test_add_node(tmp_path):
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    result = runner.invoke(
        app, ["add", "00", "Admin", "Company governance", "--path", str(tmp_path)]
    )
    assert result.exit_code == 0, result.output
    assert "Added [00] Admin" in result.output


def test_add_node_registers_in_manifest(tmp_path):
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    runner.invoke(
        app, ["add", "00", "Admin", "Company governance", "--path", str(tmp_path)]
    )
    from das.config import load_config
    from das.manifest import load_manifest
    config = load_config(tmp_path)
    manifest = load_manifest(tmp_path / config.manifest)
    assert "00" in manifest.nodes
    assert manifest.nodes["00"].label == "Admin"


def test_add_duplicate_node_exits_1(tmp_path):
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    runner.invoke(
        app, ["add", "00", "Admin", "Company governance", "--path", str(tmp_path)]
    )
    result = runner.invoke(
        app, ["add", "00", "Admin", "Company governance", "--path", str(tmp_path)]
    )
    assert result.exit_code == 1


def test_add_child_node(tmp_path):
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    runner.invoke(
        app, ["add", "00", "Admin", "Company governance", "--path", str(tmp_path)]
    )
    result = runner.invoke(
        app,
        ["add", "00.01", "Business-Registration", "Registration docs",
         "--path", str(tmp_path)],
    )
    assert result.exit_code == 0, result.output


def test_add_child_without_parent_exits_1(tmp_path):
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    result = runner.invoke(
        app,
        ["add", "00.01", "Business-Registration", "Registration docs",
         "--path", str(tmp_path)],
    )
    assert result.exit_code == 1


def test_add_rejects_non_numeric_address(tmp_path):
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    result = runner.invoke(app, ["add", "abc", "Foo", "bar", "--path", str(tmp_path)])
    assert result.exit_code == 1
    assert "address" in result.output.lower()


def test_add_rejects_single_digit_segment(tmp_path):
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    result = runner.invoke(app, ["add", "5", "Foo", "bar", "--path", str(tmp_path)])
    assert result.exit_code == 1


def test_add_rejects_invalid_address_leaves_manifest_empty(tmp_path):
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    runner.invoke(app, ["add", "abc", "Foo", "bar", "--path", str(tmp_path)])
    from das.config import load_config
    from das.manifest import load_manifest
    config = load_config(tmp_path)
    manifest = load_manifest(tmp_path / config.manifest)
    assert manifest.nodes == {}


def test_ls_empty_corpus(tmp_path):
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    result = runner.invoke(app, ["ls", "--path", str(tmp_path)])
    assert result.exit_code == 0


def test_ls_shows_all_nodes(tmp_path):
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    runner.invoke(app, ["add", "00", "Admin", "Company governance", "--path", str(tmp_path)])
    runner.invoke(app, ["add", "01", "Finance", "Financial records", "--path", str(tmp_path)])
    result = runner.invoke(app, ["ls", "--path", str(tmp_path)])
    assert "Admin" in result.output
    assert "Finance" in result.output


def test_ls_filters_by_parent(tmp_path):
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    runner.invoke(app, ["add", "00", "Admin", "Company governance", "--path", str(tmp_path)])
    runner.invoke(app, ["add", "00.01", "Business-Registration", "Registration docs", "--path", str(tmp_path)])
    runner.invoke(app, ["add", "01", "Finance", "Financial records", "--path", str(tmp_path)])
    result = runner.invoke(app, ["ls", "00", "--path", str(tmp_path)])
    assert "Admin" in result.output
    assert "Business-Registration" in result.output
    assert "Finance" not in result.output


def test_find_returns_matching_node(tmp_path):
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    runner.invoke(app, ["add", "00", "Admin", "Company governance", "--path", str(tmp_path)])
    runner.invoke(app, ["add", "01", "Finance", "Financial records", "--path", str(tmp_path)])
    result = runner.invoke(app, ["find", "admin", "--path", str(tmp_path)])
    assert "Admin" in result.output
    assert "Finance" not in result.output


def test_find_searches_description(tmp_path):
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    runner.invoke(app, ["add", "00", "Admin", "Company governance", "--path", str(tmp_path)])
    result = runner.invoke(app, ["find", "governance", "--path", str(tmp_path)])
    assert "Admin" in result.output


def test_find_no_results_message(tmp_path):
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    result = runner.invoke(app, ["find", "nonexistent", "--path", str(tmp_path)])
    assert "No results" in result.output
    assert result.exit_code == 0


def test_validate_clean_corpus(tmp_path):
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    runner.invoke(app, ["add", "00", "Admin", "Company governance", "--path", str(tmp_path)])
    (tmp_path / "00-Admin").mkdir()
    (tmp_path / "00-Admin" / "00-TST-some-doc.md").touch()
    result = runner.invoke(app, ["validate", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert "valid" in result.output


def test_validate_unregistered_folder_exits_1(tmp_path):
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    (tmp_path / "00-Admin").mkdir()
    result = runner.invoke(app, ["validate", "--path", str(tmp_path)])
    assert result.exit_code == 1


def test_validate_folder_without_address_exits_1(tmp_path):
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    (tmp_path / "Admin").mkdir()
    result = runner.invoke(app, ["validate", "--path", str(tmp_path)])
    assert result.exit_code == 1


def test_validate_reports_error_count(tmp_path):
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    (tmp_path / "Admin").mkdir()
    (tmp_path / "Finance").mkdir()
    result = runner.invoke(app, ["validate", "--path", str(tmp_path)])
    assert "2 validation error" in result.output
