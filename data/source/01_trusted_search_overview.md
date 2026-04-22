# Trusted Search Overview

Trusted search should prefer evidence over eloquence. A retrieval system is more reliable when it cites the exact source chunk that supports each claim and when those citations are tied to stable indexes instead of ad hoc prompt stuffing.

BM25 is strong at exact term matching. It rewards documents that contain the words a user typed, especially rare terms. That makes it a good fit for version numbers, identifiers, product names, and questions with precise vocabulary.

Vector retrieval covers a different failure mode. Users often ask the right question with the wrong words. A vector index can still connect related concepts when the query vocabulary does not literally overlap with the best passage.

The safest practical design is hybrid retrieval. First collect candidates from both lexical and vector indexes. Then merge the candidates, deduplicate them by chunk id, and expose the evidence with citations so a downstream answer generator can stay grounded.

Grounding is not just about retrieval. The answer stage should preserve which chunks were used, avoid claims that are not supported by retrieved evidence, and let operators inspect the exact files and line ranges behind every answer.
