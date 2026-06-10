import pytest

from das.naming import compile_pattern, render_pattern


def test_compile_slug_date_published_matches():
    rx = compile_pattern("{slug}-{YYMMDD}.{ext}")
    assert rx.match("labs-launch-social-260526.md")
    assert rx.match("you-have-a-corpus-260603.md")


def test_compile_slug_date_rejects_missing_date():
    rx = compile_pattern("{slug}-{YYMMDD}.{ext}")
    # No 6-digit date tail - the pattern requires one.
    assert not rx.match("labs-launch-social.md")


def test_compile_slug_date_rejects_uppercase_slug():
    rx = compile_pattern("{slug}-{YYMMDD}.{ext}")
    assert not rx.match("Labs-Launch-260526.md")


def test_compile_address_first_pattern_matches():
    rx = compile_pattern("{address}-{type}-{slug}.{ext}")
    assert rx.match("01.01.01-post-you-have-a-corpus.md")
    assert not rx.match("post-you-have-a-corpus.md")  # no address prefix


def test_compile_optional_tag_group():
    rx = compile_pattern("{address}-[{TAG}-]{type}-{descriptor}.{ext}")
    assert rx.match("02.01.04-ACME-runbook-netbird-ztna.md")  # tag present
    assert rx.match("00-reference-company-profile.md")        # tag absent


def test_compile_tag_token_accepts_alphanumeric():
    # The {TAG} fragment must accept uppercase-alphanumeric codes (NW7, M365)
    # that start with a letter, and still reject all-digit or lowercase tokens.
    rx = compile_pattern("{address}-[{TAG}-]{type}-{descriptor}.{ext}")
    assert rx.match("00.01.04-NW7-reference-venture-structure.md")  # digits in tag
    assert rx.match("00.01.04-M365-runbook-rollout.md")
    assert rx.match("02.01.04-ACME-runbook-netbird-ztna.md")           # letters only
    # An all-digit token is not a tag: '868' is consumed as the {type}? No -
    # {type} is lowercase, so this only matches if the tag group is absent.
    # '868' cannot be a tag, so the optional [TAG-] group must drop and '868'
    # would have to be the lowercase type, which it is not -> no match.
    assert not rx.match("00.01.04-868-runbook-foo.md")


def test_compile_literal_text_is_escaped():
    # A literal '.' in the pattern must match a literal dot, not any char.
    rx = compile_pattern("{slug}.{ext}")
    assert rx.match("hello.md")
    assert not rx.match("helloXmd")


def test_compile_address_token_requires_two_digit_segments():
    rx = compile_pattern("{address}-{type}-{slug}.{ext}")
    assert not rx.match("1-post-foo.md")     # single-digit segment
    assert rx.match("01-post-foo.md")


def test_render_draft_pattern_inserts_tokens():
    out = render_pattern(
        "{address}-{type}-{slug}.{ext}",
        address="01.01.01",
        type="post",
        slug="you-have-a-corpus",
        ext="md",
    )
    assert out == "01.01.01-post-you-have-a-corpus.md"


def test_render_published_pattern_inserts_date():
    out = render_pattern(
        "{address}-{type}-{slug}-{YYMMDD}.{ext}",
        address="01.01.01",
        type="post",
        slug="you-have-a-corpus",
        YYMMDD="260603",
        ext="md",
    )
    assert out == "01.01.01-post-you-have-a-corpus-260603.md"


def test_render_optional_tag_present_and_absent():
    with_tag = render_pattern(
        "{address}-[{TAG}-]{type}-{descriptor}.{ext}",
        address="02.01.04",
        TAG="ACME",
        type="runbook",
        descriptor="netbird-ztna",
        ext="md",
    )
    assert with_tag == "02.01.04-ACME-runbook-netbird-ztna.md"
    without_tag = render_pattern(
        "{address}-[{TAG}-]{type}-{descriptor}.{ext}",
        address="00",
        type="reference",
        descriptor="company-profile",
        ext="md",
    )
    assert without_tag == "00-reference-company-profile.md"


def test_descriptor_and_slug_are_interchangeable_token_names():
    # {slug} and {descriptor} both mean a lowercase-hyphenated run.
    rx_slug = compile_pattern("{address}-{type}-{slug}.{ext}")
    rx_desc = compile_pattern("{address}-{type}-{descriptor}.{ext}")
    assert rx_slug.match("00-post-foo-bar.md")
    assert rx_desc.match("00-post-foo-bar.md")
