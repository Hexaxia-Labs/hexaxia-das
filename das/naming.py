from __future__ import annotations
import re
from typing import Pattern

# Maps a naming-pattern token to the regex fragment that validates it. The
# fragments are deliberately the same building blocks the address-first rules
# already use, so a compiled pattern enforces the spec piece-by-piece:
#   {address}    2+-digit dotted segments (matches ADDRESS_RE without anchors)
#   {TAG}        a 2-5 char tag code: a leading uppercase letter, then
#                uppercase letters and/or digits (e.g. ACME, NW7, M365)
#   {type}       a lowercase type slug (one word, no hyphens)
#   {descriptor} / {slug}  a lowercase-hyphenated run (matches DESCRIPTOR_RE)
#   {YYMMDD}     a six-digit date
#   {ext}        a lowercase file extension
#
# Tokens are non-capturing so that optional bracketed groups can wrap them
# cleanly. The descriptor/slug fragment is greedy across hyphens, which is fine
# because the surrounding literals (e.g. '-{YYMMDD}', '.{ext}') and the trailing
# anchors pin the boundaries.
TOKEN_FRAGMENTS = {
    "address": r"\d{2,}(?:\.\d{2,})*",
    "TAG": r"[A-Z][A-Z0-9]{1,4}",
    "type": r"[a-z]+",
    "descriptor": r"[a-z0-9]+(?:-[a-z0-9]+)*",
    "slug": r"[a-z0-9]+(?:-[a-z0-9]+)*",
    "YYMMDD": r"\d{6}",
    "ext": r"[a-z0-9]+",
}

# A single {token} occurrence.
_TOKEN_RE = re.compile(r"\{([A-Za-z]+)\}")


def _segment_to_regex(segment: str) -> str:
    """Translate a pattern segment (no brackets) into a regex fragment.

    Literal characters between tokens are escaped; recognized {tokens} become
    their TOKEN_FRAGMENTS entry. An unknown token is treated as a literal so a
    typo fails loudly at match time rather than silently matching anything.
    """
    out: list[str] = []
    pos = 0
    for m in _TOKEN_RE.finditer(segment):
        out.append(re.escape(segment[pos:m.start()]))
        token = m.group(1)
        if token in TOKEN_FRAGMENTS:
            out.append(f"(?:{TOKEN_FRAGMENTS[token]})")
        else:
            out.append(re.escape(m.group(0)))
        pos = m.end()
    out.append(re.escape(segment[pos:]))
    return "".join(out)


def _pattern_to_regex(pattern: str) -> str:
    """Translate a full naming pattern into an anchored regex source string.

    Supports optional groups written as [ ... ] (e.g. '[{TAG}-]'), which become
    a regex '(?:...)?' so the run is allowed to be absent.
    """
    out: list[str] = []
    pos = 0
    depth = 0
    buf: list[str] = []
    for i, ch in enumerate(pattern):
        if ch == "[":
            if depth == 0:
                out.append(_segment_to_regex(pattern[pos:i]))
                buf = []
                pos = i + 1
            depth += 1
        elif ch == "]" and depth > 0:
            depth -= 1
            if depth == 0:
                out.append(f"(?:{_segment_to_regex(pattern[pos:i])})?")
                pos = i + 1
    if depth != 0:
        raise ValueError(f"unbalanced '[' in naming pattern: {pattern!r}")
    out.append(_segment_to_regex(pattern[pos:]))
    return "^" + "".join(out) + "$"


def compile_pattern(pattern: str) -> Pattern[str]:
    """Compile a naming pattern into an anchored, full-name regex.

    The returned regex matches a complete filename (it is anchored at both
    ends). Use it to validate that a file conforms to a declared convention.
    """
    return re.compile(_pattern_to_regex(pattern))


def render_pattern(pattern: str, **values: str) -> str:
    """Render a concrete filename from a pattern and token values.

    Optional bracketed groups (e.g. '[{TAG}-]') are emitted only when every
    token inside them has a non-empty value; otherwise the whole group is
    dropped. Tokens outside any bracket are required - a missing one raises.
    """
    out: list[str] = []
    pos = 0
    depth = 0
    for i, ch in enumerate(pattern):
        if ch == "[":
            if depth == 0:
                out.append(_render_segment(pattern[pos:i], values, optional=False))
                pos = i + 1
            depth += 1
        elif ch == "]" and depth > 0:
            depth -= 1
            if depth == 0:
                out.append(_render_segment(pattern[pos:i], values, optional=True))
                pos = i + 1
    if depth != 0:
        raise ValueError(f"unbalanced '[' in naming pattern: {pattern!r}")
    out.append(_render_segment(pattern[pos:], values, optional=False))
    return "".join(out)


def _render_segment(segment: str, values: dict, optional: bool) -> str:
    tokens = _TOKEN_RE.findall(segment)
    if optional and any(not values.get(t) for t in tokens):
        return ""  # an optional group with any empty token is dropped whole

    def repl(m: re.Match) -> str:
        token = m.group(1)
        value = values.get(token)
        if value is None or value == "":
            raise ValueError(f"missing value for required token '{{{token}}}'")
        return str(value)

    return _TOKEN_RE.sub(repl, segment)
