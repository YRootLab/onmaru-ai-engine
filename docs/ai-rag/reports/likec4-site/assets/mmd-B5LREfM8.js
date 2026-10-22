var e=e=>{switch(e){case`index`:return`---
title: "Landscape view"
---
graph TB
  Traveler@{ icon: "fa:user", shape: rounded, label: "여행자" }
  Admin@{ icon: "fa:user", shape: rounded, label: "운영자" }
  Onmaru@{ shape: rectangle, label: "OnMaru" }
  Gemini@{ shape: rectangle, label: "Gemini API" }
  Observability@{ shape: rectangle, label: "Grafana Cloud" }
  Traveler -. "\`대화 질문 입력\`" .-> Onmaru
  Admin -. "\`[...]\`" .-> Onmaru
  Onmaru -. "\`[...]\`" .-> Gemini
  Onmaru -. "\`[...]\`" .-> Observability
  Gemini -. "\`[...]\`" .-> Onmaru
`;case`system-context`:return`---
title: "1 · OnMaru 시스템 경계"
---
graph LR
  Traveler@{ icon: "fa:user", shape: rounded, label: "여행자" }
  Admin@{ icon: "fa:user", shape: rounded, label: "운영자" }
  Onmaru@{ shape: rectangle, label: "OnMaru" }
  Gemini@{ shape: rectangle, label: "Gemini API" }
  Observability@{ shape: rectangle, label: "Grafana Cloud" }
  Traveler -. "\`대화 질문 입력\`" .-> Onmaru
  Admin -. "\`[...]\`" .-> Onmaru
  Onmaru -. "\`[...]\`" .-> Gemini
  Onmaru -. "\`[...]\`" .-> Observability
  Gemini -. "\`[...]\`" .-> Onmaru
`;case`service-containers`:return'---\ntitle: "2 · FE, Spring, FastAPI, PostgreSQL 경계"\n---\ngraph LR\n  Traveler@{ icon: "fa:user", shape: rounded, label: "여행자" }\n  Admin@{ icon: "fa:user", shape: rounded, label: "운영자" }\n  Gemini@{ shape: rectangle, label: "Gemini API" }\n  subgraph Onmaru["`OnMaru`"]\n    Onmaru.Spring@{ shape: rectangle, label: "Spring API Server" }\n    Onmaru.Web@{ shape: rounded, label: "Next.js Web" }\n    Onmaru.Ai@{ shape: rectangle, label: "FastAPI AI Server" }\n    Onmaru.Nginx@{ shape: rectangle, label: "Public API Ingress" }\n    Onmaru.Db@{ shape: disk, label: "PostgreSQL" }\n  end\n  Observability@{ shape: rectangle, label: "Grafana Cloud" }\n  Traveler -. "`대화 질문 입력`" .-> Onmaru.Web\n  Admin -. "`선택한 품질 사례 조사·격리 실험 시작`" .-> Onmaru.Ai\n  Gemini -. "`구조화 claim proposal`" .-> Onmaru.Ai\n  Onmaru.Web -. "`API request / SSE connection`" .-> Onmaru.Nginx\n  Onmaru.Spring -. "`저장된 snapshot을 SSE replay`" .-> Onmaru.Web\n  Onmaru.Nginx -. "`proxy API / SSE; buffering disabled`" .-> Onmaru.Spring\n  Onmaru.Spring -. "`[...]`" .-> Onmaru.Ai\n  Onmaru.Spring -. "`정형 사실 조회·대화 저장`" .-> Onmaru.Db\n  Onmaru.Ai -. "`[...]`" .-> Onmaru.Spring\n  Onmaru.Ai -. "`공개 corpus 검색·평가 artifact`" .-> Onmaru.Db\n  Onmaru.Db -. "`[...]`" .-> Onmaru.Ai\n  Onmaru.Spring -. "`root span / low-cardinality metrics`" .-> Observability\n  Onmaru.Ai -. "`근거 제한 생성 요청`" .-> Gemini\n  Onmaru.Ai -. "`child spans / retrieval stage metrics`" .-> Observability\n';case`spring-components`:return`---
title: "3A · Spring 서버 책임"
---
graph TB
  OnmaruAi@{ shape: rectangle, label: "FastAPI AI Server" }
  subgraph OnmaruSpring["\`Spring API Server\`"]
    OnmaruSpring.Authority@{ shape: rectangle, label: "Plan Authority Gate" }
    OnmaruSpring.FinalValidator@{ shape: rectangle, label: "Final Validator" }
    OnmaruSpring.Admission@{ shape: rectangle, label: "Admission & Conversation" }
    OnmaruSpring.SqlExecutor@{ shape: rectangle, label: "Canonical SQL Executor" }
    OnmaruSpring.Persistence@{ shape: rectangle, label: "Run Persistence & SSE" }
    OnmaruSpring.Privacy@{ shape: rectangle, label: "Input Privacy Gate" }
  end
  Observability@{ shape: rectangle, label: "Grafana Cloud" }
  OnmaruDb@{ shape: disk, label: "PostgreSQL" }
  OnmaruWeb@{ shape: rounded, label: "Next.js Web" }
  OnmaruAi -. "\`PlanProposal\`" .-> OnmaruSpring.Authority
  OnmaruAi -. "\`ValidatedProposal\`" .-> OnmaruSpring.FinalValidator
  OnmaruSpring.Admission -. "\`load confirmed context · create safeQuery\`" .-> OnmaruSpring.Privacy
  OnmaruSpring.Authority -. "\`authorize canonical fields\`" .-> OnmaruSpring.SqlExecutor
  OnmaruSpring.FinalValidator -. "\`persist validated snapshot\`" .-> OnmaruSpring.Persistence
  OnmaruSpring.Privacy -. "\`plan request · transient safeQuery\`" .-> OnmaruAi
  OnmaruSpring.Authority -. "\`approved plan · planHash\`" .-> OnmaruAi
  OnmaruSpring.SqlExecutor -. "\`read permitted facts\`" .-> OnmaruDb
  OnmaruSpring.Persistence -. "\`verified SSE / replay\`" .-> OnmaruWeb
  OnmaruSpring.Persistence -. "\`privacy-safe run observation\`" .-> OnmaruAi
  OnmaruSpring -. "\`root span / low-cardinality metrics\`" .-> Observability
`;case`fastapi-components`:return'---\ntitle: "3B · FastAPI AI Engine 내부 모듈"\n---\ngraph TB\n  Admin@{ icon: "fa:user", shape: rounded, label: "운영자" }\n  Gemini@{ shape: rectangle, label: "Gemini API" }\n  OnmaruSpring@{ shape: rectangle, label: "Spring API Server" }\n  OnmaruDb@{ shape: disk, label: "PostgreSQL" }\n  subgraph OnmaruAi["`FastAPI AI Server`"]\n    OnmaruAi.QualityHarness@{ shape: rectangle, label: "Quality Harness" }\n    OnmaruAi.PlanApi@{ shape: rectangle, label: "Plan API" }\n    OnmaruAi.ExecuteApi@{ shape: rectangle, label: "Execute API" }\n    OnmaruAi.CorpusWorker@{ shape: rectangle, label: "Corpus Worker" }\n    OnmaruAi.Normalizer@{ shape: rectangle, label: "Query Normalizer" }\n    OnmaruAi.PlanValidator@{ shape: rectangle, label: "Approved Plan Validator" }\n    OnmaruAi.Planner@{ shape: rectangle, label: "Query Planner & Router" }\n    OnmaruAi.Lexical@{ shape: rectangle, label: "Lexical Retriever" }\n    OnmaruAi.Dense@{ shape: rectangle, label: "Dense Retriever" }\n    OnmaruAi.Fusion@{ shape: rectangle, label: "Fusion & Ranker" }\n    OnmaruAi.Evidence@{ shape: rectangle, label: "Evidence Selector" }\n    OnmaruAi.Prompt@{ shape: rectangle, label: "Prompt Assembler" }\n    OnmaruAi.Generator@{ shape: rectangle, label: "Grounded Generator" }\n    OnmaruAi.ProposalValidator@{ shape: rectangle, label: "Proposal Validator" }\n  end\n  Observability@{ shape: rectangle, label: "Grafana Cloud" }\n  Admin -. "`operator-selected investigation / experiment`" .-> OnmaruAi.QualityHarness\n  Gemini -. "`structured proposal`" .-> OnmaruAi.Generator\n  OnmaruSpring -. "`plan request · transient safeQuery`" .-> OnmaruAi.PlanApi\n  OnmaruSpring -. "`approved plan · planHash`" .-> OnmaruAi.ExecuteApi\n  OnmaruSpring -. "`privacy-safe run observation`" .-> OnmaruAi.QualityHarness\n  OnmaruDb -. "`public projection + rights revision`" .-> OnmaruAi.CorpusWorker\n  OnmaruDb -. "`gold set + expected evidence`" .-> OnmaruAi.QualityHarness\n  OnmaruAi.PlanApi -. "`normalize`" .-> OnmaruAi.Normalizer\n  OnmaruAi.Normalizer -. "`questionFrame`" .-> OnmaruAi.Planner\n  OnmaruAi.ExecuteApi -. "`validate approved envelope`" .-> OnmaruAi.PlanValidator\n  OnmaruAi.PlanValidator -. "`lexical route when requested`" .-> OnmaruAi.Lexical\n  OnmaruAi.PlanValidator -. "`dense route when requested`" .-> OnmaruAi.Dense\n  OnmaruAi.Lexical -. "`ranked candidates`" .-> OnmaruAi.Fusion\n  OnmaruAi.Dense -. "`ranked candidates`" .-> OnmaruAi.Fusion\n  OnmaruAi.Fusion -. "`RRF only for hybrid · rerank`" .-> OnmaruAi.Evidence\n  OnmaruAi.Evidence -. "`EvidenceSet`" .-> OnmaruAi.Prompt\n  OnmaruAi.Prompt -. "`bounded prompt`" .-> OnmaruAi.Generator\n  OnmaruAi.Generator -. "`claim + evidence IDs`" .-> OnmaruAi.ProposalValidator\n  OnmaruAi.Planner -. "`PlanProposal`" .-> OnmaruSpring\n  OnmaruAi.Generator -. "`public evidence only`" .-> Gemini\n  OnmaruAi.ProposalValidator -. "`ValidatedProposal`" .-> OnmaruSpring\n  OnmaruAi.CorpusWorker -. "`inactive revision → validate → activate`" .-> OnmaruDb\n  OnmaruAi.QualityHarness -. "`metrics + review artifact`" .-> OnmaruDb\n  OnmaruAi -. "`child spans / retrieval stage metrics`" .-> Observability\n';case`production-deployment`:return`---
title: "4 · 운영 배포 토폴로지"
---
graph TB
  subgraph ProductionAws["\`aws\`"]
    subgraph ProductionAws.Lightsail2gb["\`lightsail2gb\`"]
      ProductionAws.Lightsail2gb.SpringProcessSpringInstance@{ shape: rectangle, label: "Spring API Server" }
      ProductionAws.Lightsail2gb.NginxNginxInstance@{ shape: rectangle, label: "Public API Ingress" }
      ProductionAws.Lightsail2gb.FastapiProcessAiInstance@{ shape: rectangle, label: "FastAPI AI Server" }
      ProductionAws.Lightsail2gb.PostgresProcessDbInstance@{ shape: disk, label: "PostgreSQL" }
    end
  end
  ProductionGoogleGeminiServiceGeminiInstance@{ shape: rectangle, label: "Gemini API" }
  ProductionVercelWebRuntimeWebInstance@{ shape: rounded, label: "Next.js Web" }
  ProductionGrafanaCloudTelemetryBackendGrafanaInstance@{ shape: rectangle, label: "Grafana Cloud" }
  ProductionVercelWebRuntimeWebInstance -. "\`API request / SSE connection\`" .-> ProductionAws.Lightsail2gb.NginxNginxInstance
  ProductionAws.Lightsail2gb.SpringProcessSpringInstance -. "\`[...]\`" .-> ProductionVercelWebRuntimeWebInstance
  ProductionGoogleGeminiServiceGeminiInstance -. "\`[...]\`" .-> ProductionAws.Lightsail2gb.FastapiProcessAiInstance
  ProductionAws.Lightsail2gb.SpringProcessSpringInstance -. "\`root span / low-cardinality metrics\`" .-> ProductionGrafanaCloudTelemetryBackendGrafanaInstance
  ProductionAws.Lightsail2gb.FastapiProcessAiInstance -. "\`child spans / retrieval stage metrics\`" .-> ProductionGrafanaCloudTelemetryBackendGrafanaInstance
  ProductionAws.Lightsail2gb.NginxNginxInstance -. "\`proxy API / SSE; buffering disabled\`" .-> ProductionAws.Lightsail2gb.SpringProcessSpringInstance
  ProductionAws.Lightsail2gb.SpringProcessSpringInstance -. "\`[...]\`" .-> ProductionAws.Lightsail2gb.FastapiProcessAiInstance
  ProductionAws.Lightsail2gb.SpringProcessSpringInstance -. "\`[...]\`" .-> ProductionAws.Lightsail2gb.PostgresProcessDbInstance
  ProductionAws.Lightsail2gb.FastapiProcessAiInstance -. "\`[...]\`" .-> ProductionAws.Lightsail2gb.PostgresProcessDbInstance
`;case`online-rag-sse`:return`---
title: "5 · 대화형 RAG 요청과 SSE 응답"
---
graph LR
  subgraph Onmaru["\`OnMaru\`"]
    Onmaru.Web@{ shape: rounded, label: "Next.js Web" }
    Onmaru.Nginx@{ shape: rectangle, label: "Public API Ingress" }
    Onmaru.SpringAdmission@{ shape: rectangle, label: "Admission & Conversation" }
    Onmaru.SpringPrivacy@{ shape: rectangle, label: "Input Privacy Gate" }
    Onmaru.SpringAuthority@{ shape: rectangle, label: "Plan Authority Gate" }
    Onmaru.AiPlanApi@{ shape: rectangle, label: "Plan API" }
    Onmaru.AiNormalizer@{ shape: rectangle, label: "Query Normalizer" }
    Onmaru.AiPlanner@{ shape: rectangle, label: "Query Planner & Router" }
    Onmaru.SpringSqlExecutor@{ shape: rectangle, label: "Canonical SQL Executor" }
    Onmaru.DbBusinessSchema@{ shape: rectangle, label: "Business Schema" }
    Onmaru.AiExecuteApi@{ shape: rectangle, label: "Execute API" }
    Onmaru.AiPlanValidator@{ shape: rectangle, label: "Approved Plan Validator" }
    Onmaru.AiLexical@{ shape: rectangle, label: "Lexical Retriever" }
    Onmaru.AiDense@{ shape: rectangle, label: "Dense Retriever" }
    Onmaru.AiFusion@{ shape: rectangle, label: "Fusion & Ranker" }
    Onmaru.AiEvidence@{ shape: rectangle, label: "Evidence Selector" }
    Onmaru.AiPrompt@{ shape: rectangle, label: "Prompt Assembler" }
    Onmaru.AiGenerator@{ shape: rectangle, label: "Grounded Generator" }
    Onmaru.SpringFinalValidator@{ shape: rectangle, label: "Final Validator" }
    Onmaru.AiProposalValidator@{ shape: rectangle, label: "Proposal Validator" }
    Onmaru.SpringPersistence@{ shape: rectangle, label: "Run Persistence & SSE" }
  end
  Gemini@{ shape: rectangle, label: "Gemini API" }
  Onmaru.Web -. "\`HTTPS · create run + open SSE\`" .-> Onmaru.Nginx
  Onmaru.Nginx -. "\`POST /api/v1/journeys/{threadId}/runs\`" .-> Onmaru.SpringAdmission
  Onmaru.SpringAdmission -. "\`authenticate · load confirmed context\`" .-> Onmaru.SpringPrivacy
  Onmaru.SpringPrivacy -. "\`POST /internal/v1/plans · safeQuery\`" .-> Onmaru.AiPlanApi
  Onmaru.AiPlanApi -. "\`normalize questionFrame\`" .-> Onmaru.AiNormalizer
  Onmaru.AiNormalizer -. "\`select route · propose constraints\`" .-> Onmaru.AiPlanner
  Onmaru.AiPlanApi -. "\`PlanProposal\`" .-> Onmaru.SpringAuthority
  Onmaru.SpringAuthority -. "\`execute permitted fields when route needs SQL\`" .-> Onmaru.SpringSqlExecutor
  Onmaru.SpringSqlExecutor -. "\`parameterized SQL · business role\`" .-> Onmaru.DbBusinessSchema
  Onmaru.SpringAuthority -. "\`POST /internal/v1/runs/{id}/execute · approved plan\`" .-> Onmaru.AiExecuteApi
  Onmaru.AiExecuteApi -. "\`verify planHash · corpus/config/revocation\`" .-> Onmaru.AiPlanValidator
  Onmaru.AiPlanValidator -. "\`BM25 when route includes lexical\`" .-> Onmaru.AiLexical
  Onmaru.AiPlanValidator -. "\`384D vector when route includes dense\`" .-> Onmaru.AiDense
  Onmaru.AiLexical -. "\`ranked candidates\`" .-> Onmaru.AiFusion
  Onmaru.AiDense -. "\`ranked candidates\`" .-> Onmaru.AiFusion
  Onmaru.AiFusion -. "\`RRF only when both lists exist · rerank\`" .-> Onmaru.AiEvidence
  Onmaru.AiEvidence -. "\`EvidenceSet · source spans\`" .-> Onmaru.AiPrompt
  Onmaru.AiPrompt -. "\`bounded prompt\`" .-> Onmaru.AiGenerator
  Onmaru.AiGenerator -. "\`grounded structured generation\`" .-> Gemini
  Gemini -. "\`claim/evidence proposal\`" .-> Onmaru.AiProposalValidator
  Onmaru.AiProposalValidator -. "\`ValidatedProposal\`" .-> Onmaru.SpringFinalValidator
  Onmaru.SpringFinalValidator -. "\`rights · claim · filters re-check\`" .-> Onmaru.SpringPersistence
  Onmaru.SpringPersistence -. "\`verified SSE events / replay\`" .-> Onmaru.Nginx
  Onmaru.Nginx -. "\`SSE stream to browser\`" .-> Onmaru.Web
`;case`offline-corpus-quality`:return`---
title: "6 · 오프라인 Corpus와 비동기 Quality Harness"
---
graph LR
  subgraph Onmaru["\`OnMaru\`"]
    Onmaru.Spring@{ shape: rectangle, label: "Spring API Server" }
    Onmaru.DbBusinessSchema@{ shape: rectangle, label: "Business Schema" }
    Onmaru.AiCorpusWorker@{ shape: rectangle, label: "Corpus Worker" }
    Onmaru.DbAiSchema@{ shape: rectangle, label: "AI Corpus Schema" }
    Onmaru.AiQualityHarness@{ shape: rectangle, label: "Quality Harness" }
    Onmaru.DbEvalSchema@{ shape: rectangle, label: "Evaluation Artifacts" }
    Onmaru.AiPlanner@{ shape: rectangle, label: "Query Planner & Router" }
  end
  Admin@{ icon: "fa:user", shape: rounded, label: "운영자" }
  Onmaru.Spring -. "\`versioned public projection · rights/revocation\`" .-> Onmaru.AiCorpusWorker
  Onmaru.AiCorpusWorker -. "\`parse · chunk · enrich · embed · index inactive revision\`" .-> Onmaru.DbAiSchema
  Onmaru.DbBusinessSchema -. "\`public-only source manifest\`" .-> Onmaru.AiCorpusWorker
  Onmaru.AiQualityHarness -. "\`persist run observations · evaluation artifacts\`" .-> Onmaru.DbEvalSchema
  Onmaru.DbEvalSchema -. "\`gold replay · expected evidence\`" .-> Onmaru.AiQualityHarness
  Admin -. "\`select case · start isolated experiment\`" .-> Onmaru.AiQualityHarness
  Onmaru.AiQualityHarness -. "\`candidate config only after human approval\`" .-> Onmaru.AiPlanner
`;default:throw Error(`Unknown viewId: `+e)}};export{e as mmdSource};