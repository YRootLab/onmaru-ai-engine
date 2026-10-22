#!/usr/bin/env python3
"""Build the detailed, deterministic-first Quality Harness workflow SVG."""
from html import escape
from pathlib import Path

OUT = Path(__file__).with_name("quality-harness-architecture.svg")
W, H = 1900, 980
parts = []


def add(s):
    parts.append(s)


def text(x, y, value, size=17, weight=500, color="#263942", anchor="start"):
    add(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{escape(value)}</text>')


def box(x, y, w, h, title, subtitle, lines, fill="#fff", stroke="#9a80b0"):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    text(x + 18, y + 34, title, 19, 800, "#513c62")
    text(x + 18, y + 58, subtitle, 13, 600, "#695778")
    compact = h < 150
    start_y, step = (y + 72, 21) if compact else (y + 98, 25)
    for i, line in enumerate(lines):
        text(x + 18, start_y + step * i, line, 13 if compact else 14, 500, "#35454d")


def arrow(x1, y1, x2, y2, label=None, color="#80609a", dashed=False):
    dash = ' stroke-dasharray="7 7"' if dashed else ""
    add(f'<path d="M{x1} {y1} L{x2} {y2}" fill="none" stroke="{color}" stroke-width="2.4"{dash} marker-end="url(#arrow)"/>')
    if label:
        text((x1 + x2) / 2, (y1 + y2) / 2 - 10, label, 12, 600, color, "middle")


add(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">
<title id="title">OnMaru Quality Harness · 다섯 책임으로 구성한 비동기 품질 개선 흐름</title>
<desc id="desc">비동기 trace와 고정 gold 평가를 Evaluation Analyzer가 결정적으로 분류한다. 운영자가 검토 큐에서 사례를 선택한 뒤 Root Cause Investigator와 Experiment Planner를 실행할 수 있다. 결정적 격리 실험 결과를 Human Review Gate가 검토하고 승인된 경우에만 설정 승격 절차로 전달한다. 자동 LLM 호출이나 운영 중 설정 변경은 없다.</desc>
<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M1 1 L9 5 L1 9" fill="none" stroke="#80609a" stroke-width="1.8"/></marker></defs>
<style>text{{font-family:'Noto Sans KR','Apple SD Gothic Neo',sans-serif}}</style>
<rect width="100%" height="100%" fill="#faf9fc"/>
''')
text(52, 58, "QUALITY HARNESS · 품질 감독과 개선 실험", 30, 800, "#342640")
text(52, 91, "비동기 · 결정적 분석 우선 · 운영자가 조사와 실험을 시작 · 사람 승인 후 다음 버전에만 반영", 16, 500, "#5f6870")

# Incoming signals and scheduled deterministic evaluation.
box(62, 145, 350, 100, "입력 artifact", "비동기 수집", ["OTel stage trace · version/hash", "고정 gold 질문 · 정답 근거 ID"], "#eef4fb", "#85a9d0")
box(770, 145, 360, 100, "Quality Supervisor", "상태 관리 · 단일 writer", ["정기 replay · 중복 병합 · 비용/권한 gate", "운영자 시작 전에는 분석/실험 대기"], "#f1edf6", "#a18bb5")
box(1485, 145, 350, 100, "운영 관측", "집계·알림", ["Grafana: 지표·trace·큐 추이", "Discord / 이메일: 주간 요약"], "#f2f5f3", "#8da99a")
arrow(412, 195, 760, 195, "고정 입력 참조")
arrow(1130, 195, 1475, 195, "낮은 카디널리티 지표")

# Five bounded responsibilities.
xs = [50, 425, 800, 1175, 1550]
titles = [
    ("1 · Evaluation Analyzer", "결정적 Python", ["gold replay · Recall@K / MRR / nDCG", "단계별 비교 → FailureCase 생성", "LLM 호출 없음"]),
    ("2 · Root Cause Investigator", "규칙 우선 · 증거 연결", ["retrieval / ranking / grounding 추적", "지지·반증 artifact ID를 기록", "모호할 때만 운영자 시작 LLM"]),
    ("3 · Experiment Planner", "승인 템플릿 우선", ["가설 → allowlist ExperimentSpec", "변경변수·예상효과·실패기준", "운영자 확인 전 실행 불가"]),
    ("4 · Experiment Runner", "격리된 결정적 실행", ["고정 corpus/config snapshot 재생", "baseline ↔ candidate 비교·회귀검사", "운영 DB/config 쓰기 권한 없음"]),
    ("5 · Human Review Gate", "사람의 판정", ["결과·비용·품질·rollback 검토", "승인 / 거절 / 재실험", "승인 후 별도 승격·canary"]),
]
for x, (title, sub, lines) in zip(xs, titles):
    box(x, 330, 300, 230, title, sub, lines, "#f2edf7", "#a88cbd")

for i in range(4):
    arrow(xs[i] + 300, 444, xs[i + 1] - 10, 444)

# Explicit human-start gates between investigation and experiments.
box(405, 630, 400, 120, "운영자 시작 gate", "관리자 검토 화면에서 선택", ["case 범위 · 입력 artifact · CLI quota/비용 확인", "시작 전에는 Root Cause / Planner를 실행하지 않음"], "#fff5e5", "#d0a65e")
arrow(575, 620, 575, 560, "사례 선택 후 조사 시작", "#bd8b37")
text(1138, 423, "운영자 시작", 12, 700, "#bd8b37", "middle")

# Optional LLM boundary: available only when explicitly invoked and budgeted.
box(60, 630, 300, 120, "선택적 LLM / Antigravity CLI", "기본 경로에 포함되지 않음", ["운영자가 사례와 비용을 확인해 실행", "가설 초안만 작성 · 자동 수정 금지"], "#f7f0fa", "#b89acb")
arrow(360, 690, 415, 470, "필요할 때만", "#8b6aa5", True)
text(65, 815, "원칙", 15, 800, "#342640")
text(125, 815, "‘다섯 agent’는 다섯 개의 책임 경계입니다. Evaluation Analyzer·Experiment Runner는 코드로 결정적으로 실행합니다.", 14, 500)
text(125, 842, "Root Cause / Planner의 LLM 보조도 운영자가 명시적으로 시작한 경우에만 허용하며, 운영 요청 중 검색 전략을 바꾸지 않습니다.", 14, 500)
text(65, 917, "산출물: FailureCase → evidence-linked Finding → ExperimentSpec → immutable ExperimentReport → 서명된 승인/거절 기록", 14, 700, "#4f3b5c")
add("</svg>")
OUT.write_text("\n".join(parts), encoding="utf-8")
print(f"Built {OUT}")
