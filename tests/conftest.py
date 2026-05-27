import pytest
from pathlib import Path
from jdx.config import JDXConfig, write_config
from jdx.manifest import JDXManifest, write_manifest

@pytest.fixture
def corpus(tmp_path):
    config = JDXConfig(
        version="1.0",
        corpus="test-corpus",
        initialized="2026-05-27",
        address_separator=".",
        manifest="jdx.manifest.yaml",
        org="TST",
        context_type="client",
        date_format="YYMMDD",
    )
    manifest = JDXManifest(
        version="1.0",
        corpus="test-corpus",
        updated="2026-05-27",
    )
    write_config(tmp_path, config)
    write_manifest(tmp_path / "jdx.manifest.yaml", manifest)
    return tmp_path
