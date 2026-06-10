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
    stub = _passport_stub("02.01.04", "runbook", "netbird-ztna", "ACME", date(2026, 5, 29))
    assert stub.startswith("<!--")
    assert "passport:" in stub
    assert 'title: "Netbird Ztna"' in stub
    assert "type: runbook" in stub
    assert "status: draft" in stub
    assert "tags: [ACME]" in stub
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
    _make_folder(corpus, "02-Clients/02.01-ACME/02.01.04-Projects")
    created = create_document(corpus, "02.01.04", "runbook", "netbird-ztna")
    assert created.name == "02.01.04-runbook-netbird-ztna.md"
    assert created.parent.name == "02.01.04-Projects"
    text = created.read_text()
    assert "type: runbook" in text
    assert 'das_address: "02.01.04"' in text
    assert 'summary: ""' in text
    assert "tags:" not in text  # no tag passed


def test_create_document_with_email_type(corpus):
    # email is a v0.3.1 vocabulary type; das new must accept it.
    _make_folder(corpus, "02-Clients/02.05-Wayne-Industries")
    created = create_document(corpus, "02.05", "email", "platform-recommendation")
    assert created.name == "02.05-email-platform-recommendation.md"
    assert "type: email" in created.read_text()


def test_create_document_with_log_type(corpus):
    # log is a v0.3.1 vocabulary type; das new must accept it.
    _make_folder(corpus, "02-Clients/02.05-Wayne-Industries")
    created = create_document(corpus, "02.05", "log", "time-tracking")
    assert created.name == "02.05-log-time-tracking.md"
    assert "type: log" in created.read_text()


def test_create_document_with_tag(corpus):
    _set_tags(corpus, {"ACME": "Acme Corp"})
    _make_folder(corpus, "02.01.04-Projects")
    created = create_document(corpus, "02.01.04", "runbook", "netbird-ztna", tag="ACME")
    assert created.name == "02.01.04-ACME-runbook-netbird-ztna.md"
    assert "tags: [ACME]" in created.read_text()


def test_create_document_invalid_type(corpus):
    _make_folder(corpus, "00-Admin")
    with pytest.raises(ValueError, match="Invalid type"):
        create_document(corpus, "00", "frobnicate", "foo")


def test_create_document_bad_descriptor(corpus):
    _make_folder(corpus, "00-Admin")
    with pytest.raises(ValueError, match="[Dd]escriptor"):
        create_document(corpus, "00", "reference", "Bad Descriptor")


def test_create_document_unknown_tag(corpus):
    _set_tags(corpus, {"ACME": "Acme Corp"})
    _make_folder(corpus, "00-Admin")
    with pytest.raises(ValueError, match="unknown tag"):
        create_document(corpus, "00", "reference", "foo", tag="XYZ")


def test_create_document_tag_without_vocabulary(corpus):
    _make_folder(corpus, "00-Admin")  # corpus fixture has no tags vocab
    with pytest.raises(ValueError, match="no tags vocabulary"):
        create_document(corpus, "00", "reference", "foo", tag="ACME")


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


def test_created_file_passes_strict_validation(corpus):
    from das.validator import validate_corpus
    from das.manifest import load_manifest, add_node, write_manifest, ManifestNode

    # register the folder address in the manifest and create it on disk
    mpath = corpus / load_config(corpus).manifest
    m = load_manifest(mpath)
    add_node(m, "00", ManifestNode(label="Admin", description="gov", type="area"))
    write_manifest(mpath, m)
    (corpus / "00-Admin").mkdir()

    create_document(corpus, "00", "reference", "company-profile")
    errors = validate_corpus(corpus, strict=True)
    assert errors == []


# --- draft vs published from the declared naming convention -------------------


def _set_naming(corpus, naming):
    cfg = load_config(corpus)
    cfg.naming = naming
    write_config(corpus, cfg)


def test_create_document_published_appends_date(corpus):
    from das.config import NamingConvention
    _set_naming(corpus, NamingConvention(
        style="das-address",
        pattern_draft="{address}-{type}-{slug}.{ext}",
        pattern_published="{address}-{type}-{slug}-{YYMMDD}.{ext}",
    ))
    _make_folder(corpus, "01-Posts")
    created = create_document(
        corpus, "01", "post", "you-have-a-corpus",
        published=True, date_str="260603",
    )
    assert created.name == "01-post-you-have-a-corpus-260603.md"


def test_create_document_draft_is_dateless_by_default(corpus):
    from das.config import NamingConvention
    _set_naming(corpus, NamingConvention(
        style="das-address",
        pattern_draft="{address}-{type}-{slug}.{ext}",
        pattern_published="{address}-{type}-{slug}-{YYMMDD}.{ext}",
    ))
    _make_folder(corpus, "01-Posts")
    created = create_document(corpus, "01", "post", "you-have-a-corpus")
    assert created.name == "01-post-you-have-a-corpus.md"


def test_create_document_default_pattern_unchanged_without_naming_block(corpus):
    # No naming block: behaves exactly as before (tag-aware standard pattern).
    _set_tags(corpus, {"ACME": "Acme Corp"})
    _make_folder(corpus, "02.01.04-Projects")
    created = create_document(corpus, "02.01.04", "runbook", "netbird-ztna", tag="ACME")
    assert created.name == "02.01.04-ACME-runbook-netbird-ztna.md"


def test_create_document_published_uses_today_when_no_date_given(corpus):
    from das.config import NamingConvention
    from datetime import date
    _set_naming(corpus, NamingConvention(
        style="das-address",
        pattern_draft="{address}-{type}-{slug}.{ext}",
        pattern_published="{address}-{type}-{slug}-{YYMMDD}.{ext}",
    ))
    _make_folder(corpus, "01-Posts")
    created = create_document(corpus, "01", "post", "foo", published=True)
    expected_date = date.today().strftime("%y%m%d")
    assert created.name == f"01-post-foo-{expected_date}.md"


def test_create_document_published_without_published_pattern_errors(corpus):
    from das.config import NamingConvention
    _set_naming(corpus, NamingConvention(
        style="das-address",
        pattern_draft="{address}-{type}-{slug}.{ext}",
    ))
    _make_folder(corpus, "01-Posts")
    with pytest.raises(ValueError, match="no published pattern"):
        create_document(corpus, "01", "post", "foo", published=True)


def test_create_document_bad_date_string_errors(corpus):
    from das.config import NamingConvention
    _set_naming(corpus, NamingConvention(
        style="das-address",
        pattern_draft="{address}-{type}-{slug}.{ext}",
        pattern_published="{address}-{type}-{slug}-{YYMMDD}.{ext}",
    ))
    _make_folder(corpus, "01-Posts")
    with pytest.raises(ValueError, match="YYMMDD"):
        create_document(corpus, "01", "post", "foo", published=True, date_str="2026-06-03")
