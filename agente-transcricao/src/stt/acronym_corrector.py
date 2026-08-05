"""Corrects mis-transcribed acronyms in a transcription.

Whisper frequently garbles domain acronyms it has never seen ("IPOF" transcribed
as "HIPOF", "GU1" as "GUM"). The user supplies the acronyms that were spoken in
the meeting and this module rewrites the close-enough variants back to the
canonical spelling, before the transcription reaches Agents 2 and 3.

Only the acronym token itself is rewritten; the supplied meaning is not inserted
into the text (it is used elsewhere as context for the LLM).
"""
from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

# Minimum similarity for a token to be considered a garbled spelling of an acronym.
# 0.82 accepts HIPOF->IPOF (0.89) and rejects unrelated short words.
_DEFAULT_THRESHOLD = 0.82

# Tokens shorter than this are too ambiguous to fuzzy-match safely (only exact,
# case-insensitive matches are corrected for them).
_MIN_FUZZY_LEN = 4

# Words that must never be rewritten, however close they look to an acronym.
_PROTECTED = {
    "que", "para", "com", "uma", "por", "mais", "como", "isso", "essa", "esse",
    "não", "nao", "sim", "então", "entao", "porque", "quando", "onde", "qual",
    "todo", "toda", "ser", "estar", "tem", "ter", "faz", "fazer", "vai",
}


class Acronym:
    """One user-supplied acronym: the canonical spelling and its meaning."""

    def __init__(self, sigla: str, significado: str = ""):
        self.sigla = sigla.strip()
        self.significado = significado.strip()

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Acronym({self.sigla!r}, {self.significado!r})"


def parse_acronyms(raw: str) -> list[Acronym]:
    """Parses the GUI/CLI acronym table into Acronym objects.

    Accepts one entry per line, acronym and meaning separated by '=', ':', '-'
    or a tab. The meaning is optional:

        IPOF = Índice de Programação Orçamentária e Financeira
        SLC: Sistema de Liquidação Centralizada
        GU1
    """
    acronyms: list[Acronym] = []
    seen: set[str] = set()
    for line in (raw or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = re.split(r"\s*[=:\t]\s*|\s+[-–]\s+", line, maxsplit=1)
        sigla = parts[0].strip()
        significado = parts[1].strip() if len(parts) > 1 else ""
        if not sigla or sigla.lower() in seen:
            continue
        seen.add(sigla.lower())
        acronyms.append(Acronym(sigla, significado))
    return acronyms


def _normalize(token: str) -> str:
    """Casefold and strip accents, so 'Hipóf' and 'HIPOF' compare equal."""
    stripped = unicodedata.normalize("NFKD", token).encode("ascii", "ignore").decode("ascii")
    return stripped.lower()


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _best_match(token: str, acronyms: list[Acronym], threshold: float) -> Acronym | None:
    """Returns the acronym `token` is most likely a garbled spelling of, if any."""
    norm_token = _normalize(token)
    if not norm_token or norm_token in _PROTECTED:
        return None

    best: Acronym | None = None
    best_score = 0.0
    for acronym in acronyms:
        norm_sigla = _normalize(acronym.sigla)
        if not norm_sigla:
            continue
        if norm_token == norm_sigla:
            # Exact (case/accent-insensitive) hit: fix casing only.
            return acronym if token != acronym.sigla else None
        # Fuzzy matching is only safe for reasonably long tokens.
        if len(norm_sigla) < _MIN_FUZZY_LEN or len(norm_token) < _MIN_FUZZY_LEN:
            continue
        # Length must be comparable — avoids matching a long word to a short acronym.
        if abs(len(norm_token) - len(norm_sigla)) > 2:
            continue
        score = _similarity(norm_token, norm_sigla)
        if score >= threshold and score > best_score:
            best, best_score = acronym, score
    return best


def correct_transcription(
    text: str,
    acronyms: list[Acronym],
    threshold: float = _DEFAULT_THRESHOLD,
) -> tuple[str, dict[str, int]]:
    """Rewrites garbled acronym spellings in `text` to their canonical form.

    Returns the corrected text and a {"WRONG -> RIGHT": occurrences} report,
    so the caller can log exactly what was changed (traceability).
    """
    if not text or not acronyms:
        return text, {}

    report: dict[str, int] = {}

    def replace(match: re.Match) -> str:
        token = match.group(0)
        acronym = _best_match(token, acronyms, threshold)
        if acronym is None:
            return token
        key = f"{token} -> {acronym.sigla}"
        report[key] = report.get(key, 0) + 1
        return acronym.sigla

    # Word-ish tokens only (letters/digits), so punctuation and spacing survive.
    corrected = re.sub(r"\b[\wÀ-ÿ]+\b", replace, text, flags=re.UNICODE)
    return corrected, report


def acronyms_context(acronyms: list[Acronym]) -> str:
    """Formats the acronyms as plain-text context for the LLM prompts.

    Returns "" when nothing was supplied, so prompts can omit the block entirely.
    """
    lines = [
        f"- {a.sigla}: {a.significado}" if a.significado else f"- {a.sigla}"
        for a in acronyms
    ]
    return "\n".join(lines)
