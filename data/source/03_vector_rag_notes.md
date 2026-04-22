# Vector RAG Notes

In retrieval-augmented generation, a vector index is often used to recall chunks that are semantically related to a query. The index stores a vector for each chunk, and search ranks candidates by similarity between the query vector and chunk vectors.

Production systems often use learned embeddings, but the core idea is broader than any one model. What matters is that the vectors are computed consistently, stored in an inspectable index, and used to recall supporting evidence before answer generation.

Dense retrieval is helpful when user wording drifts away from the source wording. A passage about "evidence-backed answers" might still be relevant to a query about "trustworthy responses" even if the exact terms differ.

RAG becomes more trustworthy when the generation layer keeps citations attached to the retrieved chunks. If the answer cannot point to supporting passages, operators cannot easily audit whether the model stayed within the evidence.
