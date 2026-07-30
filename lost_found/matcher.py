from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

THRESHOLD = 0.15


def find_matches(target_item, candidates: list):
    """
    target_item: Item (lost or found)
    candidates: list of Item (opposite type, status=open)
    returns list of (item, score) sorted desc, score >= THRESHOLD
    """
    if not candidates:
        return []

    texts = [f"{target_item.title} {target_item.description}"]
    texts += [f"{c.title} {c.description}" for c in candidates]

    vec = TfidfVectorizer(stop_words="english")
    tfidf = vec.fit_transform(texts)

    sims = cosine_similarity(tfidf[0:1], tfidf[1:]).flatten()

    results = [
        (c, float(s)) for c, s in zip(candidates, sims) if s >= THRESHOLD
    ]
    results.sort(key=lambda x: x[1], reverse=True)
    return results
