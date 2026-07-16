# RDB(Postgres) vs GraphDB(Neo4j) 성능 비교 — 결과 보고서

배경/설계 논의는 [`EXPERIMENT.md`](./EXPERIMENT.md) 참고. 이 문서는 실제 실행 결과만 정리한다.

## 1. 실험 조건

- 데이터: `csv/nodes`, `csv/edges` (Neo4j import에 쓰는 원본과 100% 동일)
  - product 3,122 / ingredient 3,221 / effect 15 / concern 15
  - contains 112,966 / affects 5,386 / relates_to 24
- 비교 대상 쿼리: 4EVR0-Server가 실제로 쓰는 Cypher 쿼리 3개(`neo4j_client.py`) +
  hop-scaling 확인용 4-hop 쿼리 1개(실서비스 미사용)
- 드라이버: Neo4j는 `neo4j` 공식 드라이버(Bolt), Postgres는 `psycopg` v3 — 둘 다
  세션/커넥션을 미리 열어 재사용, 순수 쿼리 실행 시간만 측정
- 측정: 워밍업 20회 제외, 200회 반복, 두 엔진에 **완전히 동일한 파라미터 시퀀스**(seed=42)
- LLM 응답 시간은 포함하지 않음 — 이유는 `EXPERIMENT.md` 및 대화 기록 참고 (LLM 추론이
  DB latency보다 훨씬 커서 같이 재면 DB 간 차이가 노이즈에 묻힘)

## 2. 결과 정합성 검증 (`verify_parity.py`)

SQL이 Cypher와 실제로 같은 결과를 내는지 먼저 확인했다. 과정에서 실제 버그 2건을 발견/수정했다.

### 1차 실행 — mismatch 발견

```
[MISMATCH] query_products_by_ingredients: cypher=5 rows, sql=5 rows
  cypher: [('b404934a-bcad-5e25-92c5-0530ce9bc76f',), ('476a6bf3-9f00-5af4-8df3-579240ab5a2a',), ('dad7b7ae-79bc-5dc1-ab5f-16c5141d7267',), ('4529246a-125a-5e09-b642-319b4dda3b8b',), ('da16bdbf-689d-5b22-bb22-2e99111155d4',)]
  sql   : [(UUID('fadd2cce-b52d-523c-b3bb-e152a4aff367'),), (UUID('4f2a538e-9dad-55ca-bd8f-32b1785fee98'),), (UUID('e466b944-e9d1-5e5e-a42b-9ad07f7d381f'),), (UUID('061dd41b-23d4-58d3-99e3-6b0aeebefc59'),), (UUID('cb08106d-ca4b-5fb5-982e-d2b650e0d359'),)]
[OK] query_ingredients_by_effects: cypher=20 rows, sql=20 rows
[MISMATCH] query_path_by_effects: cypher=10 rows, sql=10 rows
  cypher: [('SOOTHING', 'RETINOL', '코스메쉐프 흑당고 진액 영양 주름앰플', 0.71784), ('SOOTHING', 'RETINOL', '썸바이미 레티놀 인텐스 액션 아이크림', 0.71784), ...]
  sql   : [('SOOTHING', 'RETINOL', '토리든 셀메이징 저분자 콜라겐 탄력 아이크림', 0.71784), ('SOOTHING', 'RETINOL', '피캄 레티놀라겐 앰플샷 폼클렌저', 0.71784), ...]
```

원인 규명:
- `query_products_by_ingredients`: Postgres DB collation이 `en_US.utf8`이라 한글 상품명
  정렬 순서가 Neo4j(유니코드 코드포인트 기준)와 다름 → 동점(matched_count 같음) 상품 중
  어느 5개가 뽑히는지가 완전히 달라짐. `ORDER BY product_name COLLATE "C"`로 해결.
- `query_path_by_effects`: 원본 Cypher가 `ORDER BY graph_score DESC` 하나뿐이라 동점 구간
  처리가 **프로덕션 쿼리 자체부터 비결정적**. SQL 버그가 아니라서 "고치지" 않고, 검증
  기준을 신원 비교 대신 graph_score 분포 비교로 바꿈.

### 재검증 — 전부 통과

```
[OK] query_products_by_ingredients: cypher=5 rows, sql=5 rows
[OK] query_ingredients_by_effects: cypher=20 rows, sql=20 rows
[OK] query_path_by_effects (graph_score만 비교, 동점 구간 비결정적): cypher=10 rows, sql=10 rows
```

## 3. 벤치마크 원본 출력 (`benchmark.py`)

```
=== products_by_ingredients ===
  neo4j   : {'n': 200, 'mean_ms': 13.716, 'p50_ms': 12.861, 'p95_ms': 17.818, 'p99_ms': 23.432, 'min_ms': 10.525, 'max_ms': 44.21}
  postgres: {'n': 200, 'mean_ms': 3.806, 'p50_ms': 1.992, 'p95_ms': 8.553, 'p99_ms': 30.526, 'min_ms': 0.949, 'max_ms': 92.555}
=== ingredients_by_effects ===
  neo4j   : {'n': 200, 'mean_ms': 10.533, 'p50_ms': 7.299, 'p95_ms': 21.322, 'p99_ms': 29.485, 'min_ms': 3.99, 'max_ms': 51.012}
  postgres: {'n': 200, 'mean_ms': 7.229, 'p50_ms': 3.897, 'p95_ms': 17.844, 'p99_ms': 20.968, 'min_ms': 0.984, 'max_ms': 22.026}
=== path_by_effects ===
  neo4j   : {'n': 200, 'mean_ms': 36.391, 'p50_ms': 25.086, 'p95_ms': 70.702, 'p99_ms': 96.088, 'min_ms': 5.578, 'max_ms': 109.467}
  postgres: {'n': 200, 'mean_ms': 54.216, 'p50_ms': 49.82, 'p95_ms': 89.997, 'p99_ms': 116.116, 'min_ms': 6.861, 'max_ms': 118.414}
=== products_by_concern ===
  neo4j   : {'n': 200, 'mean_ms': 3.448, 'p50_ms': 3.281, 'p95_ms': 4.884, 'p99_ms': 5.848, 'min_ms': 2.48, 'max_ms': 6.759}
  postgres: {'n': 200, 'mean_ms': 92.82, 'p50_ms': 18.537, 'p95_ms': 234.146, 'p99_ms': 247.685, 'min_ms': 6.418, 'max_ms': 254.962}

결과 저장: pg_experiment/results/latencies.json
```

원본 JSON: [`results/latencies.json`](./results/latencies.json)

## 4. 요약 표 (hop 수 순)

| 쿼리 | hop 수 | 프로덕션 사용 | Neo4j p50 | Postgres p50 | Neo4j p99 | Postgres p99 | 승자(p50) |
|---|---|---|---:|---:|---:|---:|---|
| products_by_ingredients | 1 | O | 12.9 ms | **2.0 ms** | 23.4 ms | 30.5 ms | Postgres |
| ingredients_by_effects | 1 | O | 7.3 ms | **3.9 ms** | 29.5 ms | 21.0 ms | Postgres |
| path_by_effects | 2 | O | **25.1 ms** | 49.8 ms | 96.1 ms | 116.1 ms | Neo4j |
| products_by_concern | 4 | X(실험용) | **3.3 ms** | 18.5 ms | **5.8 ms** | 247.7 ms | Neo4j (압도적) |

## 5. 해석

- **1-hop, 고정 패턴에서는 Postgres가 이긴다.** 인덱스 잘 걸린 단순 JOIN + 집계는
  이 데이터 규모(수천~10만 행)에서 Postgres 플래너가 Neo4j보다 빠르다.
- **hop이 늘어날수록 역전되고, 격차가 급격히 커진다.** 2-hop에서 이미 Neo4j가 앞서고,
  4-hop(`products_by_concern`)에서는 p99 기준 **약 43배** 차이(Neo4j 5.8ms vs Postgres
  247.7ms). Postgres는 JOIN을 늘릴수록 플래너 비용/중간 결과 크기가 커지는 반면, Neo4j는
  포인터 추적(index-free adjacency)이라 hop이 늘어도 비용이 상대적으로 완만하게 증가.
- 다만 4번째 쿼리는 프로덕션에서 안 쓰는 실험용 쿼리이고, `DISTINCT` 결과 신원 자체는
  검증하지 않았음(값 분포만 신뢰) — 참고용 신호로만 볼 것.
- **지금 프로덕션 쿼리 3개만 놓고 보면 승부는 갈린다** (1-hop 둘은 RDB 승, 2-hop 하나는
  Neo4j 승). "그래프DB가 무조건 유리하다"도 "RDB로 충분하다"도 성급한 결론.

## 6. 이번 실험이 다루지 않은 것

- **LLM 응답 시간을 포함한 end-to-end 지연**: DB 선택과 독립적인 변수라 의도적으로 제외.
  필요하면 GPU 서버(`GPU_SERVER_URL`)를 띄우고 `4EVR0-Server/load/locustfile.py`로
  별도 실험 필요.
- **가변 길이 경로 탐색** (예: `SIMILAR_TO`/`SUBSTITUTE_FOR` 성분 유사도로 `*1..3` 확장
  탐색): 지금 데이터엔 그런 관계가 없어 테스트 못 함. 이런 케이스는 Postgres도
  재귀 CTE(`WITH RECURSIVE`)로 구현은 가능하나 대체로 그래프DB가 유리한 전형적 영역 —
  "성분 표기가 달라 매칭이 안 되는" 커버리지 부족 문제를 풀려면 이쪽 실험이 이어서 필요.
- **동시 부하(동시성) 상황의 처리량**: 이번 벤치마크는 순차 실행 latency만 측정, 동시
  요청 시 커넥션 풀 경합 등은 안 봄.
