from onmaru_ai.corpus.batch_ingest import IngestItem, build_corpus_bundle
from onmaru_ai.corpus.categories import APPROVED_CANONICAL_CATEGORIES, is_approved_category


def test_approved_categories_count_and_filtering() -> None:
    assert len(APPROVED_CANONICAL_CATEGORIES) == 12
    assert is_approved_category("HANOK")
    assert is_approved_category("hanok_cafe")
    assert is_approved_category("TRADITIONAL_MARKET")
    assert not is_approved_category("UNKNOWN_RANDOM_CATEGORY")
    assert not is_approved_category("")


def test_build_corpus_bundle_filters_unapproved_categories() -> None:
    items = [
        IngestItem(
            place_id="p1",
            title="경복궁",
            body="조선 왕조의 법궁으로 서울 종로구에 위치한 대표 궁궐입니다.",
            region_code="SEOUL",
            category_code="HISTORIC_SITE",
        ),
        IngestItem(
            place_id="p2",
            title="미승인 장소",
            body="카테고리가 올바르지 않은 장소입니다.",
            region_code="SEOUL",
            category_code="CASINO_OR_OTHER",
        ),
        IngestItem(
            place_id="p3",
            title="전주 한옥마을 다원",
            body="전통 한옥에서 즐기는 전통차와 다도 체험 공간입니다.",
            region_code="JEONJU",
            category_code="HANOK_CAFE",
        ),
    ]

    result, revision, docs, chunks, embeddings = build_corpus_bundle(
        revision_id="rev-test-1",
        items=items,
        embedding_service=None,
    )

    assert result.total_input == 3
    assert result.accepted_documents == 2
    assert result.filtered_out_categories == 1
    assert len(docs) == 2
    assert len(chunks) >= 2
    assert revision.chunk_count == len(chunks)
    assert {d.category_code for d in docs} == {"HISTORIC_SITE", "HANOK_CAFE"}


def test_build_corpus_bundle_normalizes_html_and_batches_embeddings() -> None:
    from onmaru_ai.embedding import GEMINI_EMBEDDING_384, EmbeddingService
    from onmaru_ai.storage.postgres import _validate

    class FakeGeminiBackend:
        model_id = GEMINI_EMBEDDING_384.model_id
        model_commit = GEMINI_EMBEDDING_384.model_commit
        dimensions = 384

        def __init__(self) -> None:
            self.batches: list[int] = []

        def encode(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
            self.batches.append(len(texts))
            return tuple((1.0,) + (0.0,) * 383 for _ in texts)

    backend = FakeGeminiBackend()
    svc = EmbeddingService(backend, profile=GEMINI_EMBEDDING_384, max_batch_size=2)
    items = [
        IngestItem(
            place_id=f"p-tourapi-{i}",
            title=f"경주 유적 {i}",
            body=f"<p>경상북도 경주시 유적 {i}&nbsp;&nbsp;소개입니다.</p><br>방문해보세요.  ",
            region_code="KR-47",
            category_code="HISTORIC_SITE",
            source_id=f"p-tourapi-{i}",
        )
        for i in range(3)
    ]

    result, revision, docs, chunks, embeddings = build_corpus_bundle(
        revision_id="rev-test-html",
        items=items,
        embedding_service=svc,
        embed_batch_size=2,
    )

    assert result.accepted_documents == 3
    assert result.total_embeddings == 3
    assert revision.embedding_profile_id == GEMINI_EMBEDDING_384.profile_id
    assert backend.batches == [2, 1]
    assert all("<p>" not in d.normalized_text for d in docs)
    # Must pass PostgresCorpusStore._validate() invariants cleanly
    _validate(revision, docs, chunks, embeddings)

