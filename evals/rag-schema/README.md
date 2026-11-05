# RAG gold v1

`gold-dataset.schema.json` is the portable JSON Schema 2020-12 contract for
`rag-gold-dataset.v1` envelopes and their closed `rag-gold-case.v1` cases. It embeds
W0's closed `QuestionFrame`, concept vocabulary and `ConfirmedContext`; the tests
check them against the reviewed W0 models. `goldRoute` uses the five executable
W0 routes plus `CLARIFY_OR_SCOPE`, and the dictionary is pinned to `questions-1`.

Run the executable from any working directory, passing **all files in one dataset
version together** so development/sealed overlap is visible:

```bash
/path/to/repository/scripts/lint-rag-gold \
  /protected/dataset/development.json /protected/dataset/sealed.json
```

The executable uses `uv` and its inline Python 3.12/jsonschema dependency metadata.
The existing project environment also supports:

```bash
uv run python scripts/lint-rag-gold tests/evals/rag_gold/fixtures/valid-development.json
```

Exit 0 means every supplied record passed structural and relational checks, its
review hashes match its content, and the supplied files contain no detected split
leakage. Exit 1 means invalid input; invocation errors use argparse's exit 2.
Diagnostics identify files, query IDs, locations and error categories, without
printing questions or source bodies. A single-split invocation cannot establish
isolation from files it was not given.

The linter checks nonempty half-open source/query spans, declared evidence
references, positive evidence/places against allowlists, claim evidence indexes,
revision/hash consistency, unique query IDs, dataset version agreement, two
independent reviewers and completed adjudication. It does not load source bodies,
verify snapshot file bytes, evaluate retrieval or create labels. JSON Schema alone
checks shape; the executable additionally checks these relationships.

The checked-in fixture is synthetic, including its source/corpus hash placeholders
and reviewer records. It is a contract example, not a labeled evaluation dataset.
The invalid fixtures intentionally fail and must not be passed as release inputs.

See [provenance and sealed access rules](../../docs/ai-rag/evaluation-dataset-provenance.md)
for hash algorithms, reviewer workflow, split grouping and release manifests.
