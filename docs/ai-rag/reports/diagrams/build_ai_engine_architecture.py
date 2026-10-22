#!/usr/bin/env python3
"""Render the fixed-layout AI Engine module map as a standalone SVG."""
from pathlib import Path
from html import escape

OUT = Path(__file__).with_name('ai-engine-architecture.svg')
parts = []

def add(value):
    parts.append(value)

def rect(x, y, w, h, fill, stroke, radius=18, stroke_width=2):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>')

def label(x, y, value, size=16, weight=600, color='#253342', anchor='start'):
    add(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{escape(value)}</text>')

def module(x, y, w, h, title, subtitle, border='#9bb5bd', fill='#ffffff'):
    rect(x,y,w,h,fill,border,11,1.5)
    label(x+15,y+27,title,16,700)
    label(x+15,y+49,subtitle,12,400,'#536572')

def edge(d, color='#3d6ea2', width=2.5, dash=None, marker='arrow'):
    dash_attr=f' stroke-dasharray="{dash}"' if dash else ''
    add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"{dash_attr} marker-end="url(#{marker})"/>')

add('''<svg xmlns="http://www.w3.org/2000/svg" width="1850" height="1050" viewBox="0 0 1850 1050" role="img" aria-labelledby="title desc">
<title id="title">OnMaru AI Engine 레이어별 모듈 아키텍처</title>
<desc id="desc">클라이언트에서 Spring Boot로 질문을 보내고, AWS Lightsail 안의 Spring Boot가 AI Engine의 계획과 실행을 승인한다. AI Engine은 PostgreSQL의 정형 장소와 검색 corpus를 사용하고 Gemini에서 근거 기반 제안을 받아 Spring으로 보낸다. Spring의 검증된 답변은 SSE로 클라이언트에 전달된다. 하단에는 오프라인 corpus와 비동기 품질 하네스가 분리되어 있다.</desc>
<defs>
  <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto" markerUnits="userSpaceOnUse"><path d="M1 1 L9 5 L1 9" fill="none" stroke="#3d6ea2" stroke-width="1.8"/></marker>
  <marker id="greenarrow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto" markerUnits="userSpaceOnUse"><path d="M1 1 L9 5 L1 9" fill="none" stroke="#527b65" stroke-width="1.8"/></marker>
  <marker id="amberarrow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto" markerUnits="userSpaceOnUse"><path d="M1 1 L9 5 L1 9" fill="none" stroke="#ad7b36" stroke-width="1.8"/></marker>
  <marker id="purplearrow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto" markerUnits="userSpaceOnUse"><path d="M1 1 L9 5 L1 9" fill="none" stroke="#8666a3" stroke-width="1.8"/></marker>
</defs>
<style>text{font-family:'Noto Sans KR','Apple SD Gothic Neo',sans-serif} .small{font-size:12px}</style>
<rect width="1850" height="1050" fill="#f9faf7"/>
''')
label(45,55,'OnMaru AI Engine · 레이어와 모듈 관계도',30,800,'#172d30')
label(45,83,'목표 설계 · 온라인 요청, corpus 준비, 품질 감독을 분리한 논리 아키텍처',15,400,'#586a70')

# Parent boundaries, with generous margins to avoid crop at report width.
rect(30,120,215,830,'#eff4ed','#c6dac9',20)
label(50,159,'CLIENT',19,800,'#285b43')
label(50,182,'Next.js · 브라우저',13,500,'#557366')
rect(270,120,1290,830,'#edf2fa','#a8c1e5',22,2.5)
label(292,160,'AWS LIGHTSAIL · OnMaru 운영 인스턴스',20,800,'#2a5089')
label(292,184,'한 인스턴스에 별도 서버 프로세스 2개 + PostgreSQL 공존 · 저장소와 배포 산출물 분리 목표',13,500,'#587098')

# Service containers.
rect(292,215,280,505,'#e4f3e8','#a7cbb3',18)
label(312,250,'SPRING SERVER',17,800,'#276044')
label(312,272,'Spring Boot · BE 저장소 · API/SSE',13,500,'#467b5d')
rect(600,215,620,505,'#e6eefc','#a2bcea',18)
label(620,250,'FASTAPI SERVER · AI ENGINE',17,800,'#315d9e')
label(620,272,'onmaru-ai-engine 저장소 · plan/execute private REST 기준선',13,500,'#607eb1')
rect(1246,215,290,505,'#f9f0de','#dccb9c',18)
label(1266,250,'DATA LAYER',17,800,'#795b27')
label(1266,272,'PostgreSQL · PostGIS · pgvector',13,500,'#9a7842')

# Client modules.
module(50,290,175,78,'질문·대화','조건 · 후속 질문',border='#b4cfbc')
module(50,610,175,78,'결과·장소 카드','출처 · 찜 · 이어가기',border='#b4cfbc')

# Spring modules, vertically aligned to interaction phases.
module(312,290,240,65,'Admission + Privacy','인증 · 한도 · safeQuery',border='#93bda2')
module(312,385,240,65,'PlanAuthorityGate','route · 필터 · ID 승인',border='#93bda2')
module(312,472,240,58,'PlaceQueryPort inbound adapter','private REST 기본 · MCP 선택',border='#93bda2')
module(312,542,240,64,'PlaceQueryPort + Service','grant 검증 · 고정 query',border='#93bda2')
module(312,632,240,60,'FinalValidator + SSE','claim · 권리 · 저장 · 전송',border='#93bda2')

# AI sub-layers: compact but not tangled.
rect(620,290,580,150,'#f8fbff','#b9cdee',12,1.5)
label(638,317,'01 · QUERY PROCESSING LAYER',13,800,'#4265a2')
module(638,330,174,82,'Query Preprocessing','표기 · 검수 별칭 정리',border='#a7bce1')
module(823,330,174,82,'Query Interpretation','조건 · 부정 · 맥락',border='#a7bce1')
module(1008,330,174,82,'Search Router','5개 route 제안',border='#a7bce1')
rect(620,460,580,130,'#f8fbff','#b9cdee',12,1.5)
label(638,488,'02 · RETRIEVAL & RANKING',13,800,'#4265a2')
module(638,505,245,65,'Keyword + Semantic Search','BM25 · 384D vector',border='#a7bce1')
module(895,505,135,65,'Hybrid Fusion','RRF',border='#a7bce1')
module(1040,505,140,65,'Reranker','후보 재채점',border='#a7bce1')
rect(620,610,580,105,'#f8fbff','#b9cdee',12,1.5)
label(638,638,'03 · GROUNDED GENERATION',13,800,'#4265a2')
module(638,650,260,55,'PromptAssembler','근거 제한 템플릿',border='#a7bce1')
module(920,650,260,55,'ProposalValidator','claim ↔ evidence ID',border='#a7bce1')

# Storage and provider.
module(1266,290,250,72,'업무 schema / PostGIS','회원 대화 · 정형 장소',border='#d3bd85')
module(1266,390,250,85,'AI corpus schema','청크 · BM25 · pgvector',border='#d3bd85')
module(1266,505,250,72,'평가 artifact','gold · trace · version',border='#d3bd85')
rect(1582,560,245,160,'#f9f2fa','#c9a9ca',16,2)
label(1601,595,'EXTERNAL PROVIDER',16,800,'#795487')
module(1601,618,207,72,'Gemini API','구조화 claim 제안',border='#c9a9ca',fill='#ffffff')

# Main request lines. Short, separate corridors and explicit labels.
edge('M225 328 H302')
label(235,314,'질문',12,600,'#315e96')
edge('M552 322 H628')
label(565,308,'safeQuery',12,600,'#315e96')
edge('M812 371 H817',marker='greenarrow',color='#527b65')
edge('M997 371 H1002',marker='greenarrow',color='#527b65')
edge('M1095 412 V425 H590 V418 H560')
label(739,445,'PlanProposal → Spring 승인',12,600,'#315e96')
edge('M552 432 H590 V535 H628')
label(566,481,'ApprovedPlan',12,600,'#315e96')
edge('M638 548 H580 V501 H560',marker='greenarrow',color='#527b65')
label(578,490,'queryGrant',10,600,'#527b65')
edge('M552 574 H600 V570 H628',marker='greenarrow',color='#527b65')
label(587,585,'PlaceLookupResult',10,600,'#527b65')
edge('M432 530 V537',marker='greenarrow',color='#527b65')
edge('M883 537 H889',marker='greenarrow',color='#527b65')
edge('M1030 537 H1034',marker='greenarrow',color='#527b65')
edge('M1110 570 V601 H766 V643',marker='greenarrow',color='#527b65')
label(870,599,'EvidenceSet',12,600,'#527b65')
edge('M898 677 H910',marker='greenarrow',color='#527b65')
edge('M1180 675 H1565 V654 H1591',marker='greenarrow',color='#527b65')
label(1290,664,'공개 근거만 외부 호출',12,600,'#527b65')
edge('M1601 689 H1568 V704 H1190 V690 H1180',marker='greenarrow',color='#527b65')
label(1330,701,'구조화 제안',11,600,'#527b65')
edge('M920 704 H585 V662 H560')
label(700,719,'ValidatedProposal → Spring 최종 검사',12,600,'#315e96')
edge('M302 662 H235')
label(246,646,'확정 답변 · SSE',12,700,'#315e96')

# Data dependencies terminate at container edges; no crossing the AI submodules.
edge('M552 574 H583 V205 H1238 V326 H1256',color='#ad7b36',marker='amberarrow',width=1.7,dash='5 5')
label(840,200,'Spring PlaceQueryPort → fixed query → 업무 schema',11,600,'#986e36')
edge('M1180 537 H1229 V432 H1256',color='#ad7b36',marker='amberarrow',width=1.7)
label(1203,488,'corpus',11,600,'#986e36')

# Offline and quality module groups, below online modules.
rect(292,765,595,150,'#fff5e8','#dfbf90',14,1.6)
label(312,798,'04 · CORPUS PIPELINE  |  오프라인',16,800,'#88602f')
module(312,820,175,67,'SourceAdapter','권리 · revision · 철회',border='#d9b680')
module(502,820,175,67,'Parser + Chunker','본문 · 출처 metadata',border='#d9b680')
module(692,820,175,67,'Embed + Index','384D · BM25 색인',border='#d9b680')
edge('M487 854 H495',color='#ad7b36',marker='amberarrow',width=1.8)
edge('M677 854 H685',color='#ad7b36',marker='amberarrow',width=1.8)
rect(910,765,626,150,'#f5eef8','#cbb7d9',14,1.6)
label(930,798,'05 · QUALITY HARNESS  |  비동기',16,800,'#78558f')
module(930,820,175,67,'OTel + Gold Replay','trace · 합성 질문',border='#c6aed5')
module(1118,820,175,67,'Evaluation Analyzer','Recall@K · MRR · nDCG',border='#c6aed5')
module(1306,820,210,67,'Review + Experiment','검토 큐 · 사람 승인',border='#c6aed5')
edge('M1105 854 H1111',color='#8666a3',marker='purplearrow',width=1.8)
edge('M1293 854 H1299',color='#8666a3',marker='purplearrow',width=1.8)
edge('M867 854 H890 V747 H1238 V432 H1256',color='#ad7b36',marker='amberarrow',width=1.8)
label(916,742,'검증 후 active revision 승격',11,600,'#986e36')

# Simple offline / quality inputs, kept outside main request corridors.
edge('M1390 577 V735 H980 V811',color='#8666a3',marker='purplearrow',width=1.6,dash='5 5')
edge('M1060 715 V811',color='#8666a3',marker='purplearrow',width=1.6,dash='5 5')
label(294,985,'실선: 온라인 호출·데이터 전달   ·   주황 점선: 오프라인 색인   ·   보라 점선: 비동기 평가',14,500,'#5b6d75')
add('</svg>')
OUT.write_text('\n'.join(parts), encoding='utf-8')
print(f'Built {OUT}')
