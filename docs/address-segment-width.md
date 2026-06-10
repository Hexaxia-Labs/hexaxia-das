# Address Segment Width

DAS addresses are dotted sequences of numeric segments: `10.02.07`. The default is
two digits per segment (`00`-`99`). That default is right for most corpora, but it is
a choice, not a hard constraint. This document explains when to widen a segment, how
to do it correctly, and what wider segments mean for tools and humans reading the address.

---

## What segment width means

The width of a segment is the number of digits in each part of the address. It determines
how many sibling nodes can exist under the same parent:

| Width | Range | Slots |
|-------|-------|-------|
| 2 digits | `00`-`99` | 100 |
| 3 digits | `000`-`999` | 1,000 |
| 4 digits | `0000`-`9999` | 10,000 |

Width is a per-level decision, not a global corpus setting. You can use two-digit area
addresses and three-digit program addresses in the same corpus:

```
10          <- two-digit area
10.01       <- two-digit category
10.01.001   <- three-digit individual program
10.01.002
```

What you cannot do is mix widths *at the same level under the same parent* - that makes
the address space ambiguous and sort order undefined. `10.01` and `10.001` cannot both
be children of `10`.

---

## The default: two digits

Two digits is right for almost every corpus you will build by hand. It provides 100 slots
per level, which is plenty for:

- Areas in a product corpus (you will rarely have more than 20)
- Categories within an area (rarely more than 10-15)
- Documents in a category (if you hit 50+ documents in one category, consider whether a
  subcategory is overdue)

Two digits also keeps addresses short and human-legible. `10.02.07` reads naturally;
`010.002.007` does not. The cognitive load of scanning an address increases with its length,
and DAS addresses are used as visual landmarks - they should be glanceable.

---

## Three digits: when and why

Three digits (`000`-`999`) is the first widening step. Choose it for a specific level when
you have a **concrete, known reason to expect more than 99 siblings** at that level, and
subdividing into sub-categories would not help (either because the items are genuinely flat,
or because the sub-classification overhead outweighs the benefit).

**The cases where three digits fits:**

**Large data or research corpora.** A sensor-telemetry corpus expecting several hundred readings
under a single device category, a document archive ingesting an entire company filing
system, a corpus of legal cases or research papers - any situation where the primary artifact
count is expected to exceed 99 and the artifacts are all of the same type. Subdividing 300
telemetry runs into subcategories (`10.01.01-Lab-Sourced`, `10.01.02-Lab-Synthetic`)
only gets you two-digit space back under each sub-category; if either sub-category itself
will exceed 99, three digits at the program level is the right answer.

**Automated ingestion pipelines.** When a tool (ETL, a bulk-import script) is filing
documents rather than a human, the visual-scanning argument for short addresses weakens.
A tool does not care whether it reads `10.001` or `10.01`. Three digits accommodates a full
pipeline run without the operator needing to manage segment boundaries mid-run.

**Long-lived archives with known scale.** A corpus being built to hold all historical
records from a department that has been operating for 20 years, where the document count
is already known to be in the hundreds, is a candidate for three digits at the document level
from the start. Retrofitting a width change mid-corpus is expensive (all existing addresses
must be re-padded and the manifest rewritten).

**Three digits does not fit when:**

- You are just being cautious. If you have 30 documents now and might have 150 in five years,
  two digits still works - you have 70 free slots, and the corpus may evolve in structure
  before it fills them.
- The real fix is a sub-level. Eighty programs of three distinct operation types should be
  three categories of ~27 programs each, not a flat 80-program list needing three digits.
- The corpus is primarily navigated by humans. Humans read addresses as visual landmarks.
  Three-digit addresses are noticeably harder to scan, especially at four or five levels deep.

---

## Four digits: edge cases only

Four digits (`0000`-`9999`) is warranted only in large automated pipelines where a single
category will hold thousands of items. In practice, if you are at four digits, you are almost
certainly building a tool-managed corpus where human readability of individual addresses is
not a design goal - the address is a machine key, not a navigation landmark.

Before choosing four digits, verify that the corpus genuinely cannot be subdivided. A corpus
of 5,000 legal documents can almost always be organized into areas by year, jurisdiction, or
document type, reducing any single category to a scale where three digits suffices.

---

## Mixing widths across levels

The practical pattern when widths differ across levels:

```
# Two-digit areas, two-digit categories, three-digit readings
10            Area: Readings-MK1
10.01         Category: Sourced
10.01.001     Reading: first sourced MK1 reading
10.01.002     ...
10.02         Category: Synthetic
10.02.001     Reading: first synthetic MK1 reading
```

This is clean and readable: the area and category structure reads normally (two digits,
human-navigable), and the program level carries the wider width only where the scale demands
it.

The manifest and validator treat each segment as a string comparison, so `10.01.001` and
`10.01.002` sort correctly between `10.01` and `10.02`. No special configuration is required
as long as the width is consistent within each level.

---

## Declaring segment width in corpus conventions

Any corpus that deviates from the two-digit default should record it in its `00.01-Conventions`
document. The declaration should state:

- Which level uses the wider width
- Why (the concrete capacity reason)
- The expected range (three digits for up to 999, four for up to 9,999)

Example conventions entry:

```
Address width: two-digit default, except the program level under 10.01-Sourced and
10.02-Synthetic, which uses three digits (000-999) because the sourced set is expected
to exceed 99 programs once public GitHub repos are ingested. All other levels remain
two-digit.
```

This declaration is the contract for future maintainers. Without it, a three-digit address
reads as a mistake rather than a deliberate choice.

---

## Retrofitting width

Changing segment width on an existing corpus is expensive and should be avoided. The
permanence rule applies: if `10.01.01` exists in the manifest and is referenced anywhere,
it cannot become `10.01.001` without a full migration.

The right time to decide on width is at corpus initialization, when you know the expected
scale but before any addresses are assigned. If you missed the window:

- For a young, uncalcified corpus (nothing external depends on the addresses): treat it
  as a reshape (see `restructuring-a-corpus.md`), deprecate the two-digit addresses, and
  re-file at three-digit addresses.
- For a mature corpus: live with two digits and add a sub-level when you approach the
  99-item limit. The sub-level costs one extra depth, but it is far cheaper than a
  full corpus re-address.

---

## Summary

| Digits | Slots | Use when |
|--------|-------|----------|
| 2 (default) | 100 | Almost always - human-navigated corpora at any scale |
| 3 | 1,000 | Specific level known to exceed 99 items; data/research corpora; automated ingestion |
| 4 | 10,000 | Large automated pipelines where machine-key use outweighs human readability |

Default to two digits. Widen deliberately, at a specific level, with a documented reason.
Never mix widths at the same level under the same parent.
