"""Conservative Kikuyu orthography suggestions; never silently rewrite source records."""
import re
from dataclasses import dataclass


# Initial high-confidence suggestions only. Community reviewers should extend this
# dictionary; each entry is a suggestion, not a declaration that every context is wrong.
SUGGESTIONS: dict[str, str] = {
    "mucii": "mũciĩ",
    "gikuyu": "gĩkũyũ",
    "mundu": "mũndũ",
    "andu": "andũ",
}


@dataclass(frozen=True)
class OrthographySuggestion:
    original: str
    suggested: str
    start: int
    end: int


def _preserve_case(original: str, suggested: str) -> str:
    if original.isupper():
        return suggested.upper()
    if original[:1].isupper():
        return suggested[:1].upper() + suggested[1:]
    return suggested


def suggest_orthography(text: str) -> tuple[str, list[OrthographySuggestion]]:
    """Return a proposed spelling and character offsets without mutating stored text."""
    if not text:
        return text, []

    pattern = re.compile(r"(?<!\w)(" + "|".join(map(re.escape, SUGGESTIONS)) + r")(?!\w)", re.IGNORECASE)
    found: list[OrthographySuggestion] = []

    def replace(match: re.Match[str]) -> str:
        original = match.group(0)
        suggested = _preserve_case(original, SUGGESTIONS[original.lower()])
        found.append(OrthographySuggestion(original, suggested, match.start(), match.end()))
        return suggested

    proposed = pattern.sub(replace, text)
    return proposed, found
