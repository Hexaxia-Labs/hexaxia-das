import pytest
from das.config import DASConfig, load_config, write_config


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
    assert "context_type" not in raw


def test_invalid_address_separator():
    with pytest.raises(ValueError, match="address_separator"):
        DASConfig(
            version="1.0",
            corpus="test",
            initialized="2026-05-27",
            address_separator="/",
            manifest="das.manifest.yaml",
        )


def test_invalid_context_type():
    with pytest.raises(ValueError, match="context_type"):
        DASConfig(
            version="1.0",
            corpus="test",
            initialized="2026-05-27",
            address_separator=".",
            manifest="das.manifest.yaml",
            context_type="invalid",
        )


def test_tags_roundtrip(tmp_path):
    tags = {
        "ULS": "United Life Services client",
        "PN": "Pax Nocturna client",
        "LABS": "Hexaxia Labs / OSS",
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
            tags={"uls": "United Life Services"},
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
            tags={"ULS": ""},
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
