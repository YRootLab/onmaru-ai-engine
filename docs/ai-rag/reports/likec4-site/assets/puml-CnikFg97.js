var e=e=>{switch(e){case`index`:return`@startuml
title "Landscape view"
top to bottom direction

hide stereotype
skinparam ranksep 60
skinparam nodesep 30
skinparam {
  arrowFontSize 10
  defaultTextAlignment center
  wrapWidth 200
  maxMessageSize 100
  shadowing false
}

skinparam person<<Traveler>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam person<<Admin>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam rectangle<<Onmaru>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<Gemini>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<Observability>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
person "==여행자\\n\\nOnMaru 웹에서 대화형 여정 검색을 요청하고 검증된 결과를 받는다." <<Traveler>> as Traveler
person "==운영자\\n\\nGrafana 검토 큐에서 품질 저하 사례를 선택해 격리 실험을 시작하고 승격을 승인한다." <<Admin>> as Admin
rectangle "==OnMaru" <<Onmaru>> as Onmaru
component "==Gemini API\\n<size:10>[공개 근거와 허용된 주제 code만 받고 구조화된 claim proposal을 반환한다.]</size>\\n\\nGoogle AI" <<Gemini>> as Gemini
component "==Grafana Cloud\\n<size:10>[공통 trace 조회, metric/dashboard/alerts, 품질 검토 화면.]</size>\\n\\nOTel / Prometheus compatible" <<Observability>> as Observability

Traveler .[#8D8D8D,thickness=2].> Onmaru : <color:#8D8D8D>대화 질문 입력\\n<size:8>[<color:#8D8D8D>HTTPS]</size>
Admin .[#8D8D8D,thickness=2].> Onmaru : <color:#8D8D8D>[...]\\n<size:8>[<color:#8D8D8D>operator initiated]</size>
Onmaru .[#8D8D8D,thickness=2].> Gemini : <color:#8D8D8D>[...]\\n<size:8>[<color:#8D8D8D>HTTPS · no member transcript]</size>
Onmaru .[#8D8D8D,thickness=2].> Observability : <color:#8D8D8D>[...]
Gemini .[#8D8D8D,thickness=2].> Onmaru : <color:#8D8D8D>[...]\\n<size:8>[<color:#8D8D8D>HTTPS]</size>
@enduml
`;case`system-context`:return`@startuml
title "1 · OnMaru 시스템 경계"
left to right direction

hide stereotype
skinparam ranksep 60
skinparam nodesep 30
skinparam {
  arrowFontSize 10
  defaultTextAlignment center
  wrapWidth 200
  maxMessageSize 100
  shadowing false
}

skinparam person<<Traveler>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam person<<Admin>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam rectangle<<Onmaru>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<Gemini>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<Observability>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
person "==여행자\\n\\nOnMaru 웹에서 대화형 여정 검색을 요청하고 검증된 결과를 받는다." <<Traveler>> as Traveler
person "==운영자\\n\\nGrafana 검토 큐에서 품질 저하 사례를 선택해 격리 실험을 시작하고 승격을 승인한다." <<Admin>> as Admin
rectangle "==OnMaru" <<Onmaru>> as Onmaru
component "==Gemini API\\n<size:10>[공개 근거와 허용된 주제 code만 받고 구조화된 claim proposal을 반환한다.]</size>\\n\\nGoogle AI" <<Gemini>> as Gemini
component "==Grafana Cloud\\n<size:10>[공통 trace 조회, metric/dashboard/alerts, 품질 검토 화면.]</size>\\n\\nOTel / Prometheus compatible" <<Observability>> as Observability

Traveler .[#8D8D8D,thickness=2].> Onmaru : <color:#8D8D8D>대화 질문 입력\\n<size:8>[<color:#8D8D8D>HTTPS]</size>
Admin .[#8D8D8D,thickness=2].> Onmaru : <color:#8D8D8D>[...]\\n<size:8>[<color:#8D8D8D>operator initiated]</size>
Onmaru .[#8D8D8D,thickness=2].> Gemini : <color:#8D8D8D>[...]\\n<size:8>[<color:#8D8D8D>HTTPS · no member transcript]</size>
Onmaru .[#8D8D8D,thickness=2].> Observability : <color:#8D8D8D>[...]
Gemini .[#8D8D8D,thickness=2].> Onmaru : <color:#8D8D8D>[...]\\n<size:8>[<color:#8D8D8D>HTTPS]</size>
@enduml
`;case`service-containers`:return`@startuml
title "2 · FE, Spring, FastAPI, PostgreSQL 경계"
left to right direction

hide stereotype
skinparam ranksep 60
skinparam nodesep 30
skinparam {
  arrowFontSize 10
  defaultTextAlignment center
  wrapWidth 200
  maxMessageSize 100
  shadowing false
}

skinparam person<<Traveler>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam person<<Admin>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<Gemini>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruSpring>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam rectangle<<OnmaruWeb>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAi>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruNginx>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam database<<OnmaruDb>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<Observability>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
person "==여행자\\n\\nOnMaru 웹에서 대화형 여정 검색을 요청하고 검증된 결과를 받는다." <<Traveler>> as Traveler
person "==운영자\\n\\nGrafana 검토 큐에서 품질 저하 사례를 선택해 격리 실험을 시작하고 승격을 승인한다." <<Admin>> as Admin
component "==Gemini API\\n<size:10>[공개 근거와 허용된 주제 code만 받고 구조화된 claim proposal을 반환한다.]</size>\\n\\nGoogle AI" <<Gemini>> as Gemini
rectangle "OnMaru" <<Onmaru>> as Onmaru {
  skinparam RectangleBorderColor<<Onmaru>> #3b82f6
  skinparam RectangleFontColor<<Onmaru>> #3b82f6
  skinparam RectangleBorderStyle<<Onmaru>> dashed

  component "==Spring API Server\\n<size:10>[회원 인증·대화·쿼리 권한·정형 SQL·최종 검증·영속화·SSE를 소유한다.]</size>\\n\\nSpring Boot · 독립 프로세스" <<OnmaruSpring>> as OnmaruSpring
  rectangle "==Next.js Web\\n<size:10>[대화 입력, SSE 표시, 장소 카드, 출처, 이어하기 UI.]</size>\\n\\nNext.js · Vercel" <<OnmaruWeb>> as OnmaruWeb
  component "==FastAPI AI Server\\n<size:10>[비공개 AI API. 질문 해석·route 제안·승인 plan 검색·근거 제한 생성·비동기 평가 코드를 소유한다.]</size>\\n\\nPython · 독립 프로세스 · onmaru-ai-engine 저장소" <<OnmaruAi>> as OnmaruAi
  component "==Public API Ingress\\n<size:10>[외부에 80/443만 열고 HTTPS와 SSE를 Spring API로 전달한다.]</size>\\n\\nNginx · Lightsail" <<OnmaruNginx>> as OnmaruNginx
  database "==PostgreSQL\\n<size:10>[업무 schema와 ai schema를 논리·role 권한으로 분리한다.]</size>\\n\\nPostGIS + pgvector + Korean full-text" <<OnmaruDb>> as OnmaruDb
}
component "==Grafana Cloud\\n<size:10>[공통 trace 조회, metric/dashboard/alerts, 품질 검토 화면.]</size>\\n\\nOTel / Prometheus compatible" <<Observability>> as Observability

Traveler .[#8D8D8D,thickness=2].> OnmaruWeb : <color:#8D8D8D>대화 질문 입력\\n<size:8>[<color:#8D8D8D>HTTPS]</size>
Admin .[#8D8D8D,thickness=2].> OnmaruAi : <color:#8D8D8D>선택한 품질 사례 조사·격리 실험 시작\\n<size:8>[<color:#8D8D8D>operator initiated]</size>
Gemini .[#8D8D8D,thickness=2].> OnmaruAi : <color:#8D8D8D>구조화 claim proposal\\n<size:8>[<color:#8D8D8D>HTTPS]</size>
OnmaruWeb .[#8D8D8D,thickness=2].> OnmaruNginx : <color:#8D8D8D>API request / SSE connection\\n<size:8>[<color:#8D8D8D>HTTPS · api.onmaru.site]</size>
OnmaruSpring .[#8D8D8D,thickness=2].> OnmaruWeb : <color:#8D8D8D>저장된 snapshot을 SSE replay\\n<size:8>[<color:#8D8D8D>SSE · Last-Event-ID]</size>
OnmaruNginx .[#8D8D8D,thickness=2].> OnmaruSpring : <color:#8D8D8D>proxy API / SSE; buffering disabled\\n<size:8>[<color:#8D8D8D>private Docker network]</size>
OnmaruSpring .[#8D8D8D,thickness=2].> OnmaruAi : <color:#8D8D8D>[...]
OnmaruSpring .[#8D8D8D,thickness=2].> OnmaruDb : <color:#8D8D8D>정형 사실 조회·대화 저장\\n<size:8>[<color:#8D8D8D>Spring DB role]</size>
OnmaruAi .[#8D8D8D,thickness=2].> OnmaruSpring : <color:#8D8D8D>[...]\\n<size:8>[<color:#8D8D8D>Private HTTP]</size>
OnmaruAi .[#8D8D8D,thickness=2].> OnmaruDb : <color:#8D8D8D>공개 corpus 검색·평가 artifact\\n<size:8>[<color:#8D8D8D>AI least-privilege DB role]</size>
OnmaruDb .[#8D8D8D,thickness=2].> OnmaruAi : <color:#8D8D8D>[...]
OnmaruSpring .[#8D8D8D,thickness=2].> Observability : <color:#8D8D8D>root span / low-cardinality metrics\\n<size:8>[<color:#8D8D8D>OTLP]</size>
OnmaruAi .[#8D8D8D,thickness=2].> Gemini : <color:#8D8D8D>근거 제한 생성 요청\\n<size:8>[<color:#8D8D8D>HTTPS · no member transcript]</size>
OnmaruAi .[#8D8D8D,thickness=2].> Observability : <color:#8D8D8D>child spans / retrieval stage metrics\\n<size:8>[<color:#8D8D8D>W3C trace context]</size>
@enduml
`;case`spring-components`:return`@startuml
title "3A · Spring 서버 책임"
top to bottom direction

hide stereotype
skinparam ranksep 60
skinparam nodesep 30
skinparam {
  arrowFontSize 10
  defaultTextAlignment center
  wrapWidth 200
  maxMessageSize 100
  shadowing false
}

skinparam component<<OnmaruAi>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruSpringAuthority>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruSpringFinalValidator>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruSpringAdmission>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<Observability>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruSpringSqlExecutor>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruSpringPersistence>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruSpringPrivacy>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam database<<OnmaruDb>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam rectangle<<OnmaruWeb>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
component "==FastAPI AI Server\\n<size:10>[비공개 AI API. 질문 해석·route 제안·승인 plan 검색·근거 제한 생성·비동기 평가 코드를 소유한다.]</size>\\n\\nPython · 독립 프로세스 · onmaru-ai-engine 저장소" <<OnmaruAi>> as OnmaruAi
rectangle "Spring API Server" <<OnmaruSpring>> as OnmaruSpring {
  skinparam RectangleBorderColor<<OnmaruSpring>> #3b82f6
  skinparam RectangleFontColor<<OnmaruSpring>> #3b82f6
  skinparam RectangleBorderStyle<<OnmaruSpring>> dashed

  component "==Plan Authority Gate\\n<size:10>[route·정형 필드·ID·공개 필터·version을 승인한다.]</size>\\n\\nallowlist / hard filters" <<OnmaruSpringAuthority>> as OnmaruSpringAuthority
  component "==Final Validator\\n<size:10>[장소·출처·철회·조건·claim을 다시 검증한다.]</size>\\n\\nclaim / rights / state" <<OnmaruSpringFinalValidator>> as OnmaruSpringFinalValidator
  component "==Admission & Conversation\\n<size:10>[소유권, 사용량, 대화 컨텍스트, 멱등성 검사.]</size>\\n\\nauth / run / state" <<OnmaruSpringAdmission>> as OnmaruSpringAdmission
  component "==Canonical SQL Executor\\n<size:10>[허용된 정형 사실만 업무 schema에서 조회한다.]</size>\\n\\nparameterized SQL" <<OnmaruSpringSqlExecutor>> as OnmaruSpringSqlExecutor
  component "==Run Persistence & SSE\\n<size:10>[확정 답변을 저장한 뒤 상태와 답변 조각을 SSE로 전송한다.]</size>\\n\\nsnapshot / replay" <<OnmaruSpringPersistence>> as OnmaruSpringPersistence
  component "==Input Privacy Gate\\n<size:10>[원문을 유지하고 AI plan용 비식별 질문을 만든다.]</size>\\n\\nsafeQuery" <<OnmaruSpringPrivacy>> as OnmaruSpringPrivacy
}
component "==Grafana Cloud\\n<size:10>[공통 trace 조회, metric/dashboard/alerts, 품질 검토 화면.]</size>\\n\\nOTel / Prometheus compatible" <<Observability>> as Observability
database "==PostgreSQL\\n<size:10>[업무 schema와 ai schema를 논리·role 권한으로 분리한다.]</size>\\n\\nPostGIS + pgvector + Korean full-text" <<OnmaruDb>> as OnmaruDb
rectangle "==Next.js Web\\n<size:10>[대화 입력, SSE 표시, 장소 카드, 출처, 이어하기 UI.]</size>\\n\\nNext.js · Vercel" <<OnmaruWeb>> as OnmaruWeb

OnmaruAi .[#8D8D8D,thickness=2].> OnmaruSpringAuthority : <color:#8D8D8D>PlanProposal
OnmaruAi .[#8D8D8D,thickness=2].> OnmaruSpringFinalValidator : <color:#8D8D8D>ValidatedProposal
OnmaruSpringAdmission .[#8D8D8D,thickness=2].> OnmaruSpringPrivacy : <color:#8D8D8D>load confirmed context · create safeQuery
OnmaruSpringAuthority .[#8D8D8D,thickness=2].> OnmaruSpringSqlExecutor : <color:#8D8D8D>authorize canonical fields
OnmaruSpringFinalValidator .[#8D8D8D,thickness=2].> OnmaruSpringPersistence : <color:#8D8D8D>persist validated snapshot
OnmaruSpringPrivacy .[#8D8D8D,thickness=2].> OnmaruAi : <color:#8D8D8D>plan request · transient safeQuery
OnmaruSpringAuthority .[#8D8D8D,thickness=2].> OnmaruAi : <color:#8D8D8D>approved plan · planHash
OnmaruSpringSqlExecutor .[#8D8D8D,thickness=2].> OnmaruDb : <color:#8D8D8D>read permitted facts
OnmaruSpringPersistence .[#8D8D8D,thickness=2].> OnmaruWeb : <color:#8D8D8D>verified SSE / replay
OnmaruSpringPersistence .[#8D8D8D,thickness=2].> OnmaruAi : <color:#8D8D8D>privacy-safe run observation
OnmaruSpring .[#8D8D8D,thickness=2].> Observability : <color:#8D8D8D>root span / low-cardinality metrics\\n<size:8>[<color:#8D8D8D>OTLP]</size>
@enduml
`;case`fastapi-components`:return`@startuml
title "3B · FastAPI AI Engine 내부 모듈"
top to bottom direction

hide stereotype
skinparam ranksep 60
skinparam nodesep 30
skinparam {
  arrowFontSize 10
  defaultTextAlignment center
  wrapWidth 200
  maxMessageSize 100
  shadowing false
}

skinparam person<<Admin>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<Gemini>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruSpring>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam database<<OnmaruDb>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiQualityHarness>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiPlanApi>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiExecuteApi>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiCorpusWorker>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<Observability>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiQueryProcessing>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiPlanValidator>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiLexical>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiDense>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiFusion>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiReranker>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiEvidence>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiPrompt>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiGenerator>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiProposalValidator>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
person "==운영자\\n\\nGrafana 검토 큐에서 품질 저하 사례를 선택해 격리 실험을 시작하고 승격을 승인한다." <<Admin>> as Admin
component "==Gemini API\\n<size:10>[공개 근거와 허용된 주제 code만 받고 구조화된 claim proposal을 반환한다.]</size>\\n\\nGoogle AI" <<Gemini>> as Gemini
component "==Spring API Server\\n<size:10>[회원 인증·대화·쿼리 권한·정형 SQL·최종 검증·영속화·SSE를 소유한다.]</size>\\n\\nSpring Boot · 독립 프로세스" <<OnmaruSpring>> as OnmaruSpring
database "==PostgreSQL\\n<size:10>[업무 schema와 ai schema를 논리·role 권한으로 분리한다.]</size>\\n\\nPostGIS + pgvector + Korean full-text" <<OnmaruDb>> as OnmaruDb
rectangle "FastAPI AI Server" <<OnmaruAi>> as OnmaruAi {
  skinparam RectangleBorderColor<<OnmaruAi>> #3b82f6
  skinparam RectangleFontColor<<OnmaruAi>> #3b82f6
  skinparam RectangleBorderStyle<<OnmaruAi>> dashed

  component "==Quality Harness\\n<size:10>[trace·gold 평가에서 실패를 분류하고 선택된 격리 실험 결과를 만든다.]</size>\\n\\nasynchronous / human controlled" <<OnmaruAiQualityHarness>> as OnmaruAiQualityHarness
  component "==Plan API\\n<size:10>[safeQuery와 구조화 맥락을 해석하고 PlanProposal을 반환한다.]</size>\\n\\nPOST /internal/v1/plans" <<OnmaruAiPlanApi>> as OnmaruAiPlanApi
  component "==Execute API\\n<size:10>[Spring이 승인한 plan hash와 필요한 CanonicalFacts만 받는다.]</size>\\n\\nPOST /internal/v1/runs/{id}/execute" <<OnmaruAiExecuteApi>> as OnmaruAiExecuteApi
  component "==Corpus Worker\\n<size:10>[공개 projection을 파싱·청킹·enrichment·임베딩·색인한다.]</size>\\n\\noffline / serialized" <<OnmaruAiCorpusWorker>> as OnmaruAiCorpusWorker
  component "==Query Processing Layer\\n<size:10>[검색 계획 API 안에서 순차 실행하는 논리 계층이며 별도 서비스가 아니다.]</size>\\n\\nPreprocessing → Interpretation → Search Router" <<OnmaruAiQueryProcessing>> as OnmaruAiQueryProcessing
  component "==Approved Plan Validator\\n<size:10>[승인 plan·config·corpus·철회 sequence를 검증한다.]</size>\\n\\nhash / revision / policy" <<OnmaruAiPlanValidator>> as OnmaruAiPlanValidator
  component "==Keyword Search\\n<size:10>[정확어·검수 별칭·한국어 full-text 후보와 순위를 반환한다.]</size>\\n\\nexact / alias / BM25" <<OnmaruAiLexical>> as OnmaruAiLexical
  component "==Semantic Search\\n<size:10>[질문과 청크 임베딩의 의미 유사도로 후보를 반환한다.]</size>\\n\\ne5-small 384D / pgvector" <<OnmaruAiDense>> as OnmaruAiDense
  component "==Hybrid Fusion\\n<size:10>[Keyword·Semantic Search 두 결과가 있을 때만 RRF로 순위를 결합한다.]</size>\\n\\nconditional RRF" <<OnmaruAiFusion>> as OnmaruAiFusion
  component "==Reranker\\n<size:10>[fusion 또는 단일 검색 후보의 관련도를 다시 채점하며 제한적 복귀를 지원한다.]</size>\\n\\ncross-encoder / versioned model" <<OnmaruAiReranker>> as OnmaruAiReranker
  component "==Evidence Selector\\n<size:10>[장소별 출처·revision·본문 span을 고른다.]</size>\\n\\nmax 12 chunks" <<OnmaruAiEvidence>> as OnmaruAiEvidence
  component "==Prompt Assembler\\n<size:10>[추천·수정·해설·비교 템플릿과 공개 근거만 구성한다.]</size>\\n\\ntask templates" <<OnmaruAiPrompt>> as OnmaruAiPrompt
  component "==Grounded Generator\\n<size:10>[근거 기반 구조화 claim을 제안한다.]</size>\\n\\nGemini provider adapter" <<OnmaruAiGenerator>> as OnmaruAiGenerator
  component "==Proposal Validator\\n<size:10>[claim별 evidence ID·장소 ID·길이·schema를 검증한다.]</size>\\n\\nclosed schema / evidence allowlist" <<OnmaruAiProposalValidator>> as OnmaruAiProposalValidator
}
component "==Grafana Cloud\\n<size:10>[공통 trace 조회, metric/dashboard/alerts, 품질 검토 화면.]</size>\\n\\nOTel / Prometheus compatible" <<Observability>> as Observability

Admin .[#8D8D8D,thickness=2].> OnmaruAiQualityHarness : <color:#8D8D8D>operator-selected investigation / experiment
Gemini .[#8D8D8D,thickness=2].> OnmaruAiGenerator : <color:#8D8D8D>structured proposal
OnmaruSpring .[#8D8D8D,thickness=2].> OnmaruAiPlanApi : <color:#8D8D8D>plan request · transient safeQuery
OnmaruSpring .[#8D8D8D,thickness=2].> OnmaruAiExecuteApi : <color:#8D8D8D>approved plan · planHash
OnmaruSpring .[#8D8D8D,thickness=2].> OnmaruAiQualityHarness : <color:#8D8D8D>privacy-safe run observation
OnmaruDb .[#8D8D8D,thickness=2].> OnmaruAiCorpusWorker : <color:#8D8D8D>public projection + rights revision
OnmaruDb .[#8D8D8D,thickness=2].> OnmaruAiQualityHarness : <color:#8D8D8D>gold set + expected evidence
OnmaruAiPlanApi .[#8D8D8D,thickness=2].> OnmaruAiQueryProcessing : <color:#8D8D8D>preprocess safeQuery
OnmaruAiExecuteApi .[#8D8D8D,thickness=2].> OnmaruAiPlanValidator : <color:#8D8D8D>validate approved envelope
OnmaruAiPlanValidator .[#8D8D8D,thickness=2].> OnmaruAiLexical : <color:#8D8D8D>keyword route when requested
OnmaruAiPlanValidator .[#8D8D8D,thickness=2].> OnmaruAiDense : <color:#8D8D8D>semantic route when requested
OnmaruAiLexical .[#8D8D8D,thickness=2].> OnmaruAiFusion : <color:#8D8D8D>ranked candidates
OnmaruAiLexical .[#8D8D8D,thickness=2].> OnmaruAiReranker : <color:#8D8D8D>single Keyword Search route bypasses fusion
OnmaruAiDense .[#8D8D8D,thickness=2].> OnmaruAiFusion : <color:#8D8D8D>ranked candidates
OnmaruAiDense .[#8D8D8D,thickness=2].> OnmaruAiReranker : <color:#8D8D8D>single Semantic Search route bypasses fusion
OnmaruAiFusion .[#8D8D8D,thickness=2].> OnmaruAiReranker : <color:#8D8D8D>RRF-ranked hybrid candidates
OnmaruAiReranker .[#8D8D8D,thickness=2].> OnmaruAiEvidence : <color:#8D8D8D>reranked candidates
OnmaruAiEvidence .[#8D8D8D,thickness=2].> OnmaruAiPrompt : <color:#8D8D8D>EvidenceSet
OnmaruAiPrompt .[#8D8D8D,thickness=2].> OnmaruAiGenerator : <color:#8D8D8D>bounded prompt
OnmaruAiGenerator .[#8D8D8D,thickness=2].> OnmaruAiProposalValidator : <color:#8D8D8D>claim + evidence IDs
OnmaruAiQueryProcessing .[#8D8D8D,thickness=2].> OnmaruSpring : <color:#8D8D8D>PlanProposal
OnmaruAiGenerator .[#8D8D8D,thickness=2].> Gemini : <color:#8D8D8D>public evidence only
OnmaruAiProposalValidator .[#8D8D8D,thickness=2].> OnmaruSpring : <color:#8D8D8D>ValidatedProposal
OnmaruAiCorpusWorker .[#8D8D8D,thickness=2].> OnmaruDb : <color:#8D8D8D>inactive revision → validate → activate
OnmaruAiQualityHarness .[#8D8D8D,thickness=2].> OnmaruDb : <color:#8D8D8D>metrics + review artifact
OnmaruAi .[#8D8D8D,thickness=2].> Observability : <color:#8D8D8D>child spans / retrieval stage metrics\\n<size:8>[<color:#8D8D8D>W3C trace context]</size>
@enduml
`;case`production-deployment`:return`@startuml
title "4 · 운영 배포 토폴로지"
top to bottom direction

hide stereotype
skinparam ranksep 60
skinparam nodesep 30
skinparam {
  arrowFontSize 10
  defaultTextAlignment center
  wrapWidth 200
  maxMessageSize 100
  shadowing false
}

skinparam component<<ProductionAwsLightsail2gbSpringProcessSpringInstance>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<ProductionGoogleGeminiServiceGeminiInstance>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam rectangle<<ProductionVercelWebRuntimeWebInstance>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<ProductionAwsLightsail2gbNginxNginxInstance>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<ProductionAwsLightsail2gbFastapiProcessAiInstance>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<ProductionGrafanaCloudTelemetryBackendGrafanaInstance>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam database<<ProductionAwsLightsail2gbPostgresProcessDbInstance>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
rectangle "aws" <<ProductionAws>> as ProductionAws {
  skinparam RectangleBorderColor<<ProductionAws>> #3b82f6
  skinparam RectangleFontColor<<ProductionAws>> #3b82f6
  skinparam RectangleBorderStyle<<ProductionAws>> dashed

  rectangle "lightsail2gb" <<ProductionAwsLightsail2gb>> as ProductionAwsLightsail2gb {
    skinparam RectangleBorderColor<<ProductionAwsLightsail2gb>> #3b82f6
    skinparam RectangleFontColor<<ProductionAwsLightsail2gb>> #3b82f6
    skinparam RectangleBorderStyle<<ProductionAwsLightsail2gb>> dashed

    component "==Spring API Server\\n<size:10>[회원 인증·대화·쿼리 권한·정형 SQL·최종 검증·영속화·SSE를 소유한다.]</size>\\n\\nSpring Boot · 독립 프로세스" <<ProductionAwsLightsail2gbSpringProcessSpringInstance>> as ProductionAwsLightsail2gbSpringProcessSpringInstance
    component "==Public API Ingress\\n<size:10>[외부에 80/443만 열고 HTTPS와 SSE를 Spring API로 전달한다.]</size>\\n\\nNginx · Lightsail" <<ProductionAwsLightsail2gbNginxNginxInstance>> as ProductionAwsLightsail2gbNginxNginxInstance
    component "==FastAPI AI Server\\n<size:10>[비공개 AI API. 질문 해석·route 제안·승인 plan 검색·근거 제한 생성·비동기 평가 코드를 소유한다.]</size>\\n\\nPython · 독립 프로세스 · onmaru-ai-engine 저장소" <<ProductionAwsLightsail2gbFastapiProcessAiInstance>> as ProductionAwsLightsail2gbFastapiProcessAiInstance
    database "==PostgreSQL\\n<size:10>[업무 schema와 ai schema를 논리·role 권한으로 분리한다.]</size>\\n\\nPostGIS + pgvector + Korean full-text" <<ProductionAwsLightsail2gbPostgresProcessDbInstance>> as ProductionAwsLightsail2gbPostgresProcessDbInstance
  }
}
component "==Gemini API\\n<size:10>[공개 근거와 허용된 주제 code만 받고 구조화된 claim proposal을 반환한다.]</size>\\n\\nGoogle AI" <<ProductionGoogleGeminiServiceGeminiInstance>> as ProductionGoogleGeminiServiceGeminiInstance
rectangle "==Next.js Web\\n<size:10>[대화 입력, SSE 표시, 장소 카드, 출처, 이어하기 UI.]</size>\\n\\nNext.js · Vercel" <<ProductionVercelWebRuntimeWebInstance>> as ProductionVercelWebRuntimeWebInstance
component "==Grafana Cloud\\n<size:10>[공통 trace 조회, metric/dashboard/alerts, 품질 검토 화면.]</size>\\n\\nOTel / Prometheus compatible" <<ProductionGrafanaCloudTelemetryBackendGrafanaInstance>> as ProductionGrafanaCloudTelemetryBackendGrafanaInstance

ProductionVercelWebRuntimeWebInstance .[#8D8D8D,thickness=2].> ProductionAwsLightsail2gbNginxNginxInstance : <color:#8D8D8D>API request / SSE connection\\n<size:8>[<color:#8D8D8D>HTTPS · api.onmaru.site]</size>
ProductionAwsLightsail2gbSpringProcessSpringInstance .[#8D8D8D,thickness=2].> ProductionVercelWebRuntimeWebInstance : <color:#8D8D8D>[...]\\n<size:8>[<color:#8D8D8D>SSE · Last-Event-ID]</size>
ProductionGoogleGeminiServiceGeminiInstance .[#8D8D8D,thickness=2].> ProductionAwsLightsail2gbFastapiProcessAiInstance : <color:#8D8D8D>[...]\\n<size:8>[<color:#8D8D8D>HTTPS]</size>
ProductionAwsLightsail2gbSpringProcessSpringInstance .[#8D8D8D,thickness=2].> ProductionGrafanaCloudTelemetryBackendGrafanaInstance : <color:#8D8D8D>root span / low-cardinality metrics\\n<size:8>[<color:#8D8D8D>OTLP]</size>
ProductionAwsLightsail2gbFastapiProcessAiInstance .[#8D8D8D,thickness=2].> ProductionGrafanaCloudTelemetryBackendGrafanaInstance : <color:#8D8D8D>child spans / retrieval stage metrics\\n<size:8>[<color:#8D8D8D>W3C trace context]</size>
ProductionAwsLightsail2gbNginxNginxInstance .[#8D8D8D,thickness=2].> ProductionAwsLightsail2gbSpringProcessSpringInstance : <color:#8D8D8D>proxy API / SSE; buffering disabled\\n<size:8>[<color:#8D8D8D>private Docker network]</size>
ProductionAwsLightsail2gbSpringProcessSpringInstance .[#8D8D8D,thickness=2].> ProductionAwsLightsail2gbFastapiProcessAiInstance : <color:#8D8D8D>[...]
ProductionAwsLightsail2gbSpringProcessSpringInstance .[#8D8D8D,thickness=2].> ProductionAwsLightsail2gbPostgresProcessDbInstance : <color:#8D8D8D>[...]\\n<size:8>[<color:#8D8D8D>Spring DB role]</size>
ProductionAwsLightsail2gbFastapiProcessAiInstance .[#8D8D8D,thickness=2].> ProductionAwsLightsail2gbPostgresProcessDbInstance : <color:#8D8D8D>[...]\\n<size:8>[<color:#8D8D8D>AI least-privilege DB role]</size>
@enduml
`;case`online-rag-sse`:return`@startuml
title "5 · 대화형 RAG 요청과 SSE 응답"
left to right direction

hide stereotype
skinparam ranksep 60
skinparam nodesep 30
skinparam {
  arrowFontSize 10
  defaultTextAlignment center
  wrapWidth 200
  maxMessageSize 100
  shadowing false
}

skinparam rectangle<<OnmaruWeb>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruNginx>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruSpringAdmission>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruSpringPrivacy>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiPlanApi>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiQueryProcessingPreprocessing>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiQueryProcessingInterpretation>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruSpringAuthority>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiQueryProcessingSearchRouter>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruSpringSqlExecutor>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruDbBusinessSchema>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiExecuteApi>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiPlanValidator>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiLexical>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiDense>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiFusion>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiReranker>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiEvidence>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiPrompt>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiGenerator>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruSpringFinalValidator>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiProposalValidator>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<Gemini>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruSpringPersistence>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
rectangle "OnMaru" <<Onmaru>> as Onmaru {
  skinparam RectangleBorderColor<<Onmaru>> #3b82f6
  skinparam RectangleFontColor<<Onmaru>> #3b82f6
  skinparam RectangleBorderStyle<<Onmaru>> dashed

  rectangle "==Next.js Web\\n<size:10>[대화 입력, SSE 표시, 장소 카드, 출처, 이어하기 UI.]</size>\\n\\nNext.js · Vercel" <<OnmaruWeb>> as OnmaruWeb
  component "==Public API Ingress\\n<size:10>[외부에 80/443만 열고 HTTPS와 SSE를 Spring API로 전달한다.]</size>\\n\\nNginx · Lightsail" <<OnmaruNginx>> as OnmaruNginx
  component "==Admission & Conversation\\n<size:10>[소유권, 사용량, 대화 컨텍스트, 멱등성 검사.]</size>\\n\\nauth / run / state" <<OnmaruSpringAdmission>> as OnmaruSpringAdmission
  component "==Input Privacy Gate\\n<size:10>[원문을 유지하고 AI plan용 비식별 질문을 만든다.]</size>\\n\\nsafeQuery" <<OnmaruSpringPrivacy>> as OnmaruSpringPrivacy
  component "==Plan API\\n<size:10>[safeQuery와 구조화 맥락을 해석하고 PlanProposal을 반환한다.]</size>\\n\\nPOST /internal/v1/plans" <<OnmaruAiPlanApi>> as OnmaruAiPlanApi
  component "==Query Preprocessing\\n<size:10>[표기·검수 별칭을 정리하되 원문 의미·부정 범위를 보존한다.]</size>\\n\\nnormalization / aliases" <<OnmaruAiQueryProcessingPreprocessing>> as OnmaruAiQueryProcessingPreprocessing
  component "==Query Interpretation\\n<size:10>[질문을 QueryFrame으로 구조화하고 모호성·범위를 판정한다.]</size>\\n\\nintent / entities / constraints / context" <<OnmaruAiQueryProcessingInterpretation>> as OnmaruAiQueryProcessingInterpretation
  component "==Plan Authority Gate\\n<size:10>[route·정형 필드·ID·공개 필터·version을 승인한다.]</size>\\n\\nallowlist / hard filters" <<OnmaruSpringAuthority>> as OnmaruSpringAuthority
  component "==Search Router\\n<size:10>[결정적 route와 조회 제약을 PlanProposal로 제안한다.]</size>\\n\\nSQL / keyword / semantic / hybrid" <<OnmaruAiQueryProcessingSearchRouter>> as OnmaruAiQueryProcessingSearchRouter
  component "==Canonical SQL Executor\\n<size:10>[허용된 정형 사실만 업무 schema에서 조회한다.]</size>\\n\\nparameterized SQL" <<OnmaruSpringSqlExecutor>> as OnmaruSpringSqlExecutor
  component "==Business Schema\\n<size:10>[회원·대화·장소·권리의 canonical data.]</size>\\n\\nSpring-owned" <<OnmaruDbBusinessSchema>> as OnmaruDbBusinessSchema
  component "==Execute API\\n<size:10>[Spring이 승인한 plan hash와 필요한 CanonicalFacts만 받는다.]</size>\\n\\nPOST /internal/v1/runs/{id}/execute" <<OnmaruAiExecuteApi>> as OnmaruAiExecuteApi
  component "==Approved Plan Validator\\n<size:10>[승인 plan·config·corpus·철회 sequence를 검증한다.]</size>\\n\\nhash / revision / policy" <<OnmaruAiPlanValidator>> as OnmaruAiPlanValidator
  component "==Keyword Search\\n<size:10>[정확어·검수 별칭·한국어 full-text 후보와 순위를 반환한다.]</size>\\n\\nexact / alias / BM25" <<OnmaruAiLexical>> as OnmaruAiLexical
  component "==Semantic Search\\n<size:10>[질문과 청크 임베딩의 의미 유사도로 후보를 반환한다.]</size>\\n\\ne5-small 384D / pgvector" <<OnmaruAiDense>> as OnmaruAiDense
  component "==Hybrid Fusion\\n<size:10>[Keyword·Semantic Search 두 결과가 있을 때만 RRF로 순위를 결합한다.]</size>\\n\\nconditional RRF" <<OnmaruAiFusion>> as OnmaruAiFusion
  component "==Reranker\\n<size:10>[fusion 또는 단일 검색 후보의 관련도를 다시 채점하며 제한적 복귀를 지원한다.]</size>\\n\\ncross-encoder / versioned model" <<OnmaruAiReranker>> as OnmaruAiReranker
  component "==Evidence Selector\\n<size:10>[장소별 출처·revision·본문 span을 고른다.]</size>\\n\\nmax 12 chunks" <<OnmaruAiEvidence>> as OnmaruAiEvidence
  component "==Prompt Assembler\\n<size:10>[추천·수정·해설·비교 템플릿과 공개 근거만 구성한다.]</size>\\n\\ntask templates" <<OnmaruAiPrompt>> as OnmaruAiPrompt
  component "==Grounded Generator\\n<size:10>[근거 기반 구조화 claim을 제안한다.]</size>\\n\\nGemini provider adapter" <<OnmaruAiGenerator>> as OnmaruAiGenerator
  component "==Final Validator\\n<size:10>[장소·출처·철회·조건·claim을 다시 검증한다.]</size>\\n\\nclaim / rights / state" <<OnmaruSpringFinalValidator>> as OnmaruSpringFinalValidator
  component "==Proposal Validator\\n<size:10>[claim별 evidence ID·장소 ID·길이·schema를 검증한다.]</size>\\n\\nclosed schema / evidence allowlist" <<OnmaruAiProposalValidator>> as OnmaruAiProposalValidator
  component "==Run Persistence & SSE\\n<size:10>[확정 답변을 저장한 뒤 상태와 답변 조각을 SSE로 전송한다.]</size>\\n\\nsnapshot / replay" <<OnmaruSpringPersistence>> as OnmaruSpringPersistence
}
component "==Gemini API\\n<size:10>[공개 근거와 허용된 주제 code만 받고 구조화된 claim proposal을 반환한다.]</size>\\n\\nGoogle AI" <<Gemini>> as Gemini

OnmaruWeb .[#8D8D8D,thickness=2].> OnmaruNginx : <color:#8D8D8D>HTTPS · create run + open SSE\\n<size:8>[<color:#8D8D8D>HTTPS · api.onmaru.site]</size>
OnmaruNginx .[#8D8D8D,thickness=2].> OnmaruSpringAdmission : <color:#8D8D8D>POST /api/v1/journeys/{threadId}/runs
OnmaruSpringAdmission .[#8D8D8D,thickness=2].> OnmaruSpringPrivacy : <color:#8D8D8D>authenticate · load confirmed context
OnmaruSpringPrivacy .[#8D8D8D,thickness=2].> OnmaruAiPlanApi : <color:#8D8D8D>POST /internal/v1/plans · safeQuery
OnmaruAiPlanApi .[#8D8D8D,thickness=2].> OnmaruAiQueryProcessingPreprocessing : <color:#8D8D8D>Query Preprocessing
OnmaruAiQueryProcessingPreprocessing .[#8D8D8D,thickness=2].> OnmaruAiQueryProcessingInterpretation : <color:#8D8D8D>Query Interpretation
OnmaruAiQueryProcessingInterpretation .[#8D8D8D,thickness=2].> OnmaruAiQueryProcessingSearchRouter : <color:#8D8D8D>QueryFrame
OnmaruAiQueryProcessingSearchRouter .[#8D8D8D,thickness=2].> OnmaruSpringAuthority : <color:#8D8D8D>PlanProposal
OnmaruSpringAuthority .[#8D8D8D,thickness=2].> OnmaruSpringSqlExecutor : <color:#8D8D8D>execute permitted fields when route needs SQL
OnmaruSpringSqlExecutor .[#8D8D8D,thickness=2].> OnmaruDbBusinessSchema : <color:#8D8D8D>parameterized SQL · business role
OnmaruSpringAuthority .[#8D8D8D,thickness=2].> OnmaruAiExecuteApi : <color:#8D8D8D>POST /internal/v1/runs/{id}/execute · approved plan
OnmaruAiExecuteApi .[#8D8D8D,thickness=2].> OnmaruAiPlanValidator : <color:#8D8D8D>verify planHash · corpus/config/revocation
OnmaruAiPlanValidator .[#8D8D8D,thickness=2].> OnmaruAiLexical : <color:#8D8D8D>Keyword Search · BM25 when requested
OnmaruAiPlanValidator .[#8D8D8D,thickness=2].> OnmaruAiDense : <color:#8D8D8D>Semantic Search · 384D when requested
OnmaruAiLexical .[#8D8D8D,thickness=2].> OnmaruAiFusion : <color:#8D8D8D>ranked candidates
OnmaruAiDense .[#8D8D8D,thickness=2].> OnmaruAiFusion : <color:#8D8D8D>ranked candidates
OnmaruAiFusion .[#8D8D8D,thickness=2].> OnmaruAiReranker : <color:#8D8D8D>Hybrid Fusion · RRF only when both lists exist
OnmaruAiReranker .[#8D8D8D,thickness=2].> OnmaruAiEvidence : <color:#8D8D8D>Reranker · reranked candidates
OnmaruAiEvidence .[#8D8D8D,thickness=2].> OnmaruAiPrompt : <color:#8D8D8D>EvidenceSet · source spans
OnmaruAiPrompt .[#8D8D8D,thickness=2].> OnmaruAiGenerator : <color:#8D8D8D>bounded prompt
OnmaruAiGenerator .[#8D8D8D,thickness=2].> Gemini : <color:#8D8D8D>grounded structured generation
Gemini .[#8D8D8D,thickness=2].> OnmaruAiProposalValidator : <color:#8D8D8D>claim/evidence proposal
OnmaruAiProposalValidator .[#8D8D8D,thickness=2].> OnmaruSpringFinalValidator : <color:#8D8D8D>ValidatedProposal
OnmaruSpringFinalValidator .[#8D8D8D,thickness=2].> OnmaruSpringPersistence : <color:#8D8D8D>rights · claim · filters re-check
OnmaruSpringPersistence .[#8D8D8D,thickness=2].> OnmaruNginx : <color:#8D8D8D>verified SSE events / replay
OnmaruNginx .[#8D8D8D,thickness=2].> OnmaruWeb : <color:#8D8D8D>SSE stream to browser
@enduml
`;case`offline-corpus-quality`:return`@startuml
title "6 · 오프라인 Corpus와 비동기 Quality Harness"
left to right direction

hide stereotype
skinparam ranksep 60
skinparam nodesep 30
skinparam {
  arrowFontSize 10
  defaultTextAlignment center
  wrapWidth 200
  maxMessageSize 100
  shadowing false
}

skinparam component<<OnmaruSpring>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruDbBusinessSchema>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiCorpusWorker>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruDbAiSchema>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam person<<Admin>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiQualityHarness>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruDbEvalSchema>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
skinparam component<<OnmaruAiQueryProcessingSearchRouter>>{
  BackgroundColor #3b82f6
  FontColor #eff6ff
  BorderColor #2563eb
}
rectangle "OnMaru" <<Onmaru>> as Onmaru {
  skinparam RectangleBorderColor<<Onmaru>> #3b82f6
  skinparam RectangleFontColor<<Onmaru>> #3b82f6
  skinparam RectangleBorderStyle<<Onmaru>> dashed

  component "==Spring API Server\\n<size:10>[회원 인증·대화·쿼리 권한·정형 SQL·최종 검증·영속화·SSE를 소유한다.]</size>\\n\\nSpring Boot · 독립 프로세스" <<OnmaruSpring>> as OnmaruSpring
  component "==Business Schema\\n<size:10>[회원·대화·장소·권리의 canonical data.]</size>\\n\\nSpring-owned" <<OnmaruDbBusinessSchema>> as OnmaruDbBusinessSchema
  component "==Corpus Worker\\n<size:10>[공개 projection을 파싱·청킹·enrichment·임베딩·색인한다.]</size>\\n\\noffline / serialized" <<OnmaruAiCorpusWorker>> as OnmaruAiCorpusWorker
  component "==AI Corpus Schema\\n<size:10>[source/revision/chunk/vector/BM25 metadata와 active pointer.]</size>\\n\\nAI least-privilege role" <<OnmaruDbAiSchema>> as OnmaruDbAiSchema
  component "==Quality Harness\\n<size:10>[trace·gold 평가에서 실패를 분류하고 선택된 격리 실험 결과를 만든다.]</size>\\n\\nasynchronous / human controlled" <<OnmaruAiQualityHarness>> as OnmaruAiQualityHarness
  component "==Evaluation Artifacts\\n<size:10>[dataset hash·expected evidence·version·review queue.]</size>\\n\\naccess-controlled" <<OnmaruDbEvalSchema>> as OnmaruDbEvalSchema
  component "==Search Router\\n<size:10>[결정적 route와 조회 제약을 PlanProposal로 제안한다.]</size>\\n\\nSQL / keyword / semantic / hybrid" <<OnmaruAiQueryProcessingSearchRouter>> as OnmaruAiQueryProcessingSearchRouter
}
person "==운영자\\n\\nGrafana 검토 큐에서 품질 저하 사례를 선택해 격리 실험을 시작하고 승격을 승인한다." <<Admin>> as Admin

OnmaruSpring .[#8D8D8D,thickness=2].> OnmaruAiCorpusWorker : <color:#8D8D8D>versioned public projection · rights/revocation
OnmaruAiCorpusWorker .[#8D8D8D,thickness=2].> OnmaruDbAiSchema : <color:#8D8D8D>parse · chunk · enrich · embed · index inactive revision
OnmaruDbBusinessSchema .[#8D8D8D,thickness=2].> OnmaruAiCorpusWorker : <color:#8D8D8D>public-only source manifest
OnmaruAiQualityHarness .[#8D8D8D,thickness=2].> OnmaruDbEvalSchema : <color:#8D8D8D>persist run observations · evaluation artifacts
OnmaruDbEvalSchema .[#8D8D8D,thickness=2].> OnmaruAiQualityHarness : <color:#8D8D8D>gold replay · expected evidence
Admin .[#8D8D8D,thickness=2].> OnmaruAiQualityHarness : <color:#8D8D8D>select case · start isolated experiment
OnmaruAiQualityHarness .[#8D8D8D,thickness=2].> OnmaruAiQueryProcessingSearchRouter : <color:#8D8D8D>candidate config only after human approval
@enduml
`;default:throw Error(`Unknown viewId: `+e)}};export{e as pumlSource};