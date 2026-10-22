# AI-RAG Architecture Diagrams

이 디렉터리는 목표 AI-RAG 구조를 설명하는 편집 가능한 두 가지 원본을 둔다. 운영 구현 현황이 아니라 계획된 목표 아키텍처다. 세부 입력·출력·권한·오류 계약은 상위의 `module-boundaries-and-pipelines.md`, `request-lifecycle.md`, `repository-split-and-monitoring.md`가 정본이다.

## 어떤 그림을 볼지

| 그림 | 쓰임 |
|---|---|
| `likec4/architecture.c4` | 시스템·컨테이너·컴포넌트·배포와 요청 시퀀스를 하나의 탐색 가능한 모델로 유지한다. 보고서 옆의 인터랙티브 링크로 이동·확대한다. |
| `c4-plantuml/01-containers.puml` | 사용자부터 Next.js, Nginx, Spring, FastAPI, PostgreSQL, Gemini까지 서비스 경계와 내부 호출 계약을 한 장에 설명한다. |
| `c4-plantuml/02-deployment.puml` | Vercel과 AWS Lightsail 목표 배포, 인스턴스 안의 별도 프로세스, 비공개 포트·DB 접근을 설명한다. |
| `c4-plantuml/03-spring-components.puml` | Spring의 인증·대화·개인정보·계획 승인·정형 SQL·최종 검증·저장/SSE 책임을 설명한다. |
| `c4-plantuml/04-fastapi-components.puml` | FastAPI의 계획·검색·RRF·rerank·근거·생성, corpus와 quality harness 모듈을 설명한다. |

Spring과 FastAPI는 서로 다른 애플리케이션 프로세스이며 목표로는 서로 다른 Git repository/image를 쓴다. 두 프로세스가 목표 2GB Lightsail 한 대에서 함께 실행되는 배치도와 논리 서비스 경계는 별개로 표현했다. 공개 인터넷 진입은 Nginx 80/443뿐이고, Spring↔FastAPI와 DB 연결은 비공개 네트워크·서비스 인증·분리된 DB 권한을 전제로 한다. 이 목표 배포는 아직 FastAPI 운영 배포가 완료되었음을 뜻하지 않는다.

## HTML 브리핑

[`../reports/2026-10-21-system-briefing.html`](https://github.com/YRootLab/OnMaru-backend/blob/develop/docs/ai-rag/reports/2026-10-21-system-briefing.html)은 큰 컨테이너 그림, 다섯 책임으로 확대한 Quality Harness 흐름도, 네 개의 C4-PlantUML SVG, LikeC4 인터랙티브 모델 진입점을 함께 제공한다. FastAPI C4 그림은 서버 내부 경계를 보여주고, 상세 Quality Harness 그림은 책임·운영자 gate·LLM 선택 경계·사람 승인을 따로 확대한다. 저장소 루트에서 정적 보고서를 열려면 다음처럼 HTTP 서버를 시작한다.

```bash
python3 -m http.server 18765 --bind 127.0.0.1
```

그 뒤 `http://127.0.0.1:18765/docs/ai-rag/reports/2026-10-21-system-briefing.html`을 연다. LikeC4 사이트는 HTML 보고서가 사용하는 상대 경로 아래에 빌드되어 있어 HTTP로 여는 것을 권장한다.

## 재생성

### LikeC4 모델 검사와 인터랙티브 사이트

Node.js 22.22.3 이상을 사용한다. 현재 `package.json`을 추가하지 않고 일회성 CLI 버전을 고정했다.

```bash
npx --yes likec4@1.60.0 validate --json docs/ai-rag/diagrams/likec4
npx --yes likec4@1.60.0 build \
  --base-url /docs/ai-rag/reports/likec4-site/ \
  -o docs/ai-rag/reports/likec4-site \
  docs/ai-rag/diagrams/likec4
```

### C4-PlantUML SVG

PlantUML 1.2026.9 이상과 Java가 필요하다. 원본은 공식 C4-PlantUML 저장소의 include를 네트워크로 가져오므로 빌드 시 네트워크 연결이 필요하다.

```bash
java -jar /path/to/plantuml.jar -tsvg -o ../../reports/diagrams/c4 docs/ai-rag/diagrams/c4-plantuml/01-containers.puml
java -jar /path/to/plantuml.jar -tsvg -o ../../reports/diagrams/c4 docs/ai-rag/diagrams/c4-plantuml/02-deployment.puml
java -jar /path/to/plantuml.jar -tsvg -o ../../reports/diagrams/c4 docs/ai-rag/diagrams/c4-plantuml/03-spring-components.puml
java -jar /path/to/plantuml.jar -tsvg -o ../../reports/diagrams/c4 docs/ai-rag/diagrams/c4-plantuml/04-fastapi-components.puml

cp "docs/ai-rag/reports/diagrams/c4/OnMaru C4 Container View.svg" docs/ai-rag/reports/diagrams/c4/01-containers.svg
cp "docs/ai-rag/reports/diagrams/c4/OnMaru C4 Deployment View.svg" docs/ai-rag/reports/diagrams/c4/02-deployment.svg
cp "docs/ai-rag/reports/diagrams/c4/OnMaru Spring Components.svg" docs/ai-rag/reports/diagrams/c4/03-spring-components.svg
cp "docs/ai-rag/reports/diagrams/c4/OnMaru FastAPI Components.svg" docs/ai-rag/reports/diagrams/c4/04-fastapi-components.svg
rm "docs/ai-rag/reports/diagrams/c4/OnMaru C4 Container View.svg" "docs/ai-rag/reports/diagrams/c4/OnMaru C4 Deployment View.svg" "docs/ai-rag/reports/diagrams/c4/OnMaru Spring Components.svg" "docs/ai-rag/reports/diagrams/c4/OnMaru FastAPI Components.svg"
```

위 명령은 저장소 루트에서 실행한다. PlantUML 출력 파일명은 `@startuml` 제목에서 오므로 보고서가 참조하는 안정 이름으로 복사한다. CI에서 렌더링할 경우 PlantUML jar와 C4-PlantUML remote include 버전을 고정하는 것을 권장한다.

### 보고서

다이어그램 SVG나 본문 문서를 바꾼 뒤 아래 빌더를 실행한다. LikeC4 사이트와 C4 SVG는 별도로 재생성해야 한다.

```bash
python3 docs/ai-rag/reports/build_system_briefing.py
```
