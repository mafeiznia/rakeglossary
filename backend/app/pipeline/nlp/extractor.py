"""Public API for keyword extraction."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.logging import get_logger
from app.pipeline.nlp.candidates import (
    Candidate,
    extract_entities,
    extract_noun_chunks,
    extract_rake,
    extract_yake,
)
from app.pipeline.nlp.filters import deduplicate, is_valid
from app.pipeline.nlp.preprocess import clean_text
from app.pipeline.nlp.scoring import combine

log = get_logger("nlp.extractor")


@dataclass(frozen=True)
class Keyword:
    term: str
    score: float


def extract_keywords(
    text: str,
    top_n: int = 30,
    use_spacy: bool = True,
    use_rake: bool = True,
    use_yake: bool = True,
    use_ner: bool = True,
    extra_stopwords: frozenset[str] = frozenset(),
) -> list[Keyword]:
    """Extract and rank keywords from `text`.

    Args:
        text: Raw input text (will be cleaned internally).
        top_n: Maximum number of keywords to return.
        use_spacy: Include spaCy noun chunks.
        use_rake: Include RAKE keywords.
        use_yake: Include YAKE keywords.
        use_ner: Include spaCy NER entities (proper nouns, places, orgs).
        extra_stopwords: Additional words to exclude (user blacklist).

    Returns:
        Ranked list of `Keyword`, highest score first.
    """
    if not text or not text.strip():
        log.warning("Empty text supplied to extract_keywords.")
        return []

    cleaned = clean_text(text)
    log.info(f"Preprocessed text: {len(cleaned.split())} words.")

    candidates: list[Candidate] = []
    if use_ner:
        candidates += extract_entities(cleaned)
    if use_spacy:
        candidates += extract_noun_chunks(cleaned, extra_stopwords=extra_stopwords)
    if use_rake:
        candidates += extract_rake(cleaned, extra_stopwords=extra_stopwords)
    if use_yake:
        candidates += extract_yake(cleaned)

    log.info(f"Raw candidates collected: {len(candidates)}")

    filtered = [c for c in candidates if is_valid(c, extra_stopwords=extra_stopwords)]
    log.info(f"Candidates after filtering: {len(filtered)}")

    deduped = deduplicate(filtered)
    log.info(f"Candidates after deduplication: {len(deduped)}")

    ranked = combine(deduped)
    top = ranked[:top_n]
    log.info(f"Returning top {len(top)} keywords.")

    return [Keyword(term=term, score=score) for score, term in top]
