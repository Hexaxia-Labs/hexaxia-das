from __future__ import annotations
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Optional
import re
import yaml

CONFIG_FILENAME = "das.config.yaml"
# On-disk schema version for das.config.yaml and das.manifest.yaml.
SCHEMA_VERSION = "1.0"
# A tag code is 2-5 chars: it must START WITH AN UPPERCASE LETTER, then carry
# uppercase letters and/or digits. The leading letter is the disambiguator -
# it keeps a tag distinct from a numeric address segment (all digits) on one
# side and from a lowercase type slug on the other, so real brand/product codes
# with digits (M365, O365, S3, NW7) are valid without ambiguity.
TAG_CODE_RE = re.compile(r"^[A-Z][A-Z0-9]{1,4}$")

# Recognized naming styles for a corpus's declared convention (see
# docs/corpus-conventions.md). 'das-address' is the default and behaves exactly
# as the historic address-first rules. 'slug-date' and 'custom' are deviations
# whose declared pattern is compiled to a regex by the validator.
VALID_NAMING_STYLES = {"das-address", "slug-date", "custom"}

# The default address-first convention applied when a corpus declares no
# 'naming' block. The published variant adds a publish date to the descriptor.
DEFAULT_PATTERN_DRAFT = "{address}-[{TAG}-]{type}-{descriptor}.{ext}"
DEFAULT_PATTERN_PUBLISHED = "{address}-[{TAG}-]{type}-{descriptor}-{YYMMDD}.{ext}"


@dataclass
class NamingConvention:
    """A corpus's declared filename convention.

    A corpus declares this in the 'naming' block of das.config.yaml. It is one
    machine-readable source of truth for how files are named, generated, and
    validated - replacing prose in README.md / CLAUDE.md that can drift.

    style          - 'das-address' (the default address-first rules), 'slug-date'
                     (legacy slug-first marketing files), or 'custom'.
    pattern_draft  - the canonical filename template for draft files. Tokens:
                     {address} {TAG} {type} {descriptor} {slug} {YYMMDD} {ext}.
                     An optional run is bracketed, e.g. [{TAG}-].
    pattern_published - the template once a file is promoted/published; usually
                     pattern_draft plus a publish date. Optional - a corpus with
                     no draft/published lifecycle uses pattern_draft alone.
    description    - the justification. Required by convention when style is not
                     'das-address' (deviating from address-first has a cost).
    """

    style: str = "das-address"
    pattern_draft: str = DEFAULT_PATTERN_DRAFT
    pattern_published: Optional[str] = None
    description: Optional[str] = None

    def __post_init__(self):
        if self.style not in VALID_NAMING_STYLES:
            valid = ", ".join(sorted(VALID_NAMING_STYLES))
            raise ValueError(
                f"naming style '{self.style}' is not one of: {valid}"
            )


@dataclass
class DASConfig:
    version: str
    corpus: str
    initialized: str
    address_separator: str
    manifest: str
    org: Optional[str] = None
    tags: Optional[dict[str, str]] = None
    naming: Optional[NamingConvention] = None

    def __post_init__(self):
        if self.address_separator != ".":
            raise ValueError("address_separator must be '.'")
        if self.tags:
            for code, description in self.tags.items():
                if not TAG_CODE_RE.match(code):
                    raise ValueError(
                        f"tags code '{code}' must be 2-5 uppercase "
                        "alphanumeric characters starting with a letter"
                    )
                if not isinstance(description, str) or not description.strip():
                    raise ValueError(
                        f"tags code '{code}' must have a non-empty description"
                    )
        # A naming block authored by hand in YAML arrives as a plain dict; hydrate
        # it into a NamingConvention so callers always see the typed structure.
        if isinstance(self.naming, dict):
            known = {f.name for f in fields(NamingConvention)}
            self.naming = NamingConvention(
                **{k: v for k, v in self.naming.items() if k in known}
            )


def resolve_naming(config: DASConfig) -> NamingConvention:
    """Return the effective naming convention for a corpus.

    A corpus with no declared 'naming' block resolves to the default
    address-first convention, so callers never have to special-case None.
    """
    if config.naming is not None:
        return config.naming
    return NamingConvention(
        style="das-address",
        pattern_draft=DEFAULT_PATTERN_DRAFT,
        pattern_published=DEFAULT_PATTERN_PUBLISHED,
    )


def load_config(corpus_root: Path) -> DASConfig:
    path = corpus_root / CONFIG_FILENAME
    if not path.exists():
        raise FileNotFoundError(f"{CONFIG_FILENAME} not found at {corpus_root}")
    with open(path) as f:
        data = yaml.safe_load(f)
    known_fields = {f.name for f in fields(DASConfig)}
    data = {k: v for k, v in data.items() if k in known_fields}
    return DASConfig(**data)


def _naming_to_dict(naming: NamingConvention) -> dict:
    # Mirror write_config's clean-output rule for the nested block: keep style
    # and pattern_draft (always present), omit empty pattern_published /
    # description so a minimal block stays minimal on disk.
    out: dict = {"style": naming.style, "pattern_draft": naming.pattern_draft}
    if naming.pattern_published:
        out["pattern_published"] = naming.pattern_published
    if naming.description:
        out["description"] = naming.description
    return out


def write_config(corpus_root: Path, config: DASConfig) -> None:
    path = corpus_root / CONFIG_FILENAME
    data = {}
    for k, v in vars(config).items():
        if v is None:
            continue
        if k == "naming":
            data[k] = _naming_to_dict(v)
        else:
            data[k] = v
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
