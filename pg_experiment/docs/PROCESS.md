# 실험 진행 과정 (시간 순 기록)

"왜 이 명령을 실행했고, 실행하니 무슨 일이 있었고, 그래서 다음에 뭘 했는지"를 순서대로
정리한 문서. 설계 논의 요약은 [`EXPERIMENT.md`](./EXPERIMENT.md), 최종 수치/결론은
[`RESULTS.md`](./RESULTS.md) 참고.

## 1. 왜 시작했나

기존 서비스(4EVR0-Server)는 Neo4j로 상품-성분-효능-피부고민 그래프를 운영 중인데,
데이터 규모가 크지 않고(제품 3천여 개) 실제 프로덕션 쿼리 3개도 hop 수가 고정된
1~2-hop 패턴이었다. "지금 이 규모/패턴에서 RDB가 Neo4j보다 느리다는 게 실제로 맞나?"를
직접 재보기로 했다.

→ **필요했던 것**: 같은 데이터를 Postgres에 옮기고, 실제 프로덕션이 쓰는 쿼리를 SQL로
포팅해서 같은 조건으로 latency를 비교하는 것.

## 2. 스키마 설계

`csv/nodes/*.csv`, `csv/edges/*.csv`(Neo4j import 원본)를 읽어 `Product`, `Ingredient`,
`Effect`, `Concern` 4개 엔티티 테이블 + `contains`, `affects`, `relates_to` 3개
연결(junction) 테이블로 설계했다 (`schema.sql`).

→ **왜 연결 테이블을 따로 뒀나**: `Product`-`Ingredient` 등은 전부 다대다 관계라
RDB 정규화 규칙상 연결 테이블 없이는 표현 자체가 불가능하다(그래프 흉내가 아니라
표준 RDB 설계). `affects`는 관계 자체에 `graph_score` 등 속성이 있어서 더더욱
그렇다.

→ **결과**: `pg_experiment/docker-compose.yml`로 벤치마크 전용 Postgres 컨테이너를
5433 포트에 띄우고(4EVR0-Server의 세션용 Postgres 5432와 분리), `schema.sql`을 적용.
문제없이 테이블 7개 생성됨.

## 3. CSV 적재 — 첫 시도에서 실패, 원인 파악 후 스키마 수정

`load_csv.py`로 CSV를 그대로 적재하다가 다음 에러로 중단됨:

```
psycopg.errors.UniqueViolation: duplicate key value violates unique constraint "affects_pkey"
DETAIL:  Key (inci_name, effect_code)=(COLLOIDAL OATMEAL, SOOTHING) already exists.
```

→ **왜 이런 일이 있었나 확인**: `affects.csv`를 직접 세어보니 (성분, 효능) 조합이
중복인 행이 58쌍 있었다. Neo4j는 멀티그래프라 같은 두 노드 사이에 관계가 여러 개
있어도 되지만, `affects` 테이블 PK를 `(inci_name, effect_code)`로 걸어놔서 이 중복이
적재 시 거부된 것.

→ **판단**: 이 중복을 그냥 버리면 Postgres가 원본보다 적은 행을 갖게 되어 벤치마크가
Postgres에 유리하게 왜곡된다. 그래서 PK를 `BIGSERIAL` surrogate id로 바꿔 전체 행을
유지하도록 `schema.sql` 수정 → 스키마 재적용 → 재실행.

→ **결과**: 전 테이블 정상 적재 확인 (product 3,122 / ingredient 3,221 / effect 15 /
concern 15 / contains 112,966 / affects 5,386 / relates_to 24 — Neo4j import 원본과
정확히 일치).

## 4. Cypher → SQL 포팅

프로덕션이 실제로 쓰는 Cypher 쿼리 3개(`4EVR0-Server/app/clients/neo4j_client.py`의
`query_products_by_ingredients`, `query_ingredients_by_effects`,
`query_path_by_effects`)를 그대로 가져와 동등한 SQL을 작성했다 (`queries.py`).
"hop이 늘어나면 그래프DB가 유리해지는 지점이 있을 것"이라는 가설을 확인하려고,
프로덕션엔 없지만 README에 문서화된 전체 4-hop 경로
(`Product-CONTAINS->Ingredient-AFFECTS->Effect-RELATES_TO->Concern`) 쿼리도
`products_by_concern`이라는 이름으로 하나 더 추가했다.

→ **다음 질문**: "SQL이 Cypher랑 진짜 같은 결과를 내는가?"를 확인 안 하면 벤치마크
자체가 무의미하다. → 5번으로 이어짐.

## 5. 결과 정합성 검증 — 실제 버그 2건 발견

`verify_parity.py`로 같은 파라미터를 Neo4j/Postgres 양쪽에 실행해서 결과를 비교했다.

**1차 실행 결과**: `query_products_by_ingredients`와 `query_path_by_effects`에서
mismatch 발생 — 반환된 상품 자체가 서로 완전히 다름.

→ **원인 조사**: `query_products_by_ingredients`는 상품명(한글) 기준 동점 처리가
있는데, Postgres DB collation을 확인해보니 `en_US.utf8`이었다. Neo4j(유니코드
코드포인트 기준 정렬)와 비교해보니 한글 상품명 정렬 순서 자체가 달랐다
(`ORDER BY product_name` 결과가 서로 다름 — 실제로 Neo4j는
`16년연속... → AHC 365... → ...`, Postgres `en_US.utf8`은 `스웨덴에그팩 → ...`처럼
전혀 다른 순서). → `ORDER BY product_name COLLATE "C"`로 수정하니 Neo4j와 순서
완전 일치.

→ `query_path_by_effects`는 원인이 달랐다: 원본 Cypher가 `ORDER BY graph_score DESC`
하나뿐이라, 동점(같은 score) 행이 많으면 LIMIT 안에 뭐가 들지가 **원본 쿼리 자체부터
비결정적**이었다. 이건 SQL 포팅 버그가 아니라서 고치지 않고, 검증 기준을
"신원 비교"에서 "graph_score 분포 비교"로 바꿨다.

**재검증 결과**: 3개 쿼리 전부 `[OK]`.

→ **추가로 발견**: 나중에 4-1단계(전체 결과 덤프)에서 `ingredients_by_effects`에도
같은 계열 문제가 있는 걸 하나 더 찾았다 — `RETINAL`이 `HYDRATING`/`SOOTHING` 두
효능에 완전히 동점(graph_score 같음)으로 걸려 있어서 어느 효능이 뽑히는지가
비결정적이었다. 자세한 내용/실제 데이터는 `RESULTS.md` §2 참고.

## 6. 벤치마크 실행

정합성이 확인된 후 `benchmark.py`로 4개 쿼리 × (워밍업 20회 + 측정 200회)를 양쪽
엔진에 동일 파라미터 시퀀스(seed 고정)로 실행했다. 세션/커넥션은 미리 열어 재사용해서
순수 쿼리 실행 시간만 쟀다.

→ **결과** (p50 기준, 전체 수치는 `RESULTS.md` §5 참고):

| 쿼리 | hop | 결과 |
|---|---|---|
| products_by_ingredients | 1 | Postgres가 6배 빠름 (2.0ms vs 12.9ms) |
| ingredients_by_effects | 1 | Postgres가 2배 빠름 (3.9ms vs 7.3ms) |
| path_by_effects | 2 | Neo4j가 2배 빠름 (25.1ms vs 49.8ms) |
| products_by_concern | 4 (실험용) | Neo4j가 6배 빠름, **p99는 43배** (247.7ms vs 5.8ms) |

→ **판단**: 가설이 맞았다 — hop이 늘어날수록 Neo4j가 유리해지고 격차도 커진다.
1-hop에서는 Postgres가, 2-hop 이상부터는 Neo4j가 이긴다.

## 7. 전체 원본 결과 덤프

벤치마크는 숫자만 남기고 실제 반환된 행은 기록하지 않길래, `dump_full_results.py`로
4개 쿼리 각각 고정 파라미터 1세트를 다시 실행해서 전체 행을 원본 그대로 남겼다
(`results/full_query_dump.md`, `RESULTS.md` §3에도 전문 포함). 이 과정에서 위 5번의
`ingredients_by_effects` 동점 이슈를 실제로 눈으로 확인했다.

## 8. 결과 보고서 작성 → 브랜치 정리 → PR

`RESULTS.md`에 검증 로그, 벤치마크 원본 출력, 전체 쿼리 결과, 요약 표, 해석, 결론까지
정리했다. 이 과정에서 커밋을 전부 `main`에 직접 올리는 실수를 했다는 걸 깨닫고,
`feat/pg-vs-neo4j-benchmark` 브랜치를 새로 만들어 커밋들을 옮기고 `main`은 실험 시작
전 상태로 되돌렸다 (`git branch -f main <실험 시작 전 커밋>` — working tree를 건드리지
않는 방식으로; 처음엔 `git reset --hard`를 시도했다가 `neo4j/import/`가 컨테이너
전용 권한(uid 7474, 소유자만 접근 가능)이라 도중에 실패해서 방식을 바꿨다. 실제 파일
손실은 없었음, `sudo`로 확인함). 이후 브랜치를 push하고 PR을 준비했다.

## 최종 결론

`RESULTS.md` §8 참고. 요약하면: **"관계가 명확하니 그래프DB가 맞다"는 가정은
틀렸고, 반대로 "그러니 RDB로 갈아타면 된다"도 성급하다.** 쿼리 패턴(hop 수)에 따라
유불리가 갈리며, 지금 데이터 규모에서는 1-hop은 RDB가, 2-hop 이상은 그래프DB가
우세하다는 게 실측 결론이다.
