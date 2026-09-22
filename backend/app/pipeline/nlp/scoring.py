"""Combine scores from multiple sources into a single ranked list."""

from __future__ import annotations

from collections import defaultdict

from app.pipeline.nlp.candidates import Candidate
from app.pipeline.nlp.filters import normalize

# NER terms are the highest-value (proper nouns, characters, places),
# followed by noun chunks, then RAKE, then YAKE.
_SOURCE_WEIGHTS = {
    "ner": 0.35,
    "spacy": 0.25,
    "rake": 0.25,
    "yake": 0.15,
}


def _normalize_scores(
    candidates: list[Candidate],
) -> dict[str, tuple[float, float]]:
    """Min-max normalize raw scores per source to [0, 1]."""
    by_source: dict[str, list[float]] = defaultdict(list)
    for c in candidates:
        by_source[c.source].append(c.raw_score)

    ranges: dict[str, tuple[float, float]] = {}
    for src, scores in by_source.items():
        lo, hi = min(scores), max(scores)
        ranges[src] = (lo, hi if hi > lo else lo + 1.0)
    return ranges


def combine(candidates: list[Candidate]) -> list[tuple[float, str]]:
    """Return a ranked list of (score, term), highest score first."""
    if not candidates:
        return []

    ranges = _normalize_scores(candidates)
    aggregated: dict[str, float] = defaultdict(float)
    canonical: dict[str, str] = {}
    sources: dict[str, set[str]] = defaultdict(set)

    for c in candidates:
        key = normalize(c.term).lower()
        canonical.setdefault(key, normalize(c.term))
        sources[key].add(c.source)

        lo, hi = ranges[c.source]
        norm = (c.raw_score - lo) / (hi - lo) if hi > lo else 0.5
        aggregated[key] += _SOURCE_WEIGHTS.get(c.source, 0.1) * norm

    # Small bonus for terms discovered by multiple sources (consensus)
    for key in aggregated:
        n_sources = len(sources[key])
        if n_sources > 1:
            aggregated[key] *= 1.0 + 0.1 * (n_sources - 1)

    ranked = sorted(aggregated.items(), key=lambda kv: kv[1], reverse=True)
    return [(score, canonical[key]) for key, score in ranked]
