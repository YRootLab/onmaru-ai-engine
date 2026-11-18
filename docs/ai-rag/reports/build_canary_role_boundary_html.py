#!/usr/bin/env python3
"""Build a standalone HTML version of the 2026-11-17 canary review."""
from __future__ import annotations

import re
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "2026-11-17-canary-role-boundary-review.md"
OUTPUT = HERE / "2026-11-17-canary-role-boundary-review.html"

LEGACY_DIAGRAM = r"""
<div class="flow legacy-flow" role="img" aria-label="Legacy canary flow: Spring selects at most 12 places before AI runs">
  <div class="node user"><span>01</span><strong>사용자 질문</strong><small>자연어 요청</small></div><i class="arrow">→</i>
  <div class="node spring"><span>02 · Spring</span><strong>후보 SQL</strong><small>지역·분류 기준<br>질문 관련성 순위 없음</small></div><i class="arrow">→</i>
  <div class="node warning"><span>03 · 사전 제한</span><strong>최대 12개</strong><small>장소명 / 공개 ID 순</small></div><i class="arrow">→</i>
  <div class="node ai-muted"><span>04 · AI Engine</span><strong>candidateRefs</strong><small>전달된 ID 안에서<br>생성 결과 선택</small></div>
</div>
<div class="flow-note bad-note"><b>관찰:</b> 일반 추천의 검색 범위를 Spring이 먼저 잘라냅니다. 확인한 Spring 요청 코드에는 <code>useRag=true</code>도 직렬화되지 않습니다.</div>
"""

TARGET_DIAGRAM = r"""
<div class="flow target-flow" role="img" aria-label="Target flow: AI interprets the question and searches its corpus, Spring approves authority and final publication">
  <div class="node user"><span>01</span><strong>사용자 질문</strong><small>세션은 Spring 소유</small></div><i class="arrow">→</i>
  <div class="node spring"><span>02 · Spring</span><strong>인증·비식별화</strong><small>safeQuery + 권한 범위</small></div><i class="arrow">→</i>
  <div class="node ai"><span>03 · AI Engine</span><strong>해석·route 선택</strong><small>QueryFrame<br>SQL / BM25 / vector / hybrid</small></div><i class="arrow">→</i>
  <div class="node spring"><span>04 · Spring</span><strong>authority gate</strong><small>계획 승인·최소 grant</small></div><i class="arrow">→</i>
  <div class="node ai"><span>05 · AI Engine</span><strong>내부 corpus 검색</strong><small>승인 조건 안에서<br>검색·근거 선택</small></div><i class="arrow">→</i>
  <div class="node spring"><span>06 · Spring</span><strong>최종 확인·게시</strong><small>공개/철회·저장·SSE</small></div>
</div>
<div class="flow-note"><b>선택 호출:</b> 정형 업무 정보가 필요할 때만 AI가 Spring의 grant-bound typed <code>PlaceQueryPort</code>를 요청합니다. AI에 임의 SQL이나 업무 DB 자격 증명을 주지 않습니다.</div>
"""

STYLE = r"""
:root{color-scheme:light;--ink:#152538;--muted:#526477;--line:#d9e1e9;--paper:#f4f7fa;--blue:#1267a5;--blue-soft:#e9f4fc;--red:#9f3d35;--red-soft:#fff0ee;--green:#18744c;--green-soft:#eaf7f0;--gold:#9a6400}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.72 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:#086ca9}code{font-size:.9em;background:#edf1f5;border-radius:4px;padding:.12em .35em;overflow-wrap:anywhere}.page{max-width:1180px;margin:auto;padding:28px 28px 80px}.hero{background:linear-gradient(135deg,#102b45,#145987);border-radius:22px;color:white;padding:40px 44px;margin:14px 0 24px;box-shadow:0 16px 40px #183c5924}.eyebrow{letter-spacing:.12em;text-transform:uppercase;font-size:12px;font-weight:750;opacity:.78}.hero h1{font-size:clamp(30px,4vw,48px);line-height:1.2;max-width:920px;margin:12px 0}.hero p{max-width:850px;color:#dcebf5}.meta{display:flex;flex-wrap:wrap;gap:9px;margin-top:22px}.pill{border:1px solid #ffffff55;border-radius:99px;padding:5px 12px;font-size:13px}.links{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0 30px}.links a{background:white;border:1px solid var(--line);border-radius:9px;padding:9px 14px;text-decoration:none;font-weight:650}.verdict{border-left:5px solid #d8a033;background:#fff8e7;padding:18px 22px;border-radius:10px;margin:20px 0 26px}.verdict b{color:#6d4a08}.compare{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:16px 0 34px}.panel{background:white;border:1px solid var(--line);border-radius:16px;padding:22px;min-width:0}.panel h2{font-size:20px;margin:0 0 5px}.panel .sub{color:var(--muted);margin:0 0 18px}.panel.legacy{border-top:4px solid #bd655d}.panel.target{border-top:4px solid #3a9b70}.flow{display:flex;align-items:stretch;gap:7px;overflow-x:auto;padding:4px 2px 10px}.node{flex:1 0 125px;min-height:112px;border:1px solid var(--line);background:#f8fafc;border-radius:11px;padding:11px;display:flex;flex-direction:column;justify-content:center}.node span{font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:700}.node strong{font-size:14px;line-height:1.35;margin:5px 0}.node small{font-size:11px;line-height:1.45;color:var(--muted)}.node.user{background:#f2f4f7}.node.spring{background:var(--blue-soft);border-color:#bfdbef}.node.ai{background:var(--green-soft);border-color:#b9dfc9}.node.warning{background:var(--red-soft);border-color:#efc3bd}.node.warning strong{color:var(--red)}.node.ai-muted{background:#f2f4f7;border-style:dashed}.arrow{align-self:center;color:#8292a2;font-style:normal;font-size:19px}.flow-note{margin-top:9px;padding:12px 14px;border-radius:9px;background:#f0f7f3;color:#315747;font-size:13px}.bad-note{background:var(--red-soft);color:#763d39}.callout{background:white;border:1px solid var(--line);border-radius:14px;padding:20px 24px;margin:20px 0}.callout h2{margin:0 0 8px;font-size:19px}.callout ul{margin:8px 0 0;padding-left:22px}.report{background:white;border:1px solid var(--line);border-radius:18px;padding:30px 42px}.report h2{font-size:26px;line-height:1.32;margin:38px 0 12px;padding-top:8px;border-top:1px solid var(--line)}.report h3{font-size:20px;margin:28px 0 8px}.report p,.report li{color:#293b4e}.report blockquote{margin:18px 0;padding:12px 18px;border-left:4px solid #90aac0;background:#f4f8fb;color:#42586e}.report table{border-collapse:collapse;width:100%;display:block;overflow-x:auto;margin:18px 0}.report th,.report td{border:1px solid var(--line);padding:10px 12px;text-align:left;vertical-align:top}.report th{background:#eef4f8}.report pre{white-space:pre-wrap;word-break:break-word;background:#f2f5f8;padding:16px;border-radius:10px;overflow:auto}.report pre code{background:none;padding:0}.report a{overflow-wrap:anywhere}.report hr{border:0;border-top:1px solid var(--line);margin:30px 0}.footer{color:var(--muted);font-size:13px;text-align:center;padding:24px}
@media(max-width:760px){.page{padding:14px 14px 50px}.hero{padding:28px 22px}.compare{grid-template-columns:1fr}.report{padding:22px 18px}.flow{flex-direction:column;overflow:visible}.node{flex:auto;min-height:75px}.arrow{transform:rotate(90deg);height:15px}}
@media print{body{background:white}.page{max-width:none;padding:0}.hero{box-shadow:none}.links a{color:var(--ink)}.panel,.report{break-inside:avoid;box-shadow:none}.compare{grid-template-columns:1fr 1fr}.flow{overflow:visible}.footer{display:none}}
"""


def main() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    # The comparison is rendered above; retain all prose and tables, while avoiding raw Mermaid syntax in the article.
    article = re.sub(r"```mermaid\s*[\s\S]*?```", "", source)
    article = re.sub(r"^# .+\n", "", article, count=1)
    article = re.sub(r"^> 작성 기준:.*\n", "", article, count=1, flags=re.MULTILINE)
    body = markdown.markdown(article, extensions=["tables", "fenced_code", "sane_lists"])
    html = f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="OnMaru 여정 RAG 카나리와 AI Engine 목표 파이프라인의 역할 경계 비교 보고서"><title>OnMaru 여정 RAG 카나리 역할 경계 진단</title><style>{STYLE}</style></head>
<body><main class="page">
<header class="hero"><div class="eyebrow">OnMaru AI-RAG · Architecture review · 2026-11-17</div><h1>카나리의 12개 장소는<br>AI 검색 결과가 아닙니다</h1><p>Spring E2E 카나리에서 실제로 확인된 legacy 후보 제한 흐름과, 시스템 브리핑이 제시한 AI 소유 검색 파이프라인을 비교합니다.</p><div class="meta"><span class="pill">AI Engine v0.1.8 · 4633dc7</span><span class="pill">Backend develop · 39f2db0</span><span class="pill">설계 진단 · 운영 trace 미확인</span></div></header>
<nav class="links" aria-label="관련 자료"><a href="2026-11-17-canary-role-boundary-review.md">원본 Markdown 보고서</a><a href="2026-10-21-system-briefing.html">2026-10-21 시스템 브리핑</a><a href="../README.md">AI-RAG 문서 색인</a></nav>
<section class="verdict"><b>배포 판단</b><br>현재 확인한 카나리는 Spring이 최대 12개 장소를 먼저 고르고 AI가 그 ID 안에서 제안하는 legacy 경로입니다. 이를 AI Engine 독립 RAG의 운영 검증으로 간주하지 마세요. plan/execute 전환만으로도 충분하지 않습니다. 실제 corpus 검색기·snapshot·생성 경로가 연결되고, 동일 run의 request·logs·image digest로 검증돼야 합니다.</section>
<section class="compare" aria-label="Legacy와 목표 파이프라인 비교">
<article class="panel legacy"><h2>카나리에서 확인한 흐름</h2><p class="sub">Spring이 검색 전에 후보 범위를 결정</p>{LEGACY_DIAGRAM}</article>
<article class="panel target"><h2>시스템 브리핑의 목표 흐름</h2><p class="sub">AI가 질문 해석과 corpus 검색을 소유</p>{TARGET_DIAGRAM}</article>
</section>
<section class="callout"><h2>헷갈리기 쉬운 두 숫자</h2><ul><li><b>최대 12개</b>: legacy 경로에서 Spring이 AI에 전달하기 전에 만든 후보 allowlist입니다.</li><li><b>maxPlaces=5</b>: 검색과 검증을 마친 뒤 사용자에게 제안하는 최종 결과 수 상한입니다.</li><li>AI 독립성은 업무 DB 직접 접근을 뜻하지 않습니다. AI는 자체 corpus를 검색하고, Spring은 권한 승인·정형 조회·최종 게시 검증을 담당합니다.</li></ul></section>
<article class="report">{body}</article>
<footer class="footer">정적 단일 HTML · 외부 JavaScript/CDN 없음 · 인쇄/PDF 저장 가능 · 생성 원본: {SOURCE.name}</footer>
</main></body></html>'''
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(HERE.parent.parent)}")


if __name__ == "__main__":
    main()
