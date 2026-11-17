# AI Engine 배포와 릴리스 모델

> 상태: 설계 초안. AI 저장소는 아직 비어 있는 원격 저장소에 대한 로컬 migration draft이며, FastAPI 운영 배포는 구현되지 않았다.

## 핵심 원칙

AI 코드 저장소를 분리해도 AWS 실행 인스턴스는 분리하지 않는다. `onmaru-ai-engine`은 FastAPI 코드·검증·빌드와 immutable image 발행을 소유한다. `OnMaru-backend`는 현재 Lightsail host, Compose, Nginx, PostgreSQL volume/backup, 제한된 production deployer를 계속 소유한다. 2GB로 업그레이드한 기존 한 인스턴스에서 Spring·DB·FastAPI를 공존시키는 것이 목표다.

현재 Compose는 Spring Blue-Green·PostgreSQL·Nginx만 운영하며 FastAPI를 포함하지 않는다. 구현되었다고 간주하지 말고, 2GB 혼합 부하와 배포/복구 리허설을 통과한 뒤에만 운영 경로를 연다.

## 배포 토폴로지

```text
Public Internet
     │ HTTPS 443
     ▼
Nginx ── public REST/SSE ──> Spring Boot Blue/Green
                                  │ private REST + traceparent
                                  ▼
                             FastAPI (single active container)
                                  │ private network, AI-only DB role
                                  ▼
                       PostgreSQL/PostGIS + pgvector
```

모든 컨테이너는 기존 Lightsail Docker host에서 실행한다. 호스트의 80/443 외에는 공개 포트를 열지 않는다. Spring 8080, FastAPI, PostgreSQL 5432는 host port에 publish하지 않는다. FastAPI는 필요한 `app`/`database` 내부 network에만 연결하며 AI schema 최소 권한을 쓴다. MCP는 tool discovery가 필요한 기능에만 적용하고 고정 plan/execute는 private REST로 시작한다.

## CI와 운영 배포 책임

1. AI 저장소의 pull request는 lint, typecheck, unit/contract/evaluation tests, dependency scan, Docker build를 실행한다. PR workflow에는 운영 secret과 production deploy permission을 주지 않는다.
2. 승인된 AI release는 source SHA가 붙은 OCI image를 GHCR에 발행하고 digest를 배포 산출물로 기록한다. mutable `latest`는 운영에서 사용하지 않는다.
3. 백엔드 저장소가 가진 staging/production workflow는 AI image digest, Spring image digest, 계약 버전을 조합해 호환성을 검사한다. 배포 workflow는 승인된 조합의 AI digest만 제한 SSH deployer로 전달한다.
4. Spring만 변경하면 현재 AI digest를 고정해 그대로 둔다. AI만 변경하면 현재 Spring digest와 DB schema version을 고정한다. 두 서비스가 동시에 바뀌면 두 digest를 release manifest에 함께 기록한다.
5. Production state에는 현재/직전 Spring과 AI digest를 각각 기록해 개별 롤백과 함께 배포한 조합 롤백을 구분한다.

Spring/Nginx/DB 인프라를 가진 백엔드 저장소가 deployer 입력을 소유한다. AI repository workflow가 운영 SSH key를 갖거나 전체 backend repository를 임의 checkout해 production을 직접 변경하지 않는다.

## 배포 중 메모리와 장애 경계

기존 Spring Blue-Green은 현재 제한과 검증 절차를 유지한다. FastAPI는 2GB host에서 peak RSS가 측정되기 전까지 Blue-Green 두 벌을 동시에 띄우지 않는다. Compose가 단일 FastAPI service를 재생성하는 방식으로 먼저 시작하고, 짧은 AI endpoint 중단 중 Spring은 timeout/fallback 정책을 적용한다. 실패 시 직전 image digest로 되돌리고 health check를 다시 통과시킨다.

AI 이미지의 readyness는 HTTP health만 확인하지 않는다. 모델/profile 및 계약 버전, PostgreSQL ai schema 접근, 필수 검색 인덱스 활성화 상태를 확인한다. 외부 Gemini 응답을 매번 readiness에 포함해 provider 일시 장애가 컨테이너 재시작 loop를 일으키지 않게 한다.

AI 오프라인 품질 harness와 대량 embedding은 사용자 요청과 분리한다. 초기에는 상시 worker를 추가하지 않는다. 작업은 낮은 concurrency·명시 budget으로 실행하고, 실행 전/중 메모리·CPU·DB connection을 제한한다. 2GB 혼합 부하에서 부족하면 동시성·모델 로딩·색인 작업 일정을 조정한 후 재측정한다.

## 인프라 저장소에서 필요한 작업

다음은 `OnMaru-backend`에서 구현하고 검증할 항목이다.

- 현재 Lightsail Compose에 내부 전용 FastAPI service, bounded resources, non-root/security options, health check와 로그 제한을 정의한다.
- Spring과 FastAPI에 필요한 network access만 허용한다. AI DB credential은 Spring runtime 계정과 분리한다. DB 포트는 공개하지 않는다.
- 현재 production deployer는 Spring digest 하나만 받으므로 AI digest 및 release compatibility 입력을 명시적으로 지원한다. 입력은 digest 형식 allowlist 검증 후 root-owned script에 전달한다.
- 현재 1GB 환경에서 운영 FastAPI를 켜지 않는다. 기존 Lightsail의 2GB 플랜 변경 후 실제 이미지/모델, PostgreSQL 인덱스, Blue-Green Spring 교체를 포함해 검증한다.
- pgvector와 PostGIS extension, AI schema migration, 계정 권한 및 백업 복원을 staging에서 검증한다. AI migration 작업은 AI runtime credential과 분리한다.
- system of record인 release state에 실행 image digest, source SHA, contract version, migration version, health/rollback 결과를 기록한다.
- 기존 Nginx SSE 설정·Spring health smoke·제한 SSH key를 재사용하고, FastAPI 포트가 public route/listen으로 노출되지 않는 테스트를 둔다.

구현할 backend-side 인수 기준은 [`docs/ai-rag-spring/repository-and-deployment.md`](https://github.com/YRootLab/OnMaru-backend/tree/develop/docs/ai-rag-spring/repository-and-deployment.md)에 둘 예정이다. 실제 BE 변경이 검토·병합된 뒤 이 링크를 해당 커밋의 영구 permalink로 교체한다.

## staging 합격 기준

운영과 같은 컨테이너 제한과 대표 corpus를 사용해 아래를 측정한다.

- idle, normal query, concurrent query, indexing/evaluation 단계의 container RSS, host MemAvailable, swap delta, CPU, disk/index growth
- Spring Blue-Green 겹침 중 peak memory와 OOM 여부
- FastAPI 재시작·timeout/provider 장애에서 Spring fallback과 SSE 동작
- Spring→FastAPI W3C Trace Context 연속성, AI image digest와 run trace 연결
- ai schema 권한 경계·pgvector/BM25 검색·migration 전후 호환 및 backup restore
- 새 digest readiness 실패 시 이전 digest 복원, 직전 schema와의 호환성

현재 CPU 사용률이 낮다는 이유만으로 공존을 판정하지 않는다. embedding, reranker, indexing과 deploy overlap의 peak를 확인한다. 운영 배포는 2GB Lightsail 변경, 혼합 부하, rollback 검증이 모두 끝난 뒤에만 활성화한다.
