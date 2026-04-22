# BM25 Notes

BM25 is a ranking function commonly used in full-text search engines. It estimates how relevant a document is to a query by balancing term frequency, inverse document frequency, and document length normalization.

Because BM25 works directly over an inverted index, it is fast and explainable. If a result ranks highly, you can usually trace that to the presence of important query terms in a relatively focused document.

SQLite `fts5` includes a built-in `bm25()` ranking function. That gives a practical way to ship a real BM25-backed search system in a single local file without adding external services.

BM25 still has limits. It does not understand paraphrases, latent topics, or related terminology unless the words overlap. A query for "confidence in sources" may miss passages that only say "grounded citations" or "evidence-backed retrieval."
