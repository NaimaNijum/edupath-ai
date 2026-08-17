from __future__ import annotations

import re

# Small stopword list -- just enough to strip common sentence filler out of a
# free-text student request so keyword search has a chance of matching
# database rows. Not meant to be linguistically exhaustive.
_STOPWORDS = {
    "a", "an", "the", "i", "want", "in", "for", "to", "of", "and", "with",
    "my", "is", "are", "on", "at", "this", "that", "fully", "funded",
    "looking", "please", "would", "like", "me", "find", "search", "help",
}
_WORD_RE = re.compile(r"[a-zA-Z]{3,}")


def extract_keywords(query: str) -> list[str]:
    """Split a free-text query into meaningful keywords for an OR-matched
    ILIKE search. Falls back to the raw (stripped) query if nothing survives
    stopword filtering, so a short/unusual query still searches on something."""
    words = _WORD_RE.findall(query.lower())
    keywords = [word for word in words if word not in _STOPWORDS]
    if keywords:
        return list(dict.fromkeys(keywords))  # de-dupe, preserve order
    stripped = query.strip()
    return [stripped] if stripped else []
