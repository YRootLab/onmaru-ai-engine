# Evaluation artifacts

## Journey comparison CLI

The CLI input schema is [`input.schema.json`](input.schema.json), version `1.2`. Each case pins the exact `gold.query`, optional canonical `gold.regionCode`, and ordered `gold.candidateRefs` snapshot (maximum 12), followed by the place relevance grades, `supportedEvidence`, `allowedRefs`, and `expectedOutcome`. The document also pins `candidatePolicy`, `corpusRevision`, full OCI `imageDigest`, `embeddingProfile`, code/prompt/ranking versions, and thresholds. Baseline and RAG runs can use different image digests and implementation versions; each report records its own provenance and the comparison embeds the baseline digest. Comparison compatibility requires matching gold fingerprint, policy, corpus revision, embedding profile, and thresholds. The generated report contract is [`report.schema.json`](report.schema.json).

Run the deterministic scorer and compare its report with the baseline report:

```bash
uv run python scripts/run-ai-evals \
  --input /protected/evaluation/rag-run.json \
  --output /protected/results/rag-report.json \
  --compare /protected/results/baseline-report.json
```

The checked-in [`journey-eval-contract-fixture-v1.json`](journey-eval-contract-fixture-v1.json) is a four-case synthetic contract fixture for unit tests.

The verified 100-case dataset for operational RAG activation is [`journey-eval-gold-100-v1.json`](journey-eval-gold-100-v1.json) (along with [`journey-eval-baseline-100-v1.json`](journey-eval-baseline-100-v1.json)). It covers 10 representative travel themes across multiple Korean regions with variations, evaluating retrieval recall, NDCG@3, claim support, latency, and cost deltas. Its evaluation outputs are stored in [`rag-report.json`](rag-report.json) and [`baseline-report.json`](baseline-report.json), which pass all thresholds and demonstrate positive retrieval recall (+0.167) and NDCG@3 (+0.163) gain over the baseline.

## RAG gold authoring contract

[`rag-schema/`](rag-schema/README.md) describes the separate reviewed RAG source/evidence dataset, cross-split leakage linter, hash rules, and sealed-set controls. Its checked-in fixtures are also synthetic. A real activation dataset must be authored from approved source snapshots, independently reviewed, adjudicated, frozen, and kept out of public repository history when it contains sealed cases.

## Release evidence

[`ai-rag/release-evidence/`](../docs/ai-rag/release-evidence/README.md) records infrastructure and performance evidence. Generated synthetic load estimates are labeled `SIMULATED_REFERENCE_ONLY`; they never count as measured memory or load results and cannot approve a release.
