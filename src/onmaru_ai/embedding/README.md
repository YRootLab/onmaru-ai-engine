# Embedding adapter boundary

W4 pins `intfloat/multilingual-e5-small` commit
`614241f622f53c4eeff9890bdc4f31cfecc418b3` as the first 384-dimensional profile.
The service applies `passage: ` and `query: ` itself, requires unit-normalized finite output,
and rejects a backend whose model ID, commit, or dimension differs.

The model runtime is injected through `EmbeddingBackend`; this module does not download a model
or contact a remote provider. Packaging the pinned artifact and recording its license review remain
deployment work. `EmbeddingWorkGate` provides the process-local online/batch boundary. A deployment
with more than one process must use a shared admission mechanism before offline indexing.

`VectorSearcher` performs exact cosine search through a `CorpusSnapshot`, so revision, profile,
dictionary version, and revocation watermark stay attached to every candidate. It is dense-only;
BM25, RRF, and HNSW are outside W4.
