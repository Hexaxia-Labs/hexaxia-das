import pytest
from pathlib import Path
from das.config import DASConfig, write_config
from das.manifest import DASManifest, write_manifest

@pytest.fixture
def corpus(tmp_path):
    config = DASConfig(
        version="1.0",
        corpus="test-corpus",
        initialized="2026-05-27",
        address_separator=".",
        manifest="das.manifest.yaml",
        org="TST",
        context_type="client",
        date_format="YYMMDD",
    )
    manifest = DASManifest(
        version="1.0",
        corpus="test-corpus",
        updated="2026-05-27",
    )
    write_config(tmp_path, config)
    write_manifest(tmp_path / "das.manifest.yaml", manifest)
    return tmp_path
