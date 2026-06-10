import pytest
from typer.testing import CliRunner
from das.cli import app

runner = CliRunner()


def test_version_flag_outputs_version():
    from das import __version__
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


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
    runner.invoke(app, ["init", "my-corpus", "--org", "ATL", "--path", str(tmp_path)])
    from das.config import load_config
    config = load_config(tmp_path)
    assert config.org == "ATL"


def test_init_with_tags(tmp_path):
    result = runner.invoke(
        app,
        [
            "init", "my-corpus",
            "--tag", "ACME=Acme Corp",
            "--tag", "GBX=Globex",
            "--path", str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    from das.config import load_config
    config = load_config(tmp_path)
    assert config.tags == {
        "ACME": "Acme Corp",
        "GBX": "Globex",
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


def test_validate_strict_flags_bad_type(tmp_path):
    runner.invoke(app, ["init", "c", "--path", str(tmp_path)])
    runner.invoke(app, ["add", "00", "Admin", "gov", "--path", str(tmp_path)])
    (tmp_path / "00-Admin").mkdir()
    (tmp_path / "00-Admin" / "00-frobnicate-foo.md").touch()
    clean = runner.invoke(app, ["validate", "--path", str(tmp_path)])
    assert clean.exit_code == 0  # default mode ignores type
    strict = runner.invoke(app, ["validate", "--strict", "--path", str(tmp_path)])
    assert strict.exit_code == 1
    assert "type slug" in strict.output


def test_new_creates_md_file(tmp_path):
    runner.invoke(app, ["init", "c", "--path", str(tmp_path)])
    runner.invoke(app, ["add", "00", "Admin", "gov", "--path", str(tmp_path)])
    (tmp_path / "00-Admin").mkdir()
    result = runner.invoke(
        app, ["new", "00", "reference", "company-profile", "--path", str(tmp_path)]
    )
    assert result.exit_code == 0
    created = tmp_path / "00-Admin" / "00-reference-company-profile.md"
    assert created.exists()
    assert "00-Admin/00-reference-company-profile.md" in result.output


def test_new_invalid_type_exits_1(tmp_path):
    runner.invoke(app, ["init", "c", "--path", str(tmp_path)])
    (tmp_path / "00-Admin").mkdir()
    result = runner.invoke(
        app, ["new", "00", "frobnicate", "foo", "--path", str(tmp_path)]
    )
    assert result.exit_code == 1
    assert "Invalid type" in result.output


def test_new_unresolved_address_exits_1(tmp_path):
    runner.invoke(app, ["init", "c", "--path", str(tmp_path)])
    result = runner.invoke(
        app, ["new", "07", "spec", "foo", "--path", str(tmp_path)]
    )
    assert result.exit_code == 1
    assert "no folder found" in result.output


def test_new_non_md_exits_0(tmp_path):
    runner.invoke(app, ["init", "c", "--path", str(tmp_path)])
    (tmp_path / "00-Admin").mkdir()
    result = runner.invoke(
        app, ["new", "00", "report", "audit", "--ext", "pdf", "--path", str(tmp_path)]
    )
    assert result.exit_code == 0
    assert (tmp_path / "00-Admin" / "00-report-audit.pdf").exists()


def test_new_published_with_date(tmp_path):
    runner.invoke(app, ["init", "c", "--path", str(tmp_path)])
    (tmp_path / "00-Admin").mkdir()
    result = runner.invoke(
        app,
        ["new", "00", "post", "launch", "--published", "--date", "260603",
         "--path", str(tmp_path)],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "00-Admin" / "00-post-launch-260603.md").exists()


def test_new_draft_is_dateless(tmp_path):
    runner.invoke(app, ["init", "c", "--path", str(tmp_path)])
    (tmp_path / "00-Admin").mkdir()
    result = runner.invoke(
        app, ["new", "00", "post", "launch", "--path", str(tmp_path)]
    )
    assert result.exit_code == 0
    assert (tmp_path / "00-Admin" / "00-post-launch.md").exists()


def test_new_bad_date_exits_1(tmp_path):
    runner.invoke(app, ["init", "c", "--path", str(tmp_path)])
    (tmp_path / "00-Admin").mkdir()
    result = runner.invoke(
        app,
        ["new", "00", "post", "launch", "--published", "--date", "2026-06-03",
         "--path", str(tmp_path)],
    )
    assert result.exit_code == 1
    assert "YYMMDD" in result.output


def test_init_default_writes_das_address_naming_block(tmp_path):
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    import yaml
    raw = yaml.safe_load((tmp_path / "das.config.yaml").read_text())
    assert raw["naming"]["style"] == "das-address"
    assert "{address}" in raw["naming"]["pattern_draft"]


def test_init_naming_style_slug_date(tmp_path):
    result = runner.invoke(
        app,
        ["init", "labs", "--naming-style", "slug-date", "--path", str(tmp_path)],
    )
    assert result.exit_code == 0, result.output
    from das.config import load_config
    config = load_config(tmp_path)
    assert config.naming is not None
    assert config.naming.style == "slug-date"


def test_init_invalid_naming_style_exits_1(tmp_path):
    result = runner.invoke(
        app,
        ["init", "labs", "--naming-style", "bogus", "--path", str(tmp_path)],
    )
    assert result.exit_code == 1


def test_init_naming_block_roundtrips_through_load(tmp_path):
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    from das.config import load_config, NamingConvention
    config = load_config(tmp_path)
    assert isinstance(config.naming, NamingConvention)
    assert config.naming.style == "das-address"


# -- colon-space quoting (regression guard) ----------------------------------

def test_add_description_with_colon_space_produces_valid_yaml(tmp_path):
    """das add must write a manifest that yaml.safe_load can parse when the
    description contains a colon-space sequence (': ')."""
    import yaml
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    result = runner.invoke(
        app,
        [
            "add", "00", "Overview",
            "What Relay is: the governed middleware framework",
            "--path", str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    manifest_text = (tmp_path / "das.manifest.yaml").read_text()
    # Must parse without raising
    raw = yaml.safe_load(manifest_text)
    assert raw["nodes"]["00"]["description"] == (
        "What Relay is: the governed middleware framework"
    )


def test_add_agent_hint_with_colon_space_produces_valid_yaml(tmp_path):
    """das add --agent-hint must write a manifest that yaml.safe_load can parse
    when the agent_hint contains a colon-space sequence."""
    import yaml
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    result = runner.invoke(
        app,
        [
            "add", "00", "Legal", "Legal instruments",
            "--agent-hint",
            "Mixed visibility: license texts are public, risk is internal.",
            "--path", str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    raw = yaml.safe_load((tmp_path / "das.manifest.yaml").read_text())
    assert raw["nodes"]["00"]["agent_hint"] == (
        "Mixed visibility: license texts are public, risk is internal."
    )


def test_add_colon_space_description_validates_cleanly(tmp_path):
    """A corpus whose manifest has colon-space in descriptions must pass
    das validate (the manifest is loadable, not corrupted)."""
    runner.invoke(app, ["init", "my-corpus", "--path", str(tmp_path)])
    runner.invoke(
        app,
        [
            "add", "00", "Overview",
            "What Relay is: the governed middleware framework",
            "--path", str(tmp_path),
        ],
    )
    (tmp_path / "00-Overview").mkdir()
    result = runner.invoke(app, ["validate", "--path", str(tmp_path)])
    assert result.exit_code == 0, result.output
