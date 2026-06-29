# 제품 카테고리 적합성 수정 결과 (2026-06-29)

## 기존 문제

`query_products_by_ingredients`는 "성분 일치 수(matched_count)"만으로 제품 순위를 매기고
제품 카테고리를 전혀 고려하지 않았다.

결과적으로 씻어내는 제품(클렌징폼/오일 등)이나 고민과 맞지 않는 제형(여드름 고민에 크림·아이크림)이
상위에 노출되는 문제가 있었다. 예를 들어:

- **COMEDONES/PORE_CONGESTION/ENLARGED_PORES**: 추천 5개 제품이 **전부 크림(아이크림 포함)**
  - AHC 유스 래스팅 리얼 아이크림, AHC 텐 레볼루션 아이크림 등이 모공 고민에 추천됨
  - Category Precision@5 = **0.00** (5개 중 적합한 제품 0개)
- **REDNESS/ROSACEA_PRONE**: 클렌징폼(스콧해미쉬 블루 프리덤 캡슐 클렌징폼)이 추천됨
- **LOSS_OF_ELASTICITY**: 클렌져 제품(메디필 멜라논 엑스 앰플 클렌저)이 추천됨

평균 Category Precision@5: **0.82** (26개 concern 중 8개에서 부적합 제품 포함)

## 수정 방법

### 1. `neo4j_client.py` — `query_products_by_ingredients`에 카테고리 필터 파라미터 추가

- `appropriate_categories: list[str] | None` 인자 추가
- 전달 시 `WHERE prod.category IN $appropriate_categories` 필터 적용
- 미전달 시 클렌징 계열(씻어내는 제품)만 기본 제외: `WHERE NOT prod.category IN $cleansers`

### 2. `recommend_service.py` — concern → 카테고리 매핑 추가 및 쿼리에 전달

```python
_CONCERN_CATEGORY_MAP = {
    Concern.ACNE:            세럼/앰플/에센스/로션/토너/미스트/올인원/필링스크럽  # 크림 제외
    Concern.COMEDONES:       세럼/앰플/에센스/로션/토너/미스트/올인원           # 크림 제외
    Concern.PORE_CONGESTION: (동일)
    Concern.ENLARGED_PORES:  (동일)
    Concern.OILY_SKIN:       (동일)
    Concern.FLAKY_SKIN:      전체 + 페이스오일/필링스크럽
    Concern.ROUGH_TEXTURE:   전체 + 필링스크럽
    Concern.DRY_SKIN:        전체 + 페이스오일
    ...기타 concern: 기본 leave-on 제품 전체
}
```

복수 concern이 있으면 **교집합**으로 가장 엄격한 조건 적용.

## 수정 결과

평균 Category Precision@5: **0.82 → 1.00** (+0.18)

| 구분 | Before | After |
|---|---|---|
| CP@5 = 1.00 (완전 적합) | 18/26 | **26/26** |
| CP@5 < 1.00 (부적합 포함) | 8/26 | **0/26** |
| 평균 CP@5 | 0.82 | **1.00** |

주요 개선 concern:

| concern | Before CP@5 | After CP@5 | 이유 |
|---|---|---|---|
| COMEDONES | 0.00 | 1.00 | 크림 필터 → 세럼/토너 계열로 교체 |
| PORE_CONGESTION | 0.00 | 1.00 | 동일 |
| ENLARGED_PORES | 0.00 | 1.00 | 동일 |
| ACNE | 0.40 | 1.00 | 크림 필터 |
| OILY_SKIN | 0.40 | 1.00 | 크림 필터 |
| REDNESS | 0.80 | 1.00 | 클렌징폼 필터 |
| ROSACEA_PRONE | 0.80 | 1.00 | 클렌징폼 필터 |
| LOSS_OF_ELASTICITY | 0.80 | 1.00 | 클렌징폼 필터 |

## 수정 파일

- `eval/product_category_eval.py` — 평가 스크립트 신규 작성 (before/after 비교)
- `4EVR0-Server/app/clients/neo4j_client.py` — `appropriate_categories` 파라미터 추가
- `4EVR0-Server/app/services/recommend_service.py` — `_CONCERN_CATEGORY_MAP` + `_appropriate_categories()` 추가, 쿼리 호출 시 카테고리 전달

## 추가 발견: 제품 중복 노출

COMEDONES/PORE_CONGESTION에서 "AHC 유스 래스팅 리얼 아이크림 포"가 동일 이름으로 2번 등장했다.
같은 제품이 여러 `product_id`로 등록된 데이터 중복으로 보인다 (product_id 기반 LIMIT이라 이름 중복이 걸러지지 않음).
카테고리 필터로 이 제품들이 제외되면서 현재는 체감 문제가 없으나, 추후 제품명 기준 dedup도 검토할 것.

## 다음 작업

- [ ] **작업 3**: POST_ACNE_MARKS 매핑 불일치 — 운영 코드 `WOUND_HEALING` vs 그래프 `ANTI_INFLAMMATORY` 검토
- [ ] **작업 4 (장기)**: RELATES_TO 8개 Concern 누락 보강, DULLNESS pubmed_evidence 0개 해결
- [ ] 제품명 기준 dedup (product_id 중복 문제)
