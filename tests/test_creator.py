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
