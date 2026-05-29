from datetime import date

from das.creator import _titleize, _passport_stub, DESCRIPTOR_RE


def test_titleize_maps_hyphenated_descriptor():
    assert _titleize("netbird-ztna") == "Netbird Ztna"
    assert _titleize("msa") == "Msa"


def test_descriptor_re_accepts_valid_and_rejects_invalid():
    assert DESCRIPTOR_RE.match("netbird-ztna")
    assert DESCRIPTOR_RE.match("q2-social-brief")
    assert DESCRIPTOR_RE.match("msa")
    assert not DESCRIPTOR_RE.match("Net Bird")   # space + uppercase
    assert not DESCRIPTOR_RE.match("net_bird")    # underscore
    assert not DESCRIPTOR_RE.match("NetBird")     # uppercase
    assert not DESCRIPTOR_RE.match("-leading")    # leading hyphen
    assert not DESCRIPTOR_RE.match("trailing-")   # trailing hyphen


def test_passport_stub_contains_expected_fields_with_tag():
    stub = _passport_stub("02.01.04", "runbook", "netbird-ztna", "ULS", date(2026, 5, 29))
    assert stub.startswith("<!--")
    assert "passport:" in stub
    assert 'title: "Netbird Ztna"' in stub
    assert "type: runbook" in stub
    assert "status: draft" in stub
    assert "tags: [ULS]" in stub
    assert 'das_address: "02.01.04"' in stub
    assert 'created: "2026-05-29"' in stub
    assert 'summary: ""' in stub
    assert "-->" in stub
    assert "# Netbird Ztna" in stub


def test_passport_stub_omits_tags_line_without_tag():
    stub = _passport_stub("00", "reference", "company-profile", None, date(2026, 5, 29))
    assert "tags:" not in stub
    assert "type: reference" in stub


import pytest
from das.creator import create_document
from das.config import load_config, write_config


def _make_folder(corpus, rel):
    d = corpus / rel
    d.mkdir(parents=True, exist_ok=True)
    return d


def _set_tags(corpus, tags):
    cfg = load_config(corpus)
    cfg.tags = tags
    write_config(corpus, cfg)


def test_create_document_writes_md_with_stub(corpus):
    _make_folder(corpus, "02-Clients/02.01-ULS/02.01.04-Projects")
    created = create_document(corpus, "02.01.04", "runbook", "netbird-ztna")
    assert created.name == "02.01.04-runbook-netbird-ztna.md"
    assert created.parent.name == "02.01.04-Projects"
    text = created.read_text()
    assert "type: runbook" in text
    assert 'das_address: "02.01.04"' in text
    assert 'summary: ""' in text
    assert "tags:" not in text  # no tag passed


def test_create_document_with_tag(corpus):
    _set_tags(corpus, {"ULS": "United Life Services"})
    _make_folder(corpus, "02.01.04-Projects")
    created = create_document(corpus, "02.01.04", "runbook", "netbird-ztna", tag="ULS")
    assert created.name == "02.01.04-ULS-runbook-netbird-ztna.md"
    assert "tags: [ULS]" in created.read_text()


def test_create_document_invalid_type(corpus):
    _make_folder(corpus, "00-Admin")
    with pytest.raises(ValueError, match="Invalid type"):
        create_document(corpus, "00", "frobnicate", "foo")


def test_create_document_bad_descriptor(corpus):
    _make_folder(corpus, "00-Admin")
    with pytest.raises(ValueError, match="[Dd]escriptor"):
        create_document(corpus, "00", "reference", "Bad Descriptor")


def test_create_document_unknown_tag(corpus):
    _set_tags(corpus, {"ULS": "United Life Services"})
    _make_folder(corpus, "00-Admin")
    with pytest.raises(ValueError, match="unknown tag"):
        create_document(corpus, "00", "reference", "foo", tag="XYZ")


def test_create_document_tag_without_vocabulary(corpus):
    _make_folder(corpus, "00-Admin")  # corpus fixture has no tags vocab
    with pytest.raises(ValueError, match="no tags vocabulary"):
        create_document(corpus, "00", "reference", "foo", tag="ULS")


def test_create_document_no_folder_for_address(corpus):
    with pytest.raises(ValueError, match="no folder found"):
        create_document(corpus, "07", "spec", "foo")


def test_create_document_ambiguous_folder(corpus):
    _make_folder(corpus, "a/00-Admin")
    _make_folder(corpus, "b/00-Other")
    with pytest.raises(ValueError, match="ambiguous"):
        create_document(corpus, "00", "reference", "foo")


def test_create_document_no_overwrite(corpus):
    folder = _make_folder(corpus, "00-Admin")
    (folder / "00-reference-foo.md").write_text("existing")
    with pytest.raises(ValueError, match="already exists"):
        create_document(corpus, "00", "reference", "foo")


def test_create_document_non_md_has_no_passport(corpus):
    _make_folder(corpus, "00-Admin")
    created = create_document(corpus, "00", "report", "audit", ext="pdf")
    assert created.name == "00-report-audit.pdf"
    assert created.read_text() == ""  # bare file, no passport block


def test_create_document_invalid_address(corpus):
    with pytest.raises(ValueError, match="[Aa]ddress"):
        create_document(corpus, "abc", "reference", "foo")
