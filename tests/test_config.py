import pytest
from jdx.config import JDXConfig, load_config, write_config


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
    config = JDXConfig(
        version="1.0",
        corpus="my-corpus",
        initialized="2026-05-27",
        address_separator=".",
        manifest="jdx.manifest.yaml",
    )
    write_config(tmp_path, config)
    loaded = load_config(tmp_path)
    assert loaded.corpus == "my-corpus"
    assert loaded.org is None


def test_optional_fields_omitted_from_file(tmp_path):
    config = JDXConfig(
        version="1.0",
        corpus="bare",
        initialized="2026-05-27",
        address_separator=".",
        manifest="jdx.manifest.yaml",
    )
    write_config(tmp_path, config)
    import yaml
    raw = yaml.safe_load((tmp_path / "jdx.config.yaml").read_text())
    assert "org" not in raw
    assert "context_type" not in raw


def test_invalid_address_separator():
    with pytest.raises(ValueError, match="address_separator"):
        JDXConfig(
            version="1.0",
            corpus="test",
            initialized="2026-05-27",
            address_separator="/",
            manifest="jdx.manifest.yaml",
        )


def test_invalid_context_type():
    with pytest.raises(ValueError, match="context_type"):
        JDXConfig(
            version="1.0",
            corpus="test",
            initialized="2026-05-27",
            address_separator=".",
            manifest="jdx.manifest.yaml",
            context_type="invalid",
        )
