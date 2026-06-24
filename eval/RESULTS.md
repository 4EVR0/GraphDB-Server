# 문제 3 조사 결과: 추천 결과 경로 탐색·랭킹 검증

## 1. 그래프 RELATES_TO vs 운영 코드 CONCERN_EFFECT_MAP

운영 코드(4evr0-server)는 `(Concern)-[:RELATES_TO]->(Effect)` 그래프 관계를 쓰지 않고, `taxonomy_normalization_service.CONCERN_EFFECT_MAP`(하드코딩 dict)으로 concern→effect를 직접 매핑한다. 그래프 자체의 RELATES_TO 관계와 비교한 결과:

- 그래프에 RELATES_TO가 **전혀 없는** Concern: 8/15 — `AGING_SIGNS, ATOPIC_PRONE, COMEDONES, DEHYDRATED_SKIN, DULLNESS, IRRITATED_SKIN, REDNESS, ROSACEA_PRONE`
  → README에 문서화된 `(Effect)-[:RELATES_TO]->(Concern)` 경로 자체로 추천을 시도하면 이 8개 고민은 0건이 나온다. 실서비스는 이 경로를 쓰지 않아 영향이 없지만, 그래프 데이터가 자기 문서화된 스키마와 불일치하는 상태.
- 그래프와 운영 코드 매핑이 **다른** Concern: `POST_ACNE_MARKS`
  - `POST_ACNE_MARKS`: 그래프=`['ANTI_INFLAMMATORY', 'BRIGHTENING', 'DEPIGMENTING']` vs 운영코드=`['BRIGHTENING', 'DEPIGMENTING', 'WOUND_HEALING']`

## 2. 경로 탐색 커버리지 (실제 운영 경로, 26개 concern 전체)

- 성분 결과 0건 concern: **0/26**
- 제품 결과 0건 concern: **0/26**
- 논문 근거(pubmed_evidence) 성분이 그래프에 0개인 concern: **DULLNESS**
  → 경로 탐색 자체는 결과를 내놓지만(아래 표의 `ing`/`prod` 열 참고), 전부 약한 근거(`cosing_function`)뿐이라 "정답"이라 부를 근거가 약함.
- top-20 안에 **같은 성분이 중복으로 여러 줄을 차지하는** concern: **20/26** — `ACNE, SENSITIVE_SKIN, REDNESS, IRRITATED_SKIN, ATOPIC_PRONE, ROSACEA_PRONE, DRY_SKIN, DEHYDRATED_SKIN, FLAKY_SKIN, BARRIER_DAMAGE, HYPERPIGMENTATION, UNEVEN_SKIN_TONE, BLEMISHES, POST_ACNE_MARKS, DARK_CIRCLES, SUNBURN, AGING_SIGNS, WRINKLES, LOSS_OF_ELASTICITY, SAGGING_SKIN`
  → 운영 쿼리의 `RETURN DISTINCT`가 성분 이름이 아니라 (이름, effect, evidence_type, ...) 행 전체를 기준으로 동작해서, 한 성분이 두 개 이상의 effect로 매치되면 LIMIT 20 중 여러 슬롯을 그 성분 하나가 차지한다. 그만큼 사용자가 실제로 보는 **distinct 성분 수는 20보다 적어진다** (`ing` vs `distinct` 열 비교).

| concern | 후보(전체) | 후보중 gold | 성분 반환(행) | distinct 성분 | 제품 반환 | Precision@20 | Recall@20 | NDCG@20 | 빈도baseline recall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ACNE | 280 | 5 | 20 | 19 **↑중복** | 5 | 0.25 | 1.00 | 1.00 | 0.00 |
| COMEDONES | 164 | 2 | 20 | 20 | 5 | 0.10 | 1.00 | 1.00 | 0.00 |
| PORE_CONGESTION | 164 | 2 | 20 | 20 | 5 | 0.10 | 1.00 | 1.00 | 0.00 |
| ENLARGED_PORES | 164 | 2 | 20 | 20 | 5 | 0.10 | 1.00 | 1.00 | 0.00 |
| OILY_SKIN | 198 | 5 | 20 | 20 | 5 | 0.25 | 1.00 | 1.00 | 0.00 |
| SENSITIVE_SKIN | 4009 | 84 | 20 | 14 **↑중복** | 5 | 1.00 | 0.24 | 1.00 | 0.04 |
| REDNESS | 277 | 28 | 20 | 19 **↑중복** | 5 | 1.00 | 0.71 | 1.00 | 0.00 |
| IRRITATED_SKIN | 2157 | 59 | 20 | 15 **↑중복** | 5 | 1.00 | 0.34 | 1.00 | 0.02 |
| ATOPIC_PRONE | 4009 | 84 | 20 | 14 **↑중복** | 5 | 1.00 | 0.24 | 1.00 | 0.04 |
| ROSACEA_PRONE | 277 | 28 | 20 | 19 **↑중복** | 5 | 1.00 | 0.71 | 1.00 | 0.00 |
| DRY_SKIN | 3963 | 60 | 20 | 17 **↑중복** | 5 | 1.00 | 0.33 | 1.00 | 0.05 |
| DEHYDRATED_SKIN | 2083 | 29 | 20 | 17 **↑중복** | 5 | 1.00 | 0.69 | 1.00 | 0.04 |
| FLAKY_SKIN | 2090 | 29 | 20 | 17 **↑중복** | 5 | 1.00 | 0.69 | 1.00 | 0.04 |
| ROUGH_TEXTURE | 238 | 4 | 20 | 20 | 5 | 0.20 | 1.00 | 1.00 | 0.00 |
| BARRIER_DAMAGE | 4199 | 85 | 20 | 14 **↑중복** | 5 | 1.00 | 0.24 | 1.00 | 0.04 |
| HYPERPIGMENTATION | 56 | 18 | 20 | 18 **↑중복** | 5 | 0.90 | 1.00 | 1.00 | 0.06 |
| DULLNESS | 212 | 0 | 20 | 20 | 5 | 0.00 | - | 0.00 | - |
| UNEVEN_SKIN_TONE | 15 | 15 | 15 | 13 **↑중복** | 5 | 1.00 | 1.00 | 1.00 | 0.08 |
| BLEMISHES | 17 | 17 | 17 | 15 **↑중복** | 5 | 1.00 | 1.00 | 1.00 | 0.07 |
| POST_ACNE_MARKS | 17 | 17 | 17 | 15 **↑중복** | 5 | 1.00 | 1.00 | 1.00 | 0.07 |
| DARK_CIRCLES | 15 | 15 | 15 | 13 **↑중복** | 5 | 1.00 | 1.00 | 1.00 | 0.08 |
| SUNBURN | 452 | 36 | 20 | 19 **↑중복** | 5 | 1.00 | 0.56 | 1.00 | 0.00 |
| AGING_SIGNS | 423 | 15 | 20 | 15 **↑중복** | 5 | 0.70 | 0.93 | 1.00 | 0.00 |
| WRINKLES | 2070 | 40 | 20 | 17 **↑중복** | 5 | 1.00 | 0.50 | 1.00 | 0.03 |
| LOSS_OF_ELASTICITY | 449 | 19 | 20 | 18 **↑중복** | 5 | 0.90 | 0.95 | 1.00 | 0.00 |
| SAGGING_SKIN | 218 | 15 | 20 | 18 **↑중복** | 5 | 0.70 | 0.93 | 1.00 | 0.00 |

## 3. 요약 (GraphRAG 경로 탐색 vs 기존 빈도 베이스라인)

- GraphRAG 평균 Precision@20 (LIMIT 안에 진짜 근거 있는 성분 비율): **0.74**
- GraphRAG 평균 Recall@20 (전체 근거 있는 성분 중 LIMIT 안에 들어온 비율): **0.76**
- GraphRAG 평균 NDCG@20 (ORDER BY가 근거 있는 성분을 앞에 배치하는 정도): **0.96**
- 기존 빈도 베이스라인(`gold_ingredient_frequency`, concern 무관 전역 인기도) 평균 Recall: **0.026**

해석: ORDER BY 로직 자체(NDCG≈1.0)는 올바르게 동작한다 — 근거 있는 성분을 앞에 배치하는 데는 문제가 없다. 다만 ACNE/COMEDONES/PORE_CONGESTION/ENLARGED_PORES/OILY_SKIN/ROUGH_TEXTURE처럼 그래프에 논문 근거 성분이 원래 적은(gold 2~5개) concern은 LIMIT 20 슬롯 대부분이 약한 근거로 채워진다(Precision@20 0.10~0.25) — 이는 랭킹 버그가 아니라 데이터 자체의 근거 부족.

기존의 concern-무관 인기도 베이스라인은 평균 Recall이 2.6%로, 그래프 기반 경로 탐색이 실제로 "의미적으로 맞는" 후보를 찾아내는 데 훨씬 효과적임을 수치로 보여준다 (다만 이 비교는 같은 그래프의 evidence_type/graph_score를 정답 기준으로 쓰기 때문에, 그래프 데이터 자체가 잘못된 경우는 잡아내지 못한다 — §1의 RELATES_TO 불일치가 그런 사례).

## 4. 발견된 문제 정리 (4evr0-server에 수정 권고)

1. **POST_ACNE_MARKS 매핑 불일치**: `CONCERN_EFFECT_MAP`이 그래프의 RELATES_TO와 다른 effect(`WOUND_HEALING`)를 쓰고 있음 — 어느 쪽이 맞는지 도메인 검토 필요.
2. **그래프 RELATES_TO 8개 Concern 누락**: 실서비스 영향은 없지만, 그래프가 README에 문서화된 스키마와 불일치 — 데이터 정합성 문제로 별도 정리 필요.
3. **top-20 중복 성분으로 인한 다양성 손실**: 20/26 concern에서 발생. `query_ingredients_by_effects`의 `RETURN DISTINCT`를 성분 이름 기준으로 한 번 더 dedup하거나 (예: `WITH i, collect(...) ... `), Cypher 단계에서 성분당 가장 강한 근거 1건만 남기도록 수정하면 동일한 LIMIT 20으로 더 많은 distinct 성분을 보여줄 수 있음.
4. **DULLNESS 근거 부족**: 그래프에 pubmed_evidence 성분이 0개 — 데이터 보강(논문 근거 수집) 대상으로 우선순위 검토.

## 5. 이번에 다루지 않은 것

- **4evr0-server 코드 수정**: 위 발견(특히 POST_ACNE_MARKS 매핑 불일치, 그래프 RELATES_TO 누락)에 대한 수정은 별도 저장소(`4EVR0-Server`)에서 진행해야 함 — 이번 평가는 읽기 전용 진단.
- **RAG(벡터 검색) 베이스라인**: 생략. 이유는 평가 방법론상 `graph_score`/`evidence_type`을 정답 기준으로 쓰는 한, 구조화된 근거 신호가 없는 순수 벡터 유사도 검색은 애초에 이 정답 기준과 정합성이 낮게 나올 수밖에 없어(같은 잣대로 재면 불리), RAG 자체의 한계가 아니라 평가 설계의 편향처럼 보일 위험이 있음. 별도의 (텍스트 기반) 정답 기준을 마련한 뒤 재검토 필요.