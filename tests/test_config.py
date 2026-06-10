import pytest
from das.config import DASConfig, NamingConvention, load_config, write_config


def test_load_config(corpus):
    config = load_config(corpus)
    assert config.corpus == "test-corpus"
    assert config.version == "1.0"
    assert config.address_separator == "."
    assert config.org == "TST"


def test_load_config_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path)


def test_write_config_roundtrip(tmp_path):
    config = DASConfig(
        version="1.0",
        corpus="my-corpus",
        initialized="2026-05-27",
        address_separator=".",
        manifest="das.manifest.yaml",
    )
    write_config(tmp_path, config)
    loaded = load_config(tmp_path)
    assert loaded.corpus == "my-corpus"
    assert loaded.org is None


def test_optional_fields_omitted_from_file(tmp_path):
    config = DASConfig(
        version="1.0",
        corpus="bare",
        initialized="2026-05-27",
        address_separator=".",
        manifest="das.manifest.yaml",
    )
    write_config(tmp_path, config)
    import yaml
    raw = yaml.safe_load((tmp_path / "das.config.yaml").read_text())
    assert "org" not in raw
    assert "tags" not in raw


def test_dasconfig_has_no_legacy_fields():
    cfg = DASConfig(
        version="1.0",
        corpus="x",
        initialized="2026-05-29",
        address_separator=".",
        manifest="das.manifest.yaml",
    )
    assert not hasattr(cfg, "context_type")
    assert not hasattr(cfg, "date_format")


def test_legacy_config_with_dropped_fields_still_loads(tmp_path):
    import yaml
    (tmp_path / "das.config.yaml").write_text(yaml.safe_dump({
        "version": "1.0",
        "corpus": "x",
        "initialized": "2026-05-29",
        "address_separator": ".",
        "manifest": "das.manifest.yaml",
        "context_type": "client",
        "date_format": "YYMMDD",
    }))
    cfg = load_config(tmp_path)
    assert cfg.corpus == "x"
    assert not hasattr(cfg, "context_type")


def test_invalid_address_separator():
    with pytest.raises(ValueError, match="address_separator"):
        DASConfig(
            version="1.0",
            corpus="test",
            initialized="2026-05-27",
            address_separator="/",
            manifest="das.manifest.yaml",
        )


def test_tags_roundtrip(tmp_path):
    tags = {
        "ACME": "Acme Corp client",
        "GBX": "Globex client",
        "OSS": "Open-source / community",
    }
    config = DASConfig(
        version="1.0",
        corpus="tagged",
        initialized="2026-05-27",
        address_separator=".",
        manifest="das.manifest.yaml",
        tags=tags,
    )
    write_config(tmp_path, config)
    loaded = load_config(tmp_path)
    assert loaded.tags == tags


def test_tags_absent_loads_none_and_omitted_from_file(tmp_path):
    config = DASConfig(
        version="1.0",
        corpus="bare",
        initialized="2026-05-27",
        address_separator=".",
        manifest="das.manifest.yaml",
    )
    write_config(tmp_path, config)
    import yaml
    raw = yaml.safe_load((tmp_path / "das.config.yaml").read_text())
    assert "tags" not in raw
    loaded = load_config(tmp_path)
    assert loaded.tags is None


def test_tags_reject_lowercase_code():
    with pytest.raises(ValueError, match="tags"):
        DASConfig(
            version="1.0",
            corpus="test",
            initialized="2026-05-27",
            address_separator=".",
            manifest="das.manifest.yaml",
            tags={"acme": "Acme Corp"},
        )


def test_tags_accept_alphanumeric_code():
    # Real brand/product codes commonly contain digits (NW7, M365). A tag
    # must start with an uppercase letter, then uppercase letters and digits.
    tags = {
        "NW7": "Skyworks venture / brand",
        "M365": "Microsoft 365 market",
        "ACME": "Acme Corp client",
    }
    config = DASConfig(
        version="1.0",
        corpus="alnum",
        initialized="2026-06-09",
        address_separator=".",
        manifest="das.manifest.yaml",
        tags=tags,
    )
    assert config.tags == tags


def test_tags_reject_purely_numeric_code():
    # A tag must start with a letter so it can never be confused with a numeric
    # address segment; an all-digit token like '868' is not a valid tag.
    with pytest.raises(ValueError, match="tags"):
        DASConfig(
            version="1.0",
            corpus="test",
            initialized="2026-06-09",
            address_separator=".",
            manifest="das.manifest.yaml",
            tags={"868": "all digits, not a tag"},
        )


def test_tags_reject_too_long_code():
    with pytest.raises(ValueError, match="tags"):
        DASConfig(
            version="1.0",
            corpus="test",
            initialized="2026-05-27",
            address_separator=".",
            manifest="das.manifest.yaml",
            tags={"TOOLONG": "way too long"},
        )


def test_tags_reject_empty_description():
    with pytest.raises(ValueError, match="tags"):
        DASConfig(
            version="1.0",
            corpus="test",
            initialized="2026-05-27",
            address_separator=".",
            manifest="das.manifest.yaml",
            tags={"ACME": ""},
        )


def test_older_config_without_tags_loads(tmp_path):
    import yaml
    raw = {
        "version": "1.0",
        "corpus": "legacy",
        "initialized": "2026-05-27",
        "address_separator": ".",
        "manifest": "das.manifest.yaml",
        "org": "OLD",
    }
    (tmp_path / "das.config.yaml").write_text(yaml.dump(raw))
    loaded = load_config(tmp_path)
    assert loaded.corpus == "legacy"
    assert loaded.tags is None


def test_naming_absent_loads_none_and_omitted_from_file(tmp_path):
    config = DASConfig(
        version="1.0",
        corpus="bare",
        initialized="2026-05-27",
        address_separator=".",
        manifest="das.manifest.yaml",
    )
    write_config(tmp_path, config)
    import yaml
    raw = yaml.safe_load((tmp_path / "das.config.yaml").read_text())
    assert "naming" not in raw
    loaded = load_config(tmp_path)
    assert loaded.naming is None


def test_naming_block_roundtrip(tmp_path):
    naming = NamingConvention(
        style="das-address",
        pattern_draft="{address}-{type}-{slug}.{ext}",
        pattern_published="{address}-{type}-{slug}-{YYMMDD}.{ext}",
        description="Address-first for navigation, slug for legibility.",
    )
    config = DASConfig(
        version="1.0",
        corpus="content",
        initialized="2026-05-27",
        address_separator=".",
        manifest="das.manifest.yaml",
        naming=naming,
    )
    write_config(tmp_path, config)
    loaded = load_config(tmp_path)
    assert isinstance(loaded.naming, NamingConvention)
    assert loaded.naming.style == "das-address"
    assert loaded.naming.pattern_draft == "{address}-{type}-{slug}.{ext}"
    assert loaded.naming.pattern_published == "{address}-{type}-{slug}-{YYMMDD}.{ext}"
    assert loaded.naming.description == "Address-first for navigation, slug for legibility."


def test_naming_block_written_as_nested_mapping(tmp_path):
    naming = NamingConvention(
        style="slug-date",
        pattern_draft="{slug}.{ext}",
        pattern_published="{slug}-{YYMMDD}.{ext}",
        description="Legacy marketing files.",
    )
    config = DASConfig(
        version="1.0",
        corpus="labs",
        initialized="2026-05-27",
        address_separator=".",
        manifest="das.manifest.yaml",
        naming=naming,
    )
    write_config(tmp_path, config)
    import yaml
    raw = yaml.safe_load((tmp_path / "das.config.yaml").read_text())
    assert raw["naming"]["style"] == "slug-date"
    assert raw["naming"]["pattern_published"] == "{slug}-{YYMMDD}.{ext}"


def test_naming_empty_fields_omitted_from_file(tmp_path):
    # A naming block with only a style and a single pattern should not emit
    # empty pattern_published / description keys.
    naming = NamingConvention(style="das-address", pattern_draft="{address}-{type}-{slug}.{ext}")
    config = DASConfig(
        version="1.0",
        corpus="content",
        initialized="2026-05-27",
        address_separator=".",
        manifest="das.manifest.yaml",
        naming=naming,
    )
    write_config(tmp_path, config)
    import yaml
    raw = yaml.safe_load((tmp_path / "das.config.yaml").read_text())
    assert "pattern_published" not in raw["naming"]
    assert "description" not in raw["naming"]
    assert "style" in raw["naming"]


def test_naming_dict_in_yaml_loads_to_dataclass(tmp_path):
    # A config authored by hand with a naming mapping must hydrate into a
    # NamingConvention, not stay a bare dict.
    import yaml
    (tmp_path / "das.config.yaml").write_text(yaml.safe_dump({
        "version": "1.0",
        "corpus": "content",
        "initialized": "2026-05-27",
        "address_separator": ".",
        "manifest": "das.manifest.yaml",
        "naming": {
            "style": "das-address",
            "pattern_draft": "{address}-{type}-{slug}.{ext}",
            "pattern_published": "{address}-{type}-{slug}-{YYMMDD}.{ext}",
        },
    }))
    loaded = load_config(tmp_path)
    assert isinstance(loaded.naming, NamingConvention)
    assert loaded.naming.style == "das-address"


def test_naming_rejects_unknown_style():
    with pytest.raises(ValueError, match="style"):
        NamingConvention(style="invented", pattern_draft="{slug}.{ext}")


def test_naming_extra_keys_in_yaml_are_filtered(tmp_path):
    # Forward-compat: an unknown sub-key in the naming mapping must not crash.
    import yaml
    (tmp_path / "das.config.yaml").write_text(yaml.safe_dump({
        "version": "1.0",
        "corpus": "content",
        "initialized": "2026-05-27",
        "address_separator": ".",
        "manifest": "das.manifest.yaml",
        "naming": {
            "style": "das-address",
            "pattern_draft": "{address}-{type}-{slug}.{ext}",
            "future_field": "ignored",
        },
    }))
    loaded = load_config(tmp_path)
    assert isinstance(loaded.naming, NamingConvention)
    assert not hasattr(loaded.naming, "future_field")


def test_resolve_naming_defaults_to_das_address():
    from das.config import resolve_naming
    config = DASConfig(
        version="1.0",
        corpus="bare",
        initialized="2026-05-27",
        address_separator=".",
        manifest="das.manifest.yaml",
    )
    resolved = resolve_naming(config)
    assert resolved.style == "das-address"
    assert "{address}" in resolved.pattern_draft
