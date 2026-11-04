"""W16 boundary tests: portable schemas, reviewed labels and split isolation."""

from __future__ import annotations

import copy
import hashlib
import json
import runpy
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast, get_args

import pytest
from jsonschema import Draft202012Validator
from pydantic import BaseModel

from onmaru_ai.contracts.models import ConfirmedContext, QuestionFrame, Route

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).parent / "fixtures"
SCRIPT = ROOT / "scripts" / "lint-rag-gold"
SCHEMA = ROOT / "evals" / "rag-schema" / "gold-dataset.schema.json"


def load_fixture(name: str = "valid-development.json") -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((FIXTURES / name).read_text()))


def reseal(case: dict[str, Any]) -> None:
    # Independent test calculation per documented canonical format.
    content = {k: v for k, v in case.items() if k not in {"goldHash", "reviews", "adjudication"}}
    digest = (
        "sha256:"
        + hashlib.sha256(
            json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    )
    case["goldHash"] = digest
    for review in case["reviews"]:
        review["goldHash"] = digest
    case["adjudication"]["goldHash"] = digest


@pytest.fixture
def main() -> Callable[[list[str]], int]:
    def invoke(argv: list[str]) -> int:
        assert SCRIPT.exists(), "W16 gold linter is missing"
        entry = cast(Callable[[list[str]], int], runpy.run_path(str(SCRIPT))["main"])
        return entry(argv)

    return invoke


def schema_validator() -> Draft202012Validator:
    assert SCHEMA.exists(), "W16 portable gold schema is missing"
    schema = json.loads(SCHEMA.read_text())
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def test_schema_accepts_complete_synthetic_case() -> None:
    validator = schema_validator()
    validator.validate(load_fixture())


@pytest.mark.parametrize(
    "field",
    [
        "sources",
        "corpusHash",
        "goldHash",
        "goldRoute",
        "questionDictionaryVersion",
        "reviews",
        "adjudication",
        "goldEvidence",
        "split",
        "tags",
    ],
)
def test_schema_requires_provenance_and_review_fields(
    field: str,
) -> None:
    validator = schema_validator()
    dataset = load_fixture()
    del dataset["cases"][0][field]
    assert list(validator.iter_errors(dataset))


@pytest.mark.parametrize(
    "path",
    [
        [],
        ["cases", 0],
        ["cases", 0, "sources", 0],
        ["cases", 0, "goldEvidence", 0],
        ["cases", 0, "reviews", 0],
        ["cases", 0, "adjudication"],
        ["cases", 0, "goldQuestionFrame"],
    ],
)
def test_schema_closes_every_object(
    path: list[str | int],
) -> None:
    validator = schema_validator()
    dataset = load_fixture()
    value: Any = dataset
    for key in path:
        value = value[key]
    value["rawConversation"] = "must never enter gold records"
    assert list(validator.iter_errors(dataset))


def test_schema_reuses_w0_frame_context_and_route() -> None:
    validator = schema_validator()
    schema = cast(dict[str, Any], validator.schema)
    models: list[tuple[str, type[BaseModel]]] = [
        ("QuestionFrame", QuestionFrame),
        ("ConfirmedContext", ConfirmedContext),
    ]
    for name, model in models:
        generated = model.model_json_schema(by_alias=True)
        generated.pop("$defs", None)
        assert schema["$defs"][name] == generated
    route_values = schema["$defs"]["GoldCase"]["properties"]["goldRoute"]["enum"]
    assert set(route_values) == set(get_args(Route))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("goldRoute", "AUTO"),
        ("questionDictionaryVersion", "questions-unregistered"),
        ("split", "test"),
        ("corpusHash", "bad-hash"),
        ("answerable", 1),
        ("tags", ["UNKNOWN"]),
        ("reviews", []),
        ("schemaVersion", "rag-gold-case.v2"),
    ],
)
def test_schema_rejects_unknown_or_malformed_values(
    field: str,
    value: Any,
) -> None:
    validator = schema_validator()
    dataset = load_fixture()
    dataset["cases"][0][field] = value
    assert list(validator.iter_errors(dataset))


@pytest.mark.parametrize(
    ("name", "expected", "diagnostic"),
    [
        ("valid-development.json", 0, "OK"),
        ("invalid-source-hash.json", 1, "SCHEMA"),
        ("invalid-split-leakage.json", 1, "LEAKAGE"),
    ],
)
def test_checked_in_fixtures_have_expected_cli_result(
    main: Callable[[list[str]], int],
    capsys: pytest.CaptureFixture[str],
    name: str,
    expected: int,
    diagnostic: str,
) -> None:
    assert main([str(FIXTURES / name)]) == expected
    captured = capsys.readouterr()
    assert diagnostic in captured.out + captured.err


@pytest.mark.parametrize(
    ("mutation", "diagnostic"),
    [
        ("duplicate-reviewer", "REVIEW"),
        ("stale-review", "REVIEW"),
        ("pending-adjudication", "REVIEW"),
        ("unresolved-disagreement", "REVIEW"),
        ("rejected-consensus", "REVIEW"),
        ("resolved-without-third-reviewer", "REVIEW"),
        ("reversed-offset", "OFFSET"),
        ("out-of-source-offset", "OFFSET"),
        ("unknown-evidence-source", "REFERENCE"),
        ("source-hash-conflict", "PROVENANCE"),
        ("preserved-span-mismatch", "OFFSET"),
        ("unknown-claim-evidence", "REFERENCE"),
        ("allowed-forbidden-overlap", "REFERENCE"),
        ("stale-gold-hash", "HASH"),
        ("dataset-version-mismatch", "VERSION"),
        ("duplicate-query-id", "DUPLICATE"),
        ("answerable-without-evidence", "REFERENCE"),
    ],
)
def test_linter_rejects_semantically_invalid_gold(
    main: Callable[[list[str]], int],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    mutation: str,
    diagnostic: str,
) -> None:
    dataset = load_fixture()
    case = dataset["cases"][0]
    match mutation:
        case "duplicate-reviewer":
            case["reviews"][1]["reviewerId"] = "reviewer-1"
            case["reviews"][1]["rationale"] = "Different rationale from the same person."
        case "stale-review":
            case["reviews"][0]["goldHash"] = "sha256:" + "c" * 64
        case "pending-adjudication":
            case["adjudication"]["status"] = "PENDING"
        case "unresolved-disagreement":
            case["reviews"][1]["decision"] = "REJECT"
        case "rejected-consensus":
            for review in case["reviews"]:
                review["decision"] = "REJECT"
        case "resolved-without-third-reviewer":
            case["reviews"][1]["decision"] = "REJECT"
            case["adjudication"].update(status="RESOLVED", adjudicatorId="reviewer-1")
        case "reversed-offset":
            case["goldEvidence"][0]["endOffset"] = 0
        case "out-of-source-offset":
            case["goldEvidence"][0]["endOffset"] = 21
        case "unknown-evidence-source":
            case["goldEvidence"][0]["sourceRevision"] = "unlisted-revision"
        case "source-hash-conflict":
            source = copy.deepcopy(case["sources"][0])
            source["sourceHash"] = "sha256:" + "c" * 64
            case["sources"].append(source)
        case "preserved-span-mismatch":
            case["preserveSpans"][0]["text"] = "다른 표현"
        case "unknown-claim-evidence":
            case["minimumClaims"][0]["evidenceIndexes"] = [2]
        case "allowed-forbidden-overlap":
            case["forbiddenPlaceIds"] = ["place-1"]
        case "stale-gold-hash":
            case["safeQuery"] = "수정된 질문"
        case "dataset-version-mismatch":
            case["datasetVersion"] = "synthetic-2"
        case "duplicate-query-id":
            dataset["cases"].append(copy.deepcopy(case))
        case "answerable-without-evidence":
            case["goldEvidence"] = []
            case["minimumClaims"] = []
    if mutation not in {"stale-gold-hash", "stale-review"}:
        reseal(case)
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps(dataset, ensure_ascii=False))
    assert main([str(path)]) == 1
    captured = capsys.readouterr()
    assert diagnostic in captured.err
    assert "synthetic-q1" in captured.err
    assert case["safeQuery"] not in captured.err  # diagnostics never print question content


@pytest.mark.parametrize("identity", ["same-place", "same-source-revision", "distinct"])
def test_leakage_is_checked_across_files_and_question_variants(
    main: Callable[[list[str]], int],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    identity: str,
) -> None:
    dataset = load_fixture()
    second = copy.deepcopy(dataset)
    case = second["cases"][0]
    case.update(
        queryId="synthetic-q2", split="sealed", safeQuery="다른 말투의 질문", preserveSpans=[]
    )
    if identity != "same-place":
        case["sources"][0]["placeId"] = "place-2"
        case["allowedPlaceIds"] = ["place-2"]
        case["placeGrades"][0]["placeId"] = "place-2"
        case["goldEvidence"][0]["placeId"] = "place-2"
    if identity != "same-source-revision":
        case["sources"][0].update(sourceId="source-2", sourceRevision="revision-2")
        case["goldEvidence"][0].update(sourceId="source-2", sourceRevision="revision-2")
    reseal(case)
    path = tmp_path / "sealed.json"
    path.write_text(json.dumps(second, ensure_ascii=False))
    result = main([str(FIXTURES / "valid-development.json"), str(path)])
    captured = capsys.readouterr()
    assert result == (0 if identity == "distinct" else 1)
    if identity != "distinct":
        assert "LEAKAGE" in captured.err


def test_resolved_disagreement_and_same_split_variants_are_accepted(
    main: Callable[[list[str]], int],
    tmp_path: Path,
) -> None:
    dataset = load_fixture()
    case = copy.deepcopy(dataset["cases"][0])
    case["queryId"] = "synthetic-q2"
    case["reviews"][1]["decision"] = "REJECT"
    case["adjudication"].update(status="RESOLVED", adjudicatorId="reviewer-3")
    reseal(case)
    dataset["cases"].append(case)
    path = tmp_path / "resolved.json"
    path.write_text(json.dumps(dataset, ensure_ascii=False))
    assert main([str(path)]) == 0


@pytest.mark.parametrize("content", ["{", "[]", "null", '{"schemaVersion":"unknown"}'])
def test_malformed_inputs_fail_without_tracebacks(
    main: Callable[[list[str]], int],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    content: str,
) -> None:
    path = tmp_path / "invalid.json"
    path.write_text(content)
    assert main([str(path)]) == 1
    assert "Traceback" not in capsys.readouterr().err


def test_executable_works_outside_repository(tmp_path: Path) -> None:
    assert SCRIPT.exists(), "W16 executable is missing"
    result = subprocess.run(
        [str(SCRIPT), str(FIXTURES / "valid-development.json")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout


@pytest.mark.parametrize(
    "route",
    ["SQL_ONLY", "LEXICAL_ONLY", "DENSE_ONLY", "HYBRID", "SQL_PLUS_RETRIEVAL", "CLARIFY_OR_SCOPE"],
)
def test_route_controls_semantic_query_presence(route: str) -> None:
    validator = schema_validator()
    dataset = load_fixture()
    case = dataset["cases"][0]
    case["goldRoute"] = route
    retrieval = route not in {"SQL_ONLY", "CLARIFY_OR_SCOPE"}
    case["semanticQuery"]["expected"] = "한적한 한옥" if retrieval else None
    assert not list(validator.iter_errors(dataset))
    case["semanticQuery"]["expected"] = None if retrieval else "한적한 한옥"
    assert list(validator.iter_errors(dataset))


def test_unanswerable_source_free_case_is_supported(
    main: Callable[[list[str]], int],
    tmp_path: Path,
) -> None:
    dataset = load_fixture()
    case = dataset["cases"][0]
    case.update(
        answerable=False,
        sources=[],
        goldEvidence=[],
        minimumClaims=[],
        placeGrades=[],
        allowedPlaceIds=[],
        goldRoute="CLARIFY_OR_SCOPE",
    )
    case["semanticQuery"]["expected"] = None
    reseal(case)
    path = tmp_path / "unanswerable.json"
    path.write_text(json.dumps(dataset, ensure_ascii=False))
    assert main([str(path)]) == 0


def test_missing_file_fails_without_traceback(
    main: Callable[[list[str]], int],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main([str(tmp_path / "missing.json")]) == 1
    captured = capsys.readouterr()
    assert "INPUT" in captured.err
    assert "Traceback" not in captured.err
