# 성분 추천 중복 슬롯 문제 수정 (2026-06-29)

## 기존 문제

`query_ingredients_by_effects`는 `UNWIND $effects`로 concern에 매핑된 effect들을 하나씩 풀어서
`(Ingredient)-[:AFFECTS]->(Effect)` 를 매치한 뒤, 결과 전체에 `RETURN DISTINCT`를 적용했다.

`RETURN DISTINCT`는 **행 전체**(`이름, claim, evidence_type, graph_score, ...`)를 기준으로 중복을 제거한다.
그래서 한 성분이 여러 effect에 동시에 매치되면 — 예: 나이아신아마이드가 BRIGHTENING과 DEPIGMENTING 양쪽에 근거가 있을 때 —
`(나이아신아마이드, BRIGHTENING, pubmed_evidence, ...)`, `(나이아신아마이드, DEPIGMENTING, pubmed_evidence, ...)` 두 행이
서로 다른 행으로 간주되어 **LIMIT 20 슬롯을 각각 차지**했다.

결과적으로 사용자에게 보여지는 **실제 distinct 성분 수는 20보다 적었다**.
평가기 기준으로 26개 concern 중 **20개**에서 이 현상이 발생했다.

예시:
- SENSITIVE_SKIN: 행 반환 20건 → distinct 성분 **14개** (6슬롯을 중복이 잠식)
- ATOPIC_PRONE: 행 반환 20건 → distinct 성분 **14개**
- BARRIER_DAMAGE: 행 반환 20건 → distinct 성분 **14개**

## 수정 방법

`RETURN DISTINCT` 대신 Cypher의 `head(collect())` 패턴으로 **성분(i) 단위로 집계**했다.
먼저 `ORDER BY ev_rank, graph_score DESC`로 evidence 품질 기준 정렬 후,
`WITH i, head(collect({...})) AS best`로 성분당 가장 강한 근거 1건만 남긴다.
이후 `LIMIT 20`을 적용하면 **항상 20개 고유 성분**이 반환된다.

수정 전 쿼리 핵심:
```cypher
UNWIND $effects AS effect_code
MATCH (i:Ingredient)-[r:AFFECTS]->(e:Effect {effect_code: effect_code})
RETURN DISTINCT i.inci_name AS name, e.effect_name_en AS claim, r.evidence_type AS eligibility_tier, ...
ORDER BY CASE r.evidence_type WHEN 'pubmed_evidence' THEN 0 ELSE 1 END, r.graph_score DESC
LIMIT 20
-- → 같은 성분이 여러 effect로 매치되면 중복 행이 LIMIT을 낭비
```

수정 후 쿼리 핵심:
```cypher
UNWIND $effects AS effect_code
MATCH (i:Ingredient)-[r:AFFECTS]->(e:Effect {effect_code: effect_code})
WITH i, e, r, CASE r.evidence_type WHEN 'pubmed_evidence' THEN 0 ELSE 1 END AS ev_rank
ORDER BY ev_rank, r.graph_score DESC
WITH i, head(collect({claim: e.effect_name_en, eligibility_tier: r.evidence_type, ...})) AS best
RETURN i.inci_name AS name, best.claim AS claim, best.eligibility_tier AS eligibility_tier, ...
ORDER BY best.ev_rank, best.graph_score DESC
LIMIT 20
-- → i 기준 집계이므로 성분 1개 = 행 1개, LIMIT 20 = distinct 성분 20개
```

수정 파일:
- `eval/graphrag_ranking_eval.py` — `INGREDIENTS_BY_EFFECTS_QUERY` 상수
- `4EVR0-Server/app/clients/neo4j_client.py` — `query_ingredients_by_effects` 내 query 문자열

## 수정 결과

중복 성분이 있는 concern: **20/26 → 0/26** (완전 해결)

| concern | Before distinct | After distinct | 증가 |
|---|---:|---:|---:|
| SENSITIVE_SKIN | 14 | 20 | +6 |
| ATOPIC_PRONE | 14 | 20 | +6 |
| BARRIER_DAMAGE | 14 | 20 | +6 |
| IRRITATED_SKIN | 15 | 20 | +5 |
| AGING_SIGNS | 15 | 20 | +5 |
| DRY_SKIN | 17 | 20 | +3 |
| DEHYDRATED_SKIN | 17 | 20 | +3 |
| FLAKY_SKIN | 17 | 20 | +3 |
| WRINKLES | 17 | 20 | +3 |
| HYPERPIGMENTATION | 18 | 20 | +2 |
| LOSS_OF_ELASTICITY | 18 | 20 | +2 |
| SAGGING_SKIN | 18 | 20 | +2 |
| ACNE | 19 | 20 | +1 |
| REDNESS | 19 | 20 | +1 |
| ROSACEA_PRONE | 19 | 20 | +1 |
| SUNBURN | 19 | 20 | +1 |
| UNEVEN_SKIN_TONE | 13 | 13 | 0 (원래 13개뿐) |
| DARK_CIRCLES | 13 | 13 | 0 |
| BLEMISHES | 15 | 15 | 0 |
| POST_ACNE_MARKS | 15 | 15 | 0 |

> UNEVEN_SKIN_TONE / DARK_CIRCLES의 반환 행이 15 → 13으로 줄어 보이지만,
> 이전 15는 중복으로 부풀려진 숫자였고 실제 distinct 성분은 처음부터 13개였다 — 퇴보 아님.

전체 평가 지표(NDCG=1.00, 성분 0건=0, 제품 0건=0)는 수정 전과 동일하게 유지.

## 다음 작업

- [ ] **작업 2**: 제품 카테고리 적합성 평가 추가 (평가기가 못 재는 공백)
- [ ] **작업 3**: POST_ACNE_MARKS 매핑 불일치 — 운영 코드 `WOUND_HEALING` vs 그래프 `ANTI_INFLAMMATORY` 검토
- [ ] **작업 4 (장기)**: 그래프 RELATES_TO 8개 concern 누락 보강, DULLNESS pubmed_evidence 0개 해결
