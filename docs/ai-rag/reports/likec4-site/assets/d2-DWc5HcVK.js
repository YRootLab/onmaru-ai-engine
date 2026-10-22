var e=e=>{switch(e){case`index`:return`direction: down

Traveler: {
  label: "여행자"
  shape: c4-person
}
Admin: {
  label: "운영자"
  shape: c4-person
}
Onmaru: {
  label: "OnMaru"
}
Gemini: {
  label: "Gemini API"
}
Observability: {
  label: "Grafana Cloud"
}

Traveler -> Onmaru: "대화 질문 입력"
Admin -> Onmaru: "[...]"
Onmaru -> Gemini: "[...]"
Onmaru -> Observability: "[...]"
Gemini -> Onmaru: "[...]"
`;case`system-context`:return`direction: right

Traveler: {
  label: "여행자"
  shape: c4-person
}
Admin: {
  label: "운영자"
  shape: c4-person
}
Onmaru: {
  label: "OnMaru"
}
Gemini: {
  label: "Gemini API"
}
Observability: {
  label: "Grafana Cloud"
}

Traveler -> Onmaru: "대화 질문 입력"
Admin -> Onmaru: "[...]"
Onmaru -> Gemini: "[...]"
Onmaru -> Observability: "[...]"
Gemini -> Onmaru: "[...]"
`;case`service-containers`:return`direction: right

Traveler: {
  label: "여행자"
  shape: c4-person
}
Admin: {
  label: "운영자"
  shape: c4-person
}
Gemini: {
  label: "Gemini API"
}
Onmaru: {
  label: "OnMaru"

  Spring: {
    label: "Spring API Server"
  }
  Web: {
    label: "Next.js Web"
  }
  Ai: {
    label: "FastAPI AI Server"
  }
  Nginx: {
    label: "Public API Ingress"
  }
  Db: {
    label: "PostgreSQL"
    shape: stored_data
  }
}
Observability: {
  label: "Grafana Cloud"
}

Traveler -> Onmaru.Web: "대화 질문 입력"
Admin -> Onmaru.Ai: "선택한 품질 사례 조사·격리 실험 시작"
Gemini -> Onmaru.Ai: "구조화 claim proposal"
Onmaru.Web -> Onmaru.Nginx: "API request / SSE connection"
Onmaru.Spring -> Onmaru.Web: "저장된 snapshot을 SSE replay"
Onmaru.Nginx -> Onmaru.Spring: "proxy API / SSE; buffering disabled"
Onmaru.Spring -> Onmaru.Ai: "[...]"
Onmaru.Spring -> Onmaru.Db: "정형 사실 조회·대화 저장"
Onmaru.Ai -> Onmaru.Spring: "[...]"
Onmaru.Ai -> Onmaru.Db: "공개 corpus 검색·평가 artifact"
Onmaru.Db -> Onmaru.Ai: "[...]"
Onmaru.Spring -> Observability: "root span / low-cardinality metrics"
Onmaru.Ai -> Gemini: "근거 제한 생성 요청"
Onmaru.Ai -> Observability: "child spans / retrieval stage metrics"
`;case`spring-components`:return`direction: down

OnmaruAi: {
  label: "FastAPI AI Server"
}
OnmaruSpring: {
  label: "Spring API Server"

  Authority: {
    label: "Plan Authority Gate"
  }
  FinalValidator: {
    label: "Final Validator"
  }
  Admission: {
    label: "Admission & Conversation"
  }
  SqlExecutor: {
    label: "Canonical SQL Executor"
  }
  Persistence: {
    label: "Run Persistence & SSE"
  }
  Privacy: {
    label: "Input Privacy Gate"
  }
}
Observability: {
  label: "Grafana Cloud"
}
OnmaruDb: {
  label: "PostgreSQL"
  shape: stored_data
}
OnmaruWeb: {
  label: "Next.js Web"
}

OnmaruAi -> OnmaruSpring.Authority: "PlanProposal"
OnmaruAi -> OnmaruSpring.FinalValidator: "ValidatedProposal"
OnmaruSpring.Admission -> OnmaruSpring.Privacy: "load confirmed context · create safeQuery"
OnmaruSpring.Authority -> OnmaruSpring.SqlExecutor: "authorize canonical fields"
OnmaruSpring.FinalValidator -> OnmaruSpring.Persistence: "persist validated snapshot"
OnmaruSpring.Privacy -> OnmaruAi: "plan request · transient safeQuery"
OnmaruSpring.Authority -> OnmaruAi: "approved plan · planHash"
OnmaruSpring.SqlExecutor -> OnmaruDb: "read permitted facts"
OnmaruSpring.Persistence -> OnmaruWeb: "verified SSE / replay"
OnmaruSpring.Persistence -> OnmaruAi: "privacy-safe run observation"
OnmaruSpring -> Observability: "root span / low-cardinality metrics"
`;case`fastapi-components`:return`direction: down

Admin: {
  label: "운영자"
  shape: c4-person
}
Gemini: {
  label: "Gemini API"
}
OnmaruSpring: {
  label: "Spring API Server"
}
OnmaruDb: {
  label: "PostgreSQL"
  shape: stored_data
}
OnmaruAi: {
  label: "FastAPI AI Server"

  QualityHarness: {
    label: "Quality Harness"
  }
  PlanApi: {
    label: "Plan API"
  }
  ExecuteApi: {
    label: "Execute API"
  }
  CorpusWorker: {
    label: "Corpus Worker"
  }
  QueryProcessing: {
    label: "Query Processing Layer"
  }
  PlanValidator: {
    label: "Approved Plan Validator"
  }
  Lexical: {
    label: "Keyword Search"
  }
  Dense: {
    label: "Semantic Search"
  }
  Fusion: {
    label: "Hybrid Fusion"
  }
  Reranker: {
    label: "Reranker"
  }
  Evidence: {
    label: "Evidence Selector"
  }
  Prompt: {
    label: "Prompt Assembler"
  }
  Generator: {
    label: "Grounded Generator"
  }
  ProposalValidator: {
    label: "Proposal Validator"
  }
}
Observability: {
  label: "Grafana Cloud"
}

Admin -> OnmaruAi.QualityHarness: "operator-selected investigation / experiment"
Gemini -> OnmaruAi.Generator: "structured proposal"
OnmaruSpring -> OnmaruAi.PlanApi: "plan request · transient safeQuery"
OnmaruSpring -> OnmaruAi.ExecuteApi: "approved plan · planHash"
OnmaruSpring -> OnmaruAi.QualityHarness: "privacy-safe run observation"
OnmaruDb -> OnmaruAi.CorpusWorker: "public projection + rights revision"
OnmaruDb -> OnmaruAi.QualityHarness: "gold set + expected evidence"
OnmaruAi.PlanApi -> OnmaruAi.QueryProcessing: "preprocess safeQuery"
OnmaruAi.ExecuteApi -> OnmaruAi.PlanValidator: "validate approved envelope"
OnmaruAi.PlanValidator -> OnmaruAi.Lexical: "keyword route when requested"
OnmaruAi.PlanValidator -> OnmaruAi.Dense: "semantic route when requested"
OnmaruAi.Lexical -> OnmaruAi.Fusion: "ranked candidates"
OnmaruAi.Lexical -> OnmaruAi.Reranker: "single Keyword Search route bypasses fusion"
OnmaruAi.Dense -> OnmaruAi.Fusion: "ranked candidates"
OnmaruAi.Dense -> OnmaruAi.Reranker: "single Semantic Search route bypasses fusion"
OnmaruAi.Fusion -> OnmaruAi.Reranker: "RRF-ranked hybrid candidates"
OnmaruAi.Reranker -> OnmaruAi.Evidence: "reranked candidates"
OnmaruAi.Evidence -> OnmaruAi.Prompt: "EvidenceSet"
OnmaruAi.Prompt -> OnmaruAi.Generator: "bounded prompt"
OnmaruAi.Generator -> OnmaruAi.ProposalValidator: "claim + evidence IDs"
OnmaruAi.QueryProcessing -> OnmaruSpring: "PlanProposal"
OnmaruAi.Generator -> Gemini: "public evidence only"
OnmaruAi.ProposalValidator -> OnmaruSpring: "ValidatedProposal"
OnmaruAi.CorpusWorker -> OnmaruDb: "inactive revision → validate → activate"
OnmaruAi.QualityHarness -> OnmaruDb: "metrics + review artifact"
OnmaruAi -> Observability: "child spans / retrieval stage metrics"
`;case`production-deployment`:return`direction: down

ProductionAws: {
  label: "aws"

  Lightsail2gb: {
    label: "lightsail2gb"

    SpringProcessSpringInstance: {
      label: "Spring API Server"
    }
    NginxNginxInstance: {
      label: "Public API Ingress"
    }
    FastapiProcessAiInstance: {
      label: "FastAPI AI Server"
    }
    PostgresProcessDbInstance: {
      label: "PostgreSQL"
      shape: stored_data
    }
  }
}
ProductionGoogleGeminiServiceGeminiInstance: {
  label: "Gemini API"
}
ProductionVercelWebRuntimeWebInstance: {
  label: "Next.js Web"
}
ProductionGrafanaCloudTelemetryBackendGrafanaInstance: {
  label: "Grafana Cloud"
}

ProductionVercelWebRuntimeWebInstance -> ProductionAws.Lightsail2gb.NginxNginxInstance: "API request / SSE connection"
ProductionAws.Lightsail2gb.SpringProcessSpringInstance -> ProductionVercelWebRuntimeWebInstance: "[...]"
ProductionGoogleGeminiServiceGeminiInstance -> ProductionAws.Lightsail2gb.FastapiProcessAiInstance: "[...]"
ProductionAws.Lightsail2gb.SpringProcessSpringInstance -> ProductionGrafanaCloudTelemetryBackendGrafanaInstance: "root span / low-cardinality metrics"
ProductionAws.Lightsail2gb.FastapiProcessAiInstance -> ProductionGrafanaCloudTelemetryBackendGrafanaInstance: "child spans / retrieval stage metrics"
ProductionAws.Lightsail2gb.NginxNginxInstance -> ProductionAws.Lightsail2gb.SpringProcessSpringInstance: "proxy API / SSE; buffering disabled"
ProductionAws.Lightsail2gb.SpringProcessSpringInstance -> ProductionAws.Lightsail2gb.FastapiProcessAiInstance: "[...]"
ProductionAws.Lightsail2gb.SpringProcessSpringInstance -> ProductionAws.Lightsail2gb.PostgresProcessDbInstance: "[...]"
ProductionAws.Lightsail2gb.FastapiProcessAiInstance -> ProductionAws.Lightsail2gb.PostgresProcessDbInstance: "[...]"
`;case`online-rag-sse`:return`direction: right

Onmaru: {
  label: "OnMaru"

  Web: {
    label: "Next.js Web"
  }
  Nginx: {
    label: "Public API Ingress"
  }
  SpringAdmission: {
    label: "Admission & Conversation"
  }
  SpringPrivacy: {
    label: "Input Privacy Gate"
  }
  AiPlanApi: {
    label: "Plan API"
  }
  AiQueryProcessingPreprocessing: {
    label: "Query Preprocessing"
  }
  AiQueryProcessingInterpretation: {
    label: "Query Interpretation"
  }
  SpringAuthority: {
    label: "Plan Authority Gate"
  }
  AiQueryProcessingSearchRouter: {
    label: "Search Router"
  }
  SpringSqlExecutor: {
    label: "Canonical SQL Executor"
  }
  DbBusinessSchema: {
    label: "Business Schema"
  }
  AiExecuteApi: {
    label: "Execute API"
  }
  AiPlanValidator: {
    label: "Approved Plan Validator"
  }
  AiLexical: {
    label: "Keyword Search"
  }
  AiDense: {
    label: "Semantic Search"
  }
  AiFusion: {
    label: "Hybrid Fusion"
  }
  AiReranker: {
    label: "Reranker"
  }
  AiEvidence: {
    label: "Evidence Selector"
  }
  AiPrompt: {
    label: "Prompt Assembler"
  }
  AiGenerator: {
    label: "Grounded Generator"
  }
  SpringFinalValidator: {
    label: "Final Validator"
  }
  AiProposalValidator: {
    label: "Proposal Validator"
  }
  SpringPersistence: {
    label: "Run Persistence & SSE"
  }
}
Gemini: {
  label: "Gemini API"
}

Onmaru.Web -> Onmaru.Nginx: "HTTPS · create run + open SSE"
Onmaru.Nginx -> Onmaru.SpringAdmission: "POST /api/v1/journeys/{threadId}/runs"
Onmaru.SpringAdmission -> Onmaru.SpringPrivacy: "authenticate · load confirmed context"
Onmaru.SpringPrivacy -> Onmaru.AiPlanApi: "POST /internal/v1/plans · safeQuery"
Onmaru.AiPlanApi -> Onmaru.AiQueryProcessingPreprocessing: "Query Preprocessing"
Onmaru.AiQueryProcessingPreprocessing -> Onmaru.AiQueryProcessingInterpretation: "Query Interpretation"
Onmaru.AiQueryProcessingInterpretation -> Onmaru.AiQueryProcessingSearchRouter: "QueryFrame"
Onmaru.AiQueryProcessingSearchRouter -> Onmaru.SpringAuthority: "PlanProposal"
Onmaru.SpringAuthority -> Onmaru.SpringSqlExecutor: "execute permitted fields when route needs SQL"
Onmaru.SpringSqlExecutor -> Onmaru.DbBusinessSchema: "parameterized SQL · business role"
Onmaru.SpringAuthority -> Onmaru.AiExecuteApi: "POST /internal/v1/runs/{id}/execute · approved plan"
Onmaru.AiExecuteApi -> Onmaru.AiPlanValidator: "verify planHash · corpus/config/revocation"
Onmaru.AiPlanValidator -> Onmaru.AiLexical: "Keyword Search · BM25 when requested"
Onmaru.AiPlanValidator -> Onmaru.AiDense: "Semantic Search · 384D when requested"
Onmaru.AiLexical -> Onmaru.AiFusion: "ranked candidates"
Onmaru.AiDense -> Onmaru.AiFusion: "ranked candidates"
Onmaru.AiFusion -> Onmaru.AiReranker: "Hybrid Fusion · RRF only when both lists exist"
Onmaru.AiReranker -> Onmaru.AiEvidence: "Reranker · reranked candidates"
Onmaru.AiEvidence -> Onmaru.AiPrompt: "EvidenceSet · source spans"
Onmaru.AiPrompt -> Onmaru.AiGenerator: "bounded prompt"
Onmaru.AiGenerator -> Gemini: "grounded structured generation"
Gemini -> Onmaru.AiProposalValidator: "claim/evidence proposal"
Onmaru.AiProposalValidator -> Onmaru.SpringFinalValidator: "ValidatedProposal"
Onmaru.SpringFinalValidator -> Onmaru.SpringPersistence: "rights · claim · filters re-check"
Onmaru.SpringPersistence -> Onmaru.Nginx: "verified SSE events / replay"
Onmaru.Nginx -> Onmaru.Web: "SSE stream to browser"
`;case`offline-corpus-quality`:return`direction: right

Onmaru: {
  label: "OnMaru"

  Spring: {
    label: "Spring API Server"
  }
  DbBusinessSchema: {
    label: "Business Schema"
  }
  AiCorpusWorker: {
    label: "Corpus Worker"
  }
  DbAiSchema: {
    label: "AI Corpus Schema"
  }
  AiQualityHarness: {
    label: "Quality Harness"
  }
  DbEvalSchema: {
    label: "Evaluation Artifacts"
  }
  AiQueryProcessingSearchRouter: {
    label: "Search Router"
  }
}
Admin: {
  label: "운영자"
  shape: c4-person
}

Onmaru.Spring -> Onmaru.AiCorpusWorker: "versioned public projection · rights/revocation"
Onmaru.AiCorpusWorker -> Onmaru.DbAiSchema: "parse · chunk · enrich · embed · index inactive revision"
Onmaru.DbBusinessSchema -> Onmaru.AiCorpusWorker: "public-only source manifest"
Onmaru.AiQualityHarness -> Onmaru.DbEvalSchema: "persist run observations · evaluation artifacts"
Onmaru.DbEvalSchema -> Onmaru.AiQualityHarness: "gold replay · expected evidence"
Admin -> Onmaru.AiQualityHarness: "select case · start isolated experiment"
Onmaru.AiQualityHarness -> Onmaru.AiQueryProcessingSearchRouter: "candidate config only after human approval"
`;default:throw Error(`Unknown viewId: `+e)}};export{e as d2Source};