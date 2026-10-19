"""Derive a GEDCOM QUAY value (0–3) from the evidence model (ADR 0022).

QUAY is never entered by hand: it follows from the source form, the
information quality and the evidence type of the best citation.
  3 = direct evidence, primary information, original or derivative source
  2 = secondary information, or indirect evidence from primary information
  1 = undetermined information, or authored work, or negative evidence
  0 = no usable citation
"""

from __future__ import annotations


def quay_for_citation(form: str | None, information: str | None, evidence: str | None) -> int:
    if form is None and information is None and evidence is None:
        return 0
    if evidence == "negative" or information == "undetermined" or form == "authored":
        return 1
    if information == "primary" and evidence == "direct" and form in ("original", "derivative"):
        return 3
    if information in ("primary", "secondary"):
        return 2
    return 1


def quay(citations: list[tuple[str | None, str | None, str | None]]) -> int:
    """Best QUAY over all citations of an assertion."""
    return max((quay_for_citation(*c) for c in citations), default=0)
