# Grounded Citations

A citation should identify where the evidence came from, not just that "somewhere in the corpus" a related statement exists. Useful citations normally include a stable document identifier, a chunk boundary, and ideally the line span in the original file.

Line-aware chunking makes citations more actionable. When a result points to lines in a source document, a reviewer can open the file and verify the evidence directly.

Trusted systems also separate retrieval from answering. Retrieval finds evidence. Answering synthesizes from that evidence. If the answer step invents unsupported details, the citations will not match the claims and the mismatch becomes visible.

One practical safeguard is to make answer generation quote or paraphrase only from the retrieved chunks and to always print the evidence bundle alongside the answer.
