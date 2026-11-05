# RAG gold 평가셋의 provenance와 봉인 접근 규칙

W16 / [Issue #11](https://github.com/YRootLab/onmaru-ai-engine/issues/11)은
[평가 설계](evaluation-and-environment-tests.md)의 데이터 계약과 검수 도구를
제공한다. 실제 개발 200·봉인 100문항 작성은 W22, replay·품질 gate 실행은 W17의
작업이다. 저장소의 소규모 fixture와 그 안의 검수자는 합성 예시이며 실제 이중 검수
완료나 출시 품질을 의미하지 않는다.

## 버전과 기록 형식

정본은 [`gold-dataset.schema.json`](../../evals/rag-schema/gold-dataset.schema.json)의
JSON Schema 2020-12 계약이다. dataset envelope는 `schemaVersion`, `datasetVersion`,
`cases`를 가지며 모든 case는 같은 `datasetVersion`을 명시한다. 서로 다른 버전은 한
lint 호출에 섞지 않는다. v1은 모든 object의 미등록 필드를 거절한다. 필드·enum·질문
사전의 변경은 schema와 dataset의 새 버전으로 관리하고 과거 파일은 덮어쓰지 않는다.

| 기록 | 고정하는 내용 |
|---|---|
| Case 식별 | `queryId`, `datasetVersion`, `schemaVersion`, `split` (`development` / `sealed`) |
| 원천과 corpus | `corpusRevision`, `corpusHash`, `sources[]`의 canonical `placeId`, `sourceId`, `sourceRevision`, `sourceHash`, `sourceLength` |
| 질문 계약 | 공개 자료로 만든 `safeQuery`, W0 `ConfirmedContext` 형태의 `threadContextFixture` 또는 null, `goldRoute`, `goldQuestionFrame`, `questionDictionaryVersion=questions-1` |
| 표현 보존 | `preserveSpans[]`의 `startOffset`, `endOffset`, `text`; `semanticQuery.expected` 또는 null과 `forbidden[]` |
| 정답 라벨 | 허용/금지 장소, grade 0/1/2 `placeGrades`, `goldEvidence`의 place/chunk/source/revision/offset/grade, `answerable`, 근거 인덱스를 참조하는 `minimumClaims` |
| 검수 | `goldHash`, 서로 다른 두 `reviews[]`의 reviewer ID·ACCEPT/REJECT·검토 hash·사유, `adjudication`의 상태·판정·조정자·hash·사유 |
| 별도 분석 | `tags`: 부정, 다턴, 동명이인, 철회, 주입, 개인정보, 근거 부족, 범위 밖, 확인 질문, 복합, 합성 여부 |

다섯 실행 route와 실행 전 보류용 `CLARIFY_OR_SCOPE`는 W0의 고정 enum을 따른다.
확인 질문·주입 등의 부정 사례도 원래 기대 route와 차단 태그를 함께 가질 수 있다.
`threadContextFixture`에는 원문 대화가 아닌 확정된 공개 상태만 넣는다.
`semanticQuery.expected`는 SQL/확인 질문 등 검색이 없는 경우 null로 기록한다.
태그는 겹쳐 부여할 수 있으며 route별 표본 수와 별도로 집계한다.

모든 offset은 고정한 텍스트의 **Unicode code point 기준, 0부터 시작하는 반개구간
[startOffset, endOffset)**이다. UTF-8 byte/UTF-16 code unit 인덱스와 섞지 않는다.
`sourceLength`는 같은 텍스트의 code point 길이다. 원문을 정규화하거나 줄바꿈을
바꾼 뒤 과거 offset을 재사용하지 않는다. SQL_ONLY도 정형 공개 필드의 고정된 텍스트
snapshot에 대한 gold 근거를 기록할 수 있으며 런타임 본문 검색을 요구하지 않는다.
청킹이 바뀌면 chunk ID와 별도로 이 source revision/offset으로 근거 동치를 판단한다.

## Hash와 재현 가능한 provenance

Hash는 모두 소문자 `sha256:` + 64자리 hex 형식이다. 서로 다른 대상을 구분한다.

- `sourceHash`: offset이 가리키는 승인된 원천 텍스트 snapshot의 정확한 UTF-8 bytes를
  SHA-256으로 계산한다. source ID/revision은 불변이며 같은 revision의 hash나 길이가
  달라지면 lint가 실패한다. 원천 bytes나 권리 상태를 linter가 직접 조회하지는 않는다.
- `corpusHash`: 그 revision의 승인 corpus manifest 파일의 정확한 bytes를 SHA-256으로
  계산한다. manifest에는 source ID/revision/hash, 공개 자격·권리 확인 기록과 snapshot
  보관 위치를 적는다. 같은 corpus revision의 hash가 입력 파일 사이에서 다르면 실패한다.
- `goldHash`: case에서 `goldHash`, `reviews`, `adjudication` 세 필드만 제외한 모든
  필드를 UTF-8 JSON으로 직렬화해 SHA-256으로 계산한다. object key는 모든 깊이에서
  사전순, 공백/indent 없음, `ensure_ascii=False`, separator는 `,`와 `:`이며 배열 순서는
  유지한다. 추가 Unicode 정규화와 마지막 줄바꿈은 없다. Python 기준 식은
  `json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")`다.
  질문·split·version·원천·gold 라벨이 바뀌면 검수를 새 hash로 다시 받아야 한다.
- Dataset 파일 hash: 최종 JSON 파일의 정확한 bytes를 SHA-256으로 계산해 **파일 외부의
  release manifest**에 저장한다. 자기 파일의 hash를 내부에 넣는 순환을 피하고 검수
  사유 변경까지 pin한다. release manifest에는 schema 파일 hash, development/sealed 파일
  hash, corpus manifest hash, 생성 일자·책임자, source snapshot 목록을 함께 적는다.

Release manifest는 공개 자격을 확인한 사람/기록, 질문 작성자, 사람 작성 또는 보조 생성
방식, 생성 도구·모델/설정, 생성 시 접근한 source revision·dataset version과 실행 기록을
참조한다. 개발용 생성 모델/프롬프트/튜닝 작업이 봉인 질문·정답·해설을 보았는지도
명시한다. 현 저장소 fixture의 `a`/`b` hash는 형식 검증용 placeholder이므로 snapshot의
무결성이나 공개 자격을 증명하지 않는다. 실제 snapshot bytes·권리와 provenance 확인은
데이터 작성/승격 담당자가 수행한다.

## 독립 검수와 불일치 조정

두 검수자가 질문과 원천의 장소·offset·0/1/2 관련도·route·최소 사실을 독립 확인한다.
각 검수 결정은 동일한 현재 `goldHash`를 참조한다. 두 검수자 ID는 달라야 하며
ACCEPT/REJECT와 이유를 각각 보존한다. linter는 서로 다른 ID와 hash 일치를 검사하고,
실제 사람이 독립적으로 검수했는지 여부는 운영 절차에서 확인한다.

두 사람이 ACCEPT하면 `adjudication.status=AGREED`, `decision=ACCEPT`,
`adjudicatorId=null`과 합의 사유를 기록한다. 불일치하면 `PENDING`으로 두고 평가 입력에서
제외한다. 제3의 독립 조정자가 근거를 확인해 최종 gold를 승인했을 때만 `RESOLVED`,
`decision=ACCEPT`, 두 검수자와 다른 조정자 ID를 기록한다. 검수 중 라벨을 고쳤다면
새 `goldHash`에 대한 두 결정을 다시 기록하고 과거 검수 기록은 접근 제한된 이력에
보관한다. 현재 파일에서 질문/라벨이 바뀌었거나 과거 hash를 검토한 기록, 중복 검수자,
미조정 불일치와 최종 REJECT는 모두 lint 실패다. linter는 승인이나 라벨 생성을 하지 않는다.

## Split 묶음과 봉인 접근

같은 canonical 장소를 다루거나 같은 `(sourceId, sourceRevision)`을 사용하는 변형은
**하나의 split**에 둔다. 두 조건 중 하나만 같아도 교차를 거절하는 보수적인 규칙이다.
장소 묶음은 선언한 sources, 질문 frame의 명시적 대상, 양의 관련도 장소를 포함한다.
따라서 source ID·질문 문구·query ID만 바꾸어도 같은 장소의 질문을 반대 split으로 옮길
수 없다. 장소가 달라도 동일 source revision이면 같은 묶음이며 여러 source를 가진
case는 모든 묶음에 속한다. 질문을 만들기 전에 묶음을 배정한다. 분리한 JSON 파일도
하나의 호출로 검사해야 한다.

```bash
scripts/lint-rag-gold /protected/gold/development.json /protected/gold/sealed.json
```

전체 입력은 고유 query ID, 동일 dataset version, 일관된 원천/corpus hash를 가져야 한다.
같은 split 안의 질문 변형은 허용한다. 스키마만 검증하면 offset 관계, 검수 완료 여부와
교차 파일 누수를 검출하지 못하므로 승격 전 반드시 실행형 lint도 수행한다.

개발셋은 실험/튜닝 담당자가 사용한다. 봉인 질문·gold·해설·snapshot 매핑은 지정한
평가셋 관리자와 승격 평가 principal에만 읽기 권한을 주고 개발 프롬프트·일상 CI 출력·
공개 Git 이력에 넣지 않는다. 전체 파일 검사는 두 split에 접근 가능한 제한된 평가
환경에서 수행하고, 일상 CI는 여기의 공개 합성 fixture만 검사한다. 접근과 승격 실행은
누가/언제/어느 dataset hash를 읽었는지 기록한다. 저장소의 공개 lint는 ACL을 설정하거나
봉인 데이터를 자동 내려받지 않는다.

봉인셋은 승격 판단 때만 사용하며 결과를 보고 route/threshold/프롬프트를 사후 튜닝하지
않는다. 반복 튜닝에 노출했거나 모델 생성 입력으로 제공했다면 노출 기록을 남기고 해당
봉인셋을 은퇴시켜 새 version을 만든다. 운영 대화는 동의 없이 복제하지 않는다.
운영 신호에서 필요한 사례는 공개 source로 합성 재현하고 다시 이중 검수해 **다음
version**에 추가한다. 철회 source가 있으면 현재 평가 입력을 격리하고 대체 snapshot/
case를 새 version으로 검수한다. 과거 source를 다시 공개하지 않도록 접근과 보존도
권리 정책을 따른다.
