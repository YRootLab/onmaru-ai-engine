#!/usr/bin/env python3
"""Bundle the AI-RAG design corpus into the standalone system briefing HTML.

Requires: Python-Markdown and BeautifulSoup 4. Runtime report needs no dependency.
"""
from __future__ import annotations

import html
import hashlib
import os
import re
import subprocess
import tempfile
from datetime import date
from pathlib import Path
from urllib.parse import unquote, urlsplit

import markdown
from bs4 import BeautifulSoup

REPORT_DIR = Path(__file__).resolve().parent
AI_DIR = REPORT_DIR.parent
REPO = AI_DIR.parent.parent
REPORT = REPORT_DIR / "2026-10-21-system-briefing.html"
START = "<!-- FULL_DESIGN_START -->"
END = "<!-- FULL_DESIGN_END -->"
LAYER_START = "<!-- LAYER_MAP_START -->"
LAYER_END = "<!-- LAYER_MAP_END -->"
MODULE_START = "<!-- MODULE_FLOW_START -->"
MODULE_END = "<!-- MODULE_FLOW_END -->"
DOCS = [
    ("README.md", "설계 진입점·결정 추적", "00 전체 기준"),
    ("prd.md", "제품 PRD·사용자 경험", "01 제품"),
    ("conversation-and-prompt-design.md", "대화형 큐레이션·프롬프트·UI", "01A 대화·답변"),
    ("query-processing.md", "질문 정규화·계획·라우팅", "02 질문 처리"),
    ("question-understanding.md", "질문 사전·부정·다턴", "03 질문 해석"),
    ("architecture.md", "데이터 준비·온라인 RAG", "04 아키텍처"),
    ("module-boundaries-and-pipelines.md", "레이어·모듈·세 파이프라인", "04A 모듈 경계"),
    ("request-lifecycle.md", "run·내부 envelope·SSE·실패", "05 요청 생명주기"),
    ("contracts-and-data.md", "API·저장 모델", "06 계약"),
    ("rag-storage-schema.md", "문서·청크·벡터 스키마", "07 저장"),
    ("corpus-lifecycle-and-gc.md", "revision 보존·철회·GC", "08 데이터 수명"),
    ("grounding-and-review.md", "문장별 근거 검증", "09 근거"),
    ("security-and-abuse.md", "개인정보·오남용 방어", "10 안전"),
    ("evaluation-and-environment-tests.md", "품질 평가·환경 검증", "11 평가"),
    ("operations-and-evaluation.md", "운영·출시 게이트", "12 운영"),
    ("observability-contract.md", "OTel·Grafana 관측 계약", "13 관측"),
    ("repository-split-and-monitoring.md", "저장소 분리·관측 운영 결정", "13A 저장소·관측"),
    ("telemetry-and-harness-schema.md", "관측 스키마·하네스 입력", "13B 관측 스키마"),
    ("quality-engineering-agent.md", "품질 감독 workflow", "14 품질 감독"),
    ("quality-agent-prompt-contracts.md", "Quality Harness prompt·guardrail 계약", "14C 품질 감독"),
    ("../ai-rag-spring/README.md", "Spring 측 AI-RAG 통합", "14A Spring 통합"),
    ("../ai-rag-spring/quality-tools-mcp.md", "Spring Quality MCP tool 계약", "14B Spring 통합"),
    ("../ai-rag-spring/journey-query-mcp.md", "Spring PlaceQueryPort · REST/MCP/gRPC adapter 계약", "14C Spring 통합"),
    ("production-readiness-gaps.md", "미검증 사항·차단 조건", "16 준비도"),
    ("../decisions/0017-home-journey-hybrid-rag.md", "ADR-0017 · 구조 결정", "17 결정"),
    ("../decisions/0018-quality-harness-spring-mcp-tools.md", "ADR-0018 · Spring MCP tools 제안", "17A 결정"),
    ("../decisions/0019-journey-query-mcp-tools.md", "ADR-0019 · 여정 query MCP tools 제안", "17B 결정"),
    ("../operations/runbooks/lightsail-2gb-migration.md", "Lightsail 2GB 이전 절차", "18 인프라"),
    ("../ai/application-architecture.md", "공통 AI 응용 경계", "19 현행 계약"),
    ("../ai/corpus-sync-contract.md", "공통 corpus 동기화 계약", "20 현행 계약"),
    ("../ai/evaluation-harness.md", "현행 AI 평가 harness", "20A 현행 계약"),
    ("../ai/gemini-provider-adapter.md", "Gemini provider adapter", "20B 현행 계약"),
    ("../ai/internal-service-authentication.md", "서비스 간 인증·TLS", "20C 현행 계약"),
    ("../ai/journey-guardrails.md", "현행 여정 guardrails", "21 현행 구현"),
    ("../ai/proposal-validation.md", "현행 proposal 검증", "22 현행 구현"),
]

def key(path: Path) -> str:
    rel = path.relative_to(REPO).with_suffix("")
    return "doc-" + re.sub(r"[^a-z0-9]+", "-", str(rel).lower()).strip("-")

paths = [(REPO / "docs/ai-rag" / rel).resolve() for rel, _, _ in DOCS]
path_to_key = {p: key(p) for p in paths}
DIAGRAM_DIR = REPORT_DIR / "diagrams"
DIAGRAM_DIR.mkdir(exist_ok=True)
subprocess.run(
    ["python3", str(DIAGRAM_DIR / "build_ai_engine_architecture.py")],
    check=True,
)
subprocess.run(
    ["python3", str(DIAGRAM_DIR / "build_quality_harness_architecture.py")],
    check=True,
)
if missing := [str(p) for p in paths if not p.is_file()]:
    raise SystemExit(f"Missing source documents: {missing}")

def render_document(path: Path) -> str:
    source = path.read_text(encoding="utf-8")
    # ADR front matter is metadata, not a prose section.
    if source.startswith("---\n"):
        source = re.sub(r"\A---\n.*?\n---\n", "", source, count=1, flags=re.S)
    body = markdown.markdown(source, extensions=["tables", "fenced_code", "toc", "sane_lists"])
    soup = BeautifulSoup(body, "html.parser")
    prefix = path_to_key[path]
    for heading in soup.find_all(re.compile(r"^h[1-6]$")):
        if heading.get("id"):
            heading["id"] = prefix + "--" + heading["id"]
    for link in soup.find_all("a", href=True):
        raw = link["href"]
        if raw.startswith(("http:", "https:", "mailto:", "tel:")):
            link["target"] = "_blank"
            link["rel"] = "noopener noreferrer"
            continue
        url = urlsplit(raw)
        target = (path.parent / unquote(url.path)).resolve() if url.path else path
        if target in path_to_key:
            link["href"] = "#" + path_to_key[target] + ("--" + unquote(url.fragment) if url.fragment else "")
            link["class"] = list(dict.fromkeys(link.get("class", []) + ["internal-doc-link"]))
        else:
            relative = os.path.relpath(target, REPORT_DIR)
            link["href"] = relative + ("#" + url.fragment if url.fragment else "")
    for image in soup.find_all("img", src=True):
        src = image["src"]
        if not src.startswith(("http:", "https:", "data:")):
            image["src"] = os.path.relpath((path.parent / src).resolve(), REPORT_DIR)
    for n, code in enumerate(soup.select("pre code.language-mermaid"), start=1):
        mermaid_source = code.get_text()
        digest = hashlib.sha256(mermaid_source.encode()).hexdigest()[:16]
        svg_name = f"{path.stem}-{n}-{digest}.svg"
        svg_path = DIAGRAM_DIR / svg_name
        if not svg_path.exists():
            with tempfile.TemporaryDirectory() as tmp:
                input_path = Path(tmp) / "diagram.mmd"
                input_path.write_text(mermaid_source, encoding="utf-8")
                result = subprocess.run(
                    ["mmdc", "-i", str(input_path), "-o", str(svg_path), "-t", "neutral", "-b", "transparent", "-q"],
                    capture_output=True, text=True,
                )
                if result.returncode:
                    raise RuntimeError(f"Mermaid render failed in {path.name} #{n}: {result.stderr}")
        figure = soup.new_tag("figure", attrs={"class": "rendered-diagram"})
        zoom = soup.new_tag("a", href=f"diagrams/{svg_name}", target="_blank", rel="noopener noreferrer", title="다이어그램 크게 열기")
        image = soup.new_tag("img", src=f"diagrams/{svg_name}", alt=f"{path.stem}의 Mermaid 다이어그램 {n}", loading="lazy")
        zoom.append(image)
        figure.append(zoom)
        caption = soup.new_tag("figcaption")
        caption.string = "다이어그램을 누르면 크게 열립니다."
        figure.append(caption)
        source_details = soup.new_tag("details", attrs={"class": "diagram-source"})
        source_summary = soup.new_tag("summary")
        source_summary.string = "Mermaid 원본 보기"
        source_details.append(source_summary)
        pre = code.parent
        pre.replace_with(figure)
        source_details.append(pre)
        figure.append(source_details)
    return str(soup)

html_text = REPORT.read_text(encoding="utf-8")
static_replacements = [
    ("<li>AI 의미 해석 → route 제안</li>", "<li>Query Processing Layer: Preprocessing → Interpretation → Search Router</li>"),
    ("<li>Spring 승인 → SQL 또는 BM25/vector/hybrid 검색</li>", "<li>Spring 승인 → SQL / Keyword Search / Semantic Search / Hybrid Search</li>"),
    ("<div class=\"eyebrow\">03 · Query processing module</div>", "<div class=\"eyebrow\">03 · Query Processing Layer</div>"),
    ("AI 엔진이 수식·부정 관계를 로컬 검색용 <code>semanticQuery</code>에 보존하고 <strong>정규화 → 계획 → 라우팅</strong>합니다.", "AI 엔진은 Query Preprocessing에서 표기·별칭을 정리하고, Query Interpretation에서 의도·대상·조건·부정·대화 맥락을 <code>QueryFrame</code>으로 구성한 뒤 Search Router가 route를 제안합니다. 원문 뉘앙스와 부정 관계는 로컬 검색용 <code>semanticQuery</code>에 보존합니다."),
    ("<strong>AI Query normalization</strong><small>대상·지역·별칭·부정·다턴 맥락</small>", "<strong>Query Preprocessing</strong><small>표기·검수 별칭을 정리하고 의미 보존</small>"),
    ("<div class=\"arrow\">→</div><div class=\"node\"><strong>AI Query planning</strong><small>정형 사실과 공개 본문 분해·route 제안</small></div><div class=\"arrow\">→</div><div class=\"node\"><strong>Spring authority gate</strong>", "<div class=\"arrow\">→</div><div class=\"node\"><strong>Query Interpretation</strong><small>의도·대상·조건·부정·맥락 → QueryFrame</small></div><div class=\"arrow\">→</div><div class=\"node\"><strong>Search Router</strong><small>정형 사실·본문 경로 제안</small></div><div class=\"arrow\">→</div><div class=\"node\"><strong>Spring authority gate</strong>"),
    ("<p>이름·별칭·정확 용어. BM25, vector·RRF 생략.</p>", "<p>Keyword Search(BM25). Semantic Search와 RRF는 생략.</p>"),
    ("<p>승인된 단일 의미 주제. vector, BM25·RRF 생략.</p>", "<p>Semantic Search(Vector). BM25와 RRF는 생략.</p>"),
    ("<p>설명·추천·비교·복합 조건. BM25+vector→RRF.</p>", "<p>설명·추천·비교·복합 조건. Keyword + Semantic Search → Hybrid Fusion(RRF).</p>"),
    ("동일 hard filter · BM25 / vector", "동일 hard filter · Keyword Search / Semantic Search"),
    ("<strong>AI 계획 → Spring 승인</strong><small>질문 해석·route 제안 → 권한·필터 검증</small>", "<strong>Query Processing Layer → Spring 승인</strong><small>Preprocessing → Interpretation → Search Router → 권한·필터 검증</small>"),
]
for old, new in static_replacements:
    if old not in html_text:
        # The report is an input template as well as the generated artifact. Once
        # a replacement has been applied, subsequent builds should remain safe.
        if new in html_text:
            continue
        raise SystemExit(f"Expected report text to update was not found: {old[:100]}")
    html_text = html_text.replace(old, new, 1)
html_text = re.sub(re.escape(START) + r".*?" + re.escape(END), "", html_text, flags=re.S)
html_text = re.sub(re.escape(LAYER_START) + r".*?" + re.escape(LAYER_END), "", html_text, flags=re.S)
html_text = re.sub(re.escape(MODULE_START) + r".*?" + re.escape(MODULE_END), "", html_text, flags=re.S)
html_text = re.sub(r'(<a href="#overview">01 핵심 결정</a>)(?:<a href="#layer-map">레이어·모듈 지도</a>)*', r'\1<a href="#layer-map">레이어·모듈 지도</a>', html_text, count=1)
html_text = re.sub(r'(<a href="#sources">10 원본 문서</a>)(?:<a href="#full-design">11 전체 설계 본문</a>)*', r'\1<a href="#full-design">11 전체 설계 본문</a>', html_text, count=1)
if 'id="full-design"' in html_text:
    raise SystemExit("Unexpected full-design section outside generator markers")
style = """
.full-index{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin:22px 0}.full-index a{display:block;border:1px solid var(--line);border-radius:10px;padding:10px 13px;background:#fff;text-decoration:none;font-size:13px}.full-index a:hover{border-color:var(--green);background:#edf5ea}.full-index small{display:block;color:var(--muted)}.doc-details{margin:13px 0;border:1px solid var(--line);border-radius:15px;background:#fffdf8;overflow:hidden}.doc-details>summary{cursor:pointer;padding:16px 18px;font-weight:800;background:#edf2e9;list-style:none}.doc-details>summary::-webkit-details-marker{display:none}.doc-details>summary:before{content:'＋';display:inline-block;margin-right:10px;color:var(--green)}.doc-details[open]>summary:before{content:'－'}.doc-body{padding:22px 25px 28px;overflow-wrap:anywhere}.doc-body h1{font-size:27px;margin:6px 0 18px}.doc-body h2{font-size:23px;margin:32px 0 12px}.doc-body h3{font-size:19px;margin:24px 0 10px}.doc-body h4{font-size:16px;margin:20px 0 8px}.doc-body p,.doc-body li{font-size:14px;line-height:1.8}.doc-body blockquote{border-left:4px solid #8cac9b;background:#f0f5ef;margin:15px 0;padding:8px 18px;color:#415e51}.doc-body blockquote p{margin:0}.doc-body pre{overflow:auto;background:#132821;color:#e1efe7;border-radius:10px;padding:16px;font-size:12px}.doc-body code{font-size:.9em}.doc-body :not(pre)>code{background:#e8eee8;border-radius:4px;padding:1px 4px}.doc-body table{display:block;overflow-x:auto;margin:15px 0}.doc-body th,.doc-body td{min-width:110px}.doc-body .diagram-label{font-size:11px;color:var(--muted);margin-top:17px}.doc-body .mermaid-source{background:#e6f0e8;color:#204337;border:1px solid #c1d8c7}.doc-source{margin:0;padding:0 25px 20px;font-size:12px}.doc-source a{font-weight:700}.search-row{display:flex;gap:8px;align-items:center;margin:17px 0}.search-row input{width:100%;border:1px solid var(--line);border-radius:10px;padding:11px 14px;font:inherit;background:#fff}.search-row button{border:1px solid var(--line);border-radius:10px;background:#fff;padding:10px 13px;cursor:pointer}.full-count{font-size:12px;color:var(--muted)}@media(max-width:620px){.full-index{grid-template-columns:1fr}.doc-body{padding:18px 15px}.doc-source{padding:0 15px 20px}}
.architecture-track{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:22px 0}.architecture-track .card{border-top:5px solid var(--green)}.architecture-track ol{padding-left:20px;line-height:1.75}.path-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px;margin:18px 0}.path-grid .card{padding:14px}.path-grid h3{font-size:14px}.path-grid p{font-size:12px}.step-chain{display:flex;flex-wrap:wrap;gap:8px;align-items:stretch}.step-chain .node{flex:1 1 145px}.step-chain .arrow{align-self:center}.decision-note{padding:13px 17px;border-left:4px solid var(--green);background:#edf4eb;border-radius:8px;margin:18px 0}.arch-caption{font-size:13px;color:var(--muted)}@media(max-width:950px){.architecture-track{grid-template-columns:1fr}.path-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:600px){.path-grid{grid-template-columns:1fr}}
.flow-legend{display:flex;flex-wrap:wrap;gap:7px;margin:20px 0}.flow-legend span{padding:6px 10px;border-radius:999px;font-size:11px;font-weight:800}.flow-spring{--flow-color:#2b6a55;--flow-tint:#e6f3ea}.flow-ai{--flow-color:#365e9d;--flow-tint:#e9f0fb}.flow-db{--flow-color:#866027;--flow-tint:#f8f0de}.flow-external{--flow-color:#814f78;--flow-tint:#f6eaf3}.flow-fe{--flow-color:#6a7140;--flow-tint:#f3f5e5}.flow-legend span{background:var(--flow-tint);color:var(--flow-color)}.swimboard{border:1px solid var(--line);border-radius:18px;overflow:hidden;background:#fffdf8;margin:18px 0 24px}.swimhead,.swimrow{display:grid;grid-template-columns:46px repeat(5,minmax(0,1fr));gap:7px;padding:10px 12px}.swimhead{background:#173b32;color:#fff;font-size:12px}.swimhead b{text-align:center}.swimrow{border-top:1px solid #e6eae1;min-height:106px;align-items:stretch}.step-num{font-size:12px;color:#65746d;padding-top:14px;text-align:center}.swimcell{border-left:4px solid var(--flow-color);background:var(--flow-tint);border-radius:9px;padding:11px 10px;grid-column:var(--lane)}.swimcell.flow-spring{--lane:2}.swimcell.flow-ai{--lane:3}.swimcell.flow-db{--lane:4}.swimcell.flow-external{--lane:5}.swimcell.flow-fe{--lane:6}.swimcell strong{display:block;color:var(--flow-color);font-size:12px;line-height:1.35}.swimcell small{display:block;color:#34443d;font-size:11px;line-height:1.55;margin:6px 0}.swimcell em{display:block;font-style:normal;color:var(--flow-color);font-size:10px;font-weight:800}.swimcell .optional{font-weight:600;font-size:10px}.flow-transfer{text-align:center;border-top:1px dashed #d2dcd3;background:#f5f8f3;color:#456457;font-size:11px;font-weight:800;padding:6px}.module-secondary{display:grid;grid-template-columns:1fr 1fr;gap:17px}.module-secondary>section{border:1px solid var(--line);border-radius:16px;padding:18px;background:#fffdf8}.module-secondary h3{margin:0 0 14px}.module-chain{display:flex;flex-wrap:wrap;align-items:center;gap:7px}.module-chain div{flex:1 1 135px;border:1px solid var(--line);border-radius:8px;padding:8px;background:#f5f8f3}.module-chain b,.module-chain small{display:block;font-size:11px}.module-chain small{color:var(--muted);line-height:1.4;margin-top:4px}.module-chain span{color:var(--green);font-weight:900}.module-secondary p{font-size:12px;color:var(--muted)}@media(max-width:1000px){.swimboard{overflow-x:auto}.swimhead,.swimrow{min-width:1000px}.module-secondary{grid-template-columns:1fr}}@media(max-width:620px){.swimhead{display:none}.swimhead,.swimrow{min-width:0}.swimrow{display:block;padding:12px}.step-num{display:block;text-align:left;padding:0;margin-bottom:5px}.swimcell{display:block;margin:7px 0}.swimcell:before{content:attr(data-lane);display:block;color:var(--flow-color);font-size:10px;font-weight:900;text-transform:uppercase;letter-spacing:.08em}.flow-transfer{padding:8px}.module-chain{display:block}.module-chain span{display:block;text-align:center;transform:rotate(90deg)}}
.rendered-diagram{margin:20px 0;padding:15px;border:1px solid var(--line);border-radius:14px;background:#fff;overflow:auto}.rendered-diagram img{display:block;width:100%;height:auto;min-width:560px}.rendered-diagram figcaption{font-size:12px;color:var(--muted);margin:7px 0}.diagram-source{font-size:12px}.diagram-source summary{cursor:pointer;color:var(--green);font-weight:700}.diagram-source pre{margin-top:10px}.doc-details[hidden],.full-index a[hidden]{display:none}.layer-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.layer-grid .card{border-top:5px solid var(--green)}.layer-grid ol{font-size:13px;padding-left:20px;margin:8px 0}.layer-grid li{margin:4px 0}@media(max-width:800px){.layer-grid{grid-template-columns:1fr}}
.architecture-map{overflow:visible}.architecture-map img{min-width:0;width:100%;max-width:100%;height:auto}.architecture-key{display:flex;flex-wrap:wrap;gap:10px;margin:12px 0 24px}.architecture-key span{border:1px solid var(--line);border-radius:99px;padding:7px 11px;background:#fff;font-size:12px}.architecture-key b{margin-right:6px}.line-blue{color:#365e9d}.line-green{color:#536d65}.line-amber{color:#ad7b36}.line-purple{color:#886799}
.architecture-detail{margin-top:32px;padding-top:22px;border-top:1px solid var(--line)}.diagram-actions{display:flex;align-items:center;gap:14px;flex-wrap:wrap}.diagram-button{display:inline-block;padding:10px 15px;border-radius:10px;background:#173b32;color:white;text-decoration:none;font-weight:800}.diagram-button:hover{background:#285a4d}.architecture-detail-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin:20px 0}.architecture-detail-grid figure{margin:0;border:1px solid var(--line);border-radius:13px;padding:12px;background:#fff;overflow:auto}.architecture-detail-grid img{display:block;width:100%;height:auto;max-height:680px;object-fit:contain}.architecture-detail-grid figcaption{font-size:12px;color:var(--muted);line-height:1.5;margin-top:9px}@media(max-width:750px){.architecture-detail-grid{grid-template-columns:1fr}}
"""
html_text = re.sub(r"\s*\.full-index\{.*?(?=</style>)", "", html_text, count=1, flags=re.S)
html_text = html_text.replace("</style>", style + "</style>", 1)
index = []
articles = []
for (rel, title, group), path in zip(DOCS, paths):
    anchor = path_to_key[path]
    raw_href = os.path.relpath(path, REPORT_DIR)
    index.append(f'<a href="#{anchor}"><strong>{html.escape(group)} · {html.escape(title)}</strong><small>{html.escape(path.name)}</small></a>')
    articles.append(f'<details class="doc-details" id="{anchor}"><summary>{html.escape(group)} · {html.escape(title)}</summary><div class="doc-body">{render_document(path)}</div><p class="doc-source"><a href="{html.escape(raw_href)}" target="_blank" rel="noopener noreferrer">↗ 원본 Markdown 열기</a></p></details>')
def layer_figure(number: int, title: str, description: str) -> str:
    current = "".join(articles)
    matching = [path for path in DIAGRAM_DIR.glob(f"module-boundaries-and-pipelines-{number}-*.svg") if path.name in current]
    if len(matching) != 1:
        raise RuntimeError(f"Expected one rendered layer diagram #{number}, found {len(matching)}")
    src = "diagrams/" + matching[0].name
    return f'<h3>{title}</h3><p>{description}</p><figure class="rendered-diagram"><a href="{src}" target="_blank" rel="noopener noreferrer"><img src="{src}" alt="{title}" loading="lazy"></a><figcaption>그림을 누르면 확대됩니다.</figcaption></figure>'

layers = f'''{LAYER_START}<section id="layer-map"><div class="eyebrow">Architecture · Layer boundaries</div><h2>세 파이프라인, 분명한 레이어와 소유권</h2><p class="lead">질문에서 바로 검색으로 뛰지 않습니다. Spring이 입력을 비식별화하고 대화·공개 범위를 제시하면 FastAPI의 Query Processing Layer가 질문을 해석하고 Search Router가 계획을 제안합니다. Spring은 권한·필터·정형 필드를 승인합니다. Spring↔FastAPI plan/execute는 private REST 기준선으로 시작하고, trace에서 병목이 확인될 때만 gRPC unary를 비교합니다. PlaceQueryPort는 별도 정형 lookup 경계이며 MCP는 tool discovery용입니다. 오프라인 Corpus 준비와 비동기 품질 감독은 회원 요청과 다른 실행 주기로 움직입니다.</p><div class="layer-grid"><div class="card"><h3>① 데이터 준비</h3><ol><li>공개 원천·권리·revision</li><li>파싱·청킹·metadata</li><li>passage 임베딩·BM25 색인</li><li>manifest 검증·active 전환</li><li>철회 차단·GC·복원</li></ol></div><div class="card"><h3>② 온라인 응답</h3><ol><li>admission·비식별 대화 상태</li><li>Query Preprocessing → Query Interpretation → Search Router</li><li>Spring 승인·query grant 발급</li><li>승인된 경우 Spring typed lookup + AI 내부 검색</li><li>claim 검증·snapshot·SSE</li></ol></div><div class="card"><h3>③ 비동기 품질 감독</h3><ol><li>OTel trace·300문항 gold</li><li>결정적 평가·실패 분류</li><li>검토 큐·Grafana·주간 요약</li><li>운영자 선택 조사·격리 실험</li><li>사람 승인·승격·rollback</li></ol></div></div>{layer_figure(1,'1. 세 파이프라인의 연결','Corpus가 승인된 근거를 공급하고, 온라인 run의 비식별 trace가 품질 감독으로 흘러갑니다. 감독 결과는 현재 run이 아닌 다음 승인된 설정에만 반영됩니다.')}{layer_figure(2,'2. Spring과 FastAPI의 온라인 계층','Spring이 회원·원문·SQL·최종 공개 권한을 소유합니다. FastAPI 안에서 Query Processing Layer가 Search Router까지 계획을 제안하고, route adapter가 승인된 경우에만 Spring PlaceQueryPort를 호출합니다. 두 서비스는 원문 대화를 공유하지 않습니다.')}{layer_figure(3,'3. 질문별 경로의 분기와 합류','첫 출시부터 SQL_ONLY·LEXICAL_ONLY·DENSE_ONLY·HYBRID·SQL_PLUS_RETRIEVAL을 활성화합니다. 정형 query는 승인 grant로 Spring PlaceQueryPort에서 실행합니다. gRPC unary의 첫 비교 대상은 trace에서 병목이 확인된 Spring↔FastAPI plan/execute hop입니다. BM25+Semantic Search는 FastAPI 내부에서 실행해 필요한 경우 RRF·reranker로 결합하며, 복합 질문은 정형 사실과 본문 근거를 최종 snapshot에서 합칩니다.')}{layer_figure(4,'4. 품질 감독의 비동기 흐름','정기 작업은 신호 수집과 검토 큐까지만 자동입니다. 조사·실험은 운영자가 시작하고, 운영 설정·corpus 승격은 사람이 승인합니다.')}<div class="callout"><strong>구현 정본</strong> — 각 레이어·모듈의 입력·출력 artifact, 실패 처리, version 고정, 배포 순서는 <a href="#doc-docs-ai-rag-module-boundaries-and-pipelines">모듈 경계와 세 파이프라인 전체 본문</a>에서 이어서 읽을 수 있습니다.</div></section>{LAYER_END}'''
html_text = html_text.replace('<section id="experience">', layers + '<section id="experience">', 1)
module_flow = (REPORT_DIR / "module-flow.fragment.html").read_text(encoding="utf-8")
html_text = html_text.replace('<section id="overview">', MODULE_START + module_flow + MODULE_END + '<section id="overview">', 1)
full = f'''{START}<section id="full-design"><div class="eyebrow">11 · Complete design corpus</div><h2>설계 문서 전체 본문</h2><p class="lead">AI-RAG 목표 설계, 관련 ADR·이전 절차와 현재 AI 공통 계약을 원문 순서대로 담았습니다. 문서 간 링크는 가능한 경우 이 페이지의 해당 절로 이동합니다. <strong>현행·과거 계약은 새 RAG 목표 계약과 구분해</strong> 현재 동작과 전환 차이를 확인하는 자료로 읽어야 합니다.</p><div class="search-row"><input id="docFilter" type="search" placeholder="문서 제목·본문 검색 (예: RRF, SSE, 철회)" aria-label="설계 문서 검색"><button id="clearFilter" type="button">지우기</button></div><div class="full-count" id="filterCount">{len(paths)}개 문서</div><div class="full-index" id="fullIndex">{''.join(index)}</div>{''.join(articles)}</section>{END}'''
html_text = html_text.replace("<footer>OnMaru AI RAG", full + "<footer>OnMaru AI RAG", 1)
script = """
const docDetails=[...document.querySelectorAll('.doc-details')];function openHash(){const id=decodeURIComponent(location.hash.slice(1));if(!id)return;const target=document.getElementById(id);if(!target)return;const detail=target.closest('.doc-details');if(detail){detail.hidden=false;detail.open=true;setTimeout(()=>target.scrollIntoView({block:'start'}),20)}}window.addEventListener('hashchange',openHash);openHash();
const filter=document.getElementById('docFilter'),count=document.getElementById('filterCount');const docIndex=[...document.querySelectorAll('#fullIndex a')];function applyFilter(){const q=filter.value.trim().toLocaleLowerCase();let shown=0;docDetails.forEach((d,i)=>{const hit=!q||d.textContent.toLocaleLowerCase().includes(q);d.hidden=!hit;docIndex[i].hidden=!hit;if(hit)shown++});count.textContent=shown+' / '+docDetails.length+'개 문서';if(q&&shown===1){const single=docDetails.find(d=>!d.hidden);if(single)single.open=true}}filter.addEventListener('input',applyFilter);document.getElementById('clearFilter').addEventListener('click',()=>{filter.value='';applyFilter();filter.focus()});
"""
html_text = html_text.replace(script, "", 1)
html_text = html_text.replace("</script>", script + "</script>", 1)
html_text = re.sub(r"· (?:갱신 )?\d{4}-\d{2}-\d{2} · 정적 HTML", f"· 갱신 {date.today().isoformat()} · 정적 HTML", html_text)
REPORT.write_text(html_text, encoding="utf-8")
referenced_svgs = set(re.findall(r'diagrams/([A-Za-z0-9_-]+[.]svg)', html_text))
for obsolete in DIAGRAM_DIR.glob("*.svg"):
    if obsolete.name not in referenced_svgs:
        obsolete.unlink()
print(f"Built {REPORT.relative_to(REPO)} with {len(paths)} source documents ({REPORT.stat().st_size:,} bytes)")
