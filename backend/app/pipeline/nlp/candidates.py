"""Candidate keyword extraction using spaCy (noun chunks + NER) + RAKE + YAKE."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from rake_nltk import Rake

from app.core.logging import get_logger
from app.pipeline.nlp.stopwords import english_stopwords

log = get_logger("nlp.candidates")


@dataclass(frozen=True)
class Candidate:
    """A single candidate term with its raw source and raw score."""

    term: str
    source: str  # "ner" | "spacy" | "rake" | "yake"
    raw_score: float


# ---------------------------------------------------------------------------
# spaCy loader
# ---------------------------------------------------------------------------

_CONTENT_POS = {"NOUN", "PROPN", "ADJ"}
_BAD_BOUNDARY_POS = {
    "ADP",
    "PRON",
    "DET",
    "CCONJ",
    "SCONJ",
    "PART",
    "VERB",
    "AUX",
    "PUNCT",
    "SYM",
    "NUM",
}

# Named entity types that make sense as glossary terms
_INTERESTING_ENTS: dict[str, float] = {
    "PERSON": 1.00,
    "GPE": 0.95,  # geopolitical entity (countries, cities)
    "LOC": 0.95,  # non-GPE locations (mountains, seas)
    "ORG": 0.90,  # organizations, companies, institutions
    "PRODUCT": 0.90,  # products, objects
    "EVENT": 0.85,  # named events (World War II)
    "WORK_OF_ART": 0.85,  # books, films, songs
    "FAC": 0.85,  # facilities (airports, bridges)
    "NORP": 0.80,  # nationalities, religious/political groups
    "LAW": 0.75,
}


@lru_cache(maxsize=1)
def _load_spacy():
    """Load the small English spaCy model once."""
    import spacy

    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        log.warning(
            "spaCy model 'en_core_web_sm' not found. "
            "Run: python -m spacy download en_core_web_sm"
        )
        return None


# ---------------------------------------------------------------------------
# NER — named entities (people, places, orgs, etc.)
# ---------------------------------------------------------------------------


def extract_entities(
    text: str,
    max_entities: int = 2000,
) -> list[Candidate]:
    """Extract named entities using spaCy's NER.

    Rejects entities that contain a verb (e.g., "Azami imagined Yumiko"),
    since those are phrases, not proper names.
    """
    nlp = _load_spacy()
    if nlp is None:
        return []

    doc = nlp(text[:1_000_000])
    stop = english_stopwords()
    results: list[Candidate] = []
    seen: set[str] = set()

    for ent in doc.ents:
        boost = _INTERESTING_ENTS.get(ent.label_)
        if boost is None:
            continue

        # Reject entities containing a verb or auxiliary
        has_verb = any(tok.pos_ in {"VERB", "AUX"} for tok in ent)
        if has_verb:
            continue

        term = ent.text.strip().strip(" \t.,;:!?\"'`()[]{}")
        if not term or len(term) < 2:
            continue

        # Reject if every word is a stopword
        words = [w for w in term.lower().split() if w not in stop]
        if not words:
            continue

        # Reject if term has more than 4 words (likely a phrase)
        if len(term.split()) > 4:
            continue

        key = term.lower()
        if key in seen:
            continue
        seen.add(key)

        n_words = len(term.split())
        score = boost * (1.0 + 0.05 * min(n_words - 1, 3))
        results.append(Candidate(term=term, source="ner", raw_score=score))

        if len(results) >= max_entities:
            break

    log.info(f"NER extracted {len(results)} named entities.")
    return results


# ---------------------------------------------------------------------------
# spaCy noun chunks (general terms)
# ---------------------------------------------------------------------------


def extract_noun_chunks(
    text: str,
    max_chunks: int = 5000,
    extra_stopwords: frozenset[str] = frozenset(),
) -> list[Candidate]:
    """Extract meaningful noun phrases using spaCy with POS filtering."""
    nlp = _load_spacy()
    if nlp is None:
        return []

    doc = nlp(text[:1_000_000])
    stop = english_stopwords() | extra_stopwords
    results: list[Candidate] = []
    seen: set[str] = set()

    for chunk in doc.noun_chunks:
        tokens = [t for t in chunk if t.pos_ != "DET" and not t.is_punct]
        if not tokens:
            continue
        if not any(t.pos_ in _CONTENT_POS for t in tokens):
            continue
        if tokens[0].pos_ in _BAD_BOUNDARY_POS:
            continue
        if tokens[-1].pos_ in _BAD_BOUNDARY_POS:
            continue

        term = " ".join(t.text for t in tokens).strip()
        term = term.strip(" \t.,;:!?\"'`()[]{}")
        if not term or len(term) < 2:
            continue

        words = [w for w in term.lower().split() if w not in stop]
        if not words:
            continue

        key = term.lower()
        if key in seen:
            continue
        seen.add(key)

        n_words = len(term.split())
        weight = max(0.4, 1.0 - 0.15 * (n_words - 1))
        results.append(Candidate(term=term, source="spacy", raw_score=weight))

        if len(results) >= max_chunks:
            break
    return results


# ---------------------------------------------------------------------------
# RAKE
# ---------------------------------------------------------------------------


def extract_rake(
    text: str,
    max_phrases: int = 2000,
    extra_stopwords: frozenset[str] = frozenset(),
) -> list[Candidate]:
    """Extract keywords using RAKE with our combined stopword set."""
    rake = Rake(
        stopwords=set(english_stopwords()) | set(extra_stopwords),
        min_length=1,
        max_length=3,
        include_repeated_phrases=False,
    )
    rake.extract_keywords_from_text(text[:1_000_000])
    ranked = rake.get_ranked_phrases_with_scores()[:max_phrases]
    return [
        Candidate(term=phrase, source="rake", raw_score=float(score)) for score, phrase in ranked
    ]


# ---------------------------------------------------------------------------
# YAKE
# ---------------------------------------------------------------------------


def extract_yake(text: str, max_phrases: int = 500) -> list[Candidate]:
    """Extract keywords using YAKE (unsupervised, language-independent)."""
    try:
        import yake
    except ImportError:
        log.debug("YAKE not installed; skipping.")
        return []

    extractor = yake.KeywordExtractor(
        lan="en",
        n=3,
        dedupLim=0.85,
        top=max_phrases,
    )
    keywords = extractor.extract_keywords(text[:1_000_000])
    return [
        Candidate(term=kw, source="yake", raw_score=1.0 / (1.0 + score)) for kw, score in keywords
    ]
