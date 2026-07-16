# RDB vs GraphDB(Neo4j) 성능 비교 실험

## 목적

지금 서비스(4EVR0-Server)는 `Product-CONTAINS->Ingredient-AFFECTS->Effect-RELATES_TO->Concern`
구조의 지식 그래프를 Neo4j로 운영 중이다. 데이터 규모가 크지 않고(Product ~3,123 / Ingredient ~3,222
/ CONTAINS ~112,967 / AFFECTS ~5,387 / RELATES_TO 25), 실제 프로덕션 쿼리도 hop 수가 고정된
2~3-hop 패턴이라 "이 규모/패턴에서 RDB가 Neo4j보다 느리다는 게 실제로 맞나?"를 직접 재본다.

동일 데이터를 Postgres에 동일 개체/관계로 옮기고, 프로덕션이 실제로 쓰는 Cypher 쿼리 3개
(`4EVR0-Server/app/clients/neo4j_client.py`)를 동등한 SQL로 포팅해서 같은 조건으로 latency를 비교한다.

## 논의 및 결정 사항

### 1. 왜 지금 이 실험이 필요한가

"데이터 간 관계가 명확하니까 그래프DB가 맞는 선택 아니냐"는 질문이 있었음.
결론: 관계가 **고정되고 명확**한 것은 오히려 RDB가 유리해지는 조건에 가깝다.
그래프DB의 강점은 관계가 가변적이거나(hop 수를 미리 모름), 임의 깊이 탐색, 그래프 알고리즘
(커뮤니티 탐지, 최단경로 등)이 필요할 때 나온다. 지금 구조는 고정된 4단계 계층 + 고정 hop
쿼리라서, "관계가 명확함 = 그래프DB가 맞다"는 직관과 반대로 갈 수 있음. 그래서 실측이 필요함.

### 2. 스키마를 "그대로 가져간다"는 것의 의미

Neo4j의 property graph를 복사하는 게 아니라, 같은 개체·관계 모델을 RDB 정규화 규칙으로 옮기는 것.
- `Product`, `Ingredient`, `Effect`, `Concern` → 각각 테이블
- `CONTAINS`, `AFFECTS`, `RELATES_TO` → 각각 연결(junction) 테이블

### 3. 왜 CONTAINS/AFFECTS/RELATES_TO를 별도 테이블로 만드는가

이건 그래프 흉내가 아니라 RDB에서 다대다(M:N) 관계를 표현하는 표준 방식이다.
- `Product`-`Ingredient`, `Ingredient`-`Effect`, `Effect`-`Concern` 모두 다대다 관계라
  한쪽 테이블에 FK 하나 추가하는 식(1:N)으로는 표현이 안 되고 연결 테이블이 필수임.
- `AFFECTS`는 관계 자체에 속성(`evidence_type`, `graph_score`, `paper_count`)이 있어서
  애초에 두 엔티티 중 하나에 넣을 수 없고 연결 테이블에만 있을 수 있음.
- 배열 컬럼(`Product.ingredients TEXT[]`) 같은 대안은 인덱스/조인 최적화를 못 받아
  "RDB가 이 규모에서 얼마나 빠른가"를 공정하게 재는 실험 취지에 맞지 않아서 배제.

## 진행 단계

- [x] 데이터/쿼리 조사: 그래프 구조(`README.md`), 데이터 규모(`csv/nodes`, `csv/edges`),
      프로덕션 Cypher 쿼리 3개(`4EVR0-Server/app/clients/neo4j_client.py`) 확인
- [x] `pg_experiment/` 폴더 생성
- [x] `pg_experiment/schema.sql` 작성 — product/ingredient/effect/concern + 연결 테이블 3개,
      프로덕션 쿼리가 실제로 타는 컬럼(`contains.inci_name`, `product.category`,
      `affects.effect_code`) 기준 인덱스 포함
- [x] `pg_experiment/docker-compose.yml` 작성 — 5433 포트로 별도 Postgres 컨테이너
      (4EVR0-Server의 Postgres(5432, 세션 저장용)와 분리, 데이터도 독립)
- [x] Postgres 컨테이너 기동 및 스키마 적용
- [x] CSV → Postgres 적재 스크립트 작성/실행
      (product 3122 / ingredient 3221 / effect 15 / concern 15 /
      contains 112966 / affects 5386 / relates_to 24 — Neo4j import 원본과 동일)
  - 적재 중 `affects.csv`에서 (inci_name, effect_code) 중복 58쌍 발견 →
    Neo4j는 멀티그래프라 같은 두 노드 사이 관계가 여러 개 있을 수 있음.
    PK를 (inci_name, effect_code)로 걸면 이 행들이 유실되어 Postgres가
    실제보다 적은 데이터로 조인하게 됨 → `affects` PK를 BIGSERIAL로 변경,
    전체 행 유지 (schema.sql 수정, 커밋 2082434)
- [x] Cypher 쿼리 3종 → SQL 포팅 (`queries.py`) + 결과 일치 검증 (`verify_parity.py`)
  - 검증 중 발견한 이슈 1: Postgres DB collation(`en_US.utf8`)이 한글 문자열을
    Neo4j(유니코드 코드포인트 기준)와 다르게 정렬 → `query_products_by_ingredients`에서
    동점(matched_count 같음) 처리 시 top-5 상품 집합 자체가 완전히 달라짐.
    `ORDER BY product_name COLLATE "C"`로 코드포인트 기준 정렬을 맞춰 해결.
  - 검증 중 발견한 이슈 2: `query_path_by_effects`는 원본 Cypher가
    `ORDER BY r.graph_score DESC` 하나만 쓰고 2차 정렬 기준이 없어서, 동점(같은
    graph_score) 행이 많으면 LIMIT 10 안에 어느 행이 들지가 **원본 쿼리 자체가
    이미 비결정적**. SQL 포팅 버그가 아니라 프로덕션 쿼리의 기존 특성이라
    "고치지" 않고 그대로 반영, 검증도 신원이 아닌 graph_score 분포로만 비교.
- [ ] 벤치마크 하네스 작성 (반복 실행, p50/p95/p99, hop 수 확장 시나리오)
- [ ] 벤치마크 실행 및 결과 정리

## 파일 구성

```
pg_experiment/
├── EXPERIMENT.md      # 이 문서 — 과정 기록
├── docker-compose.yml # 벤치마크 전용 Postgres 컨테이너 (5433 포트)
├── schema.sql          # RDB 스키마
├── load_csv.py          # (예정) CSV -> Postgres 적재
├── queries_sql.py       # (예정) Cypher 3종의 SQL 버전
└── benchmark.py          # (예정) Neo4j vs Postgres latency 비교
```
