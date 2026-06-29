# 제품 중복 노출 수정 (2026-06-29)

## 기존 문제

`query_products_by_ingredients`는 `prod`(Product 노드) 단위로 집계하기 때문에,
같은 제품명이 서로 다른 `product_id`로 그래프에 등록되어 있으면 LIMIT 5 안에 같은 이름이 2번 나왔다.

예) COMEDONES 고민 추천 결과 (수정 전):
```
AHC 유스 래스팅 리얼 아이크림 포 페이스  크림  2개 매칭
AHC 유스 래스팅 리얼 아이크림 포 페이스  크림  2개 매칭  ← 동일 제품 중복
AHC 텐 레볼루션 리얼 아이크림 포 페이스  크림  2개 매칭
AHC 텐 레볼루션 리얼 아이크림 포 페이스  크림  2개 매칭  ← 동일 제품 중복
CKD 레티노콜라겐 저분자 300 크림        크림  2개 매칭
```

사용자 입장에선 5개 추천 중 실제 다른 제품은 3개뿐인 상황.

카테고리 필터(RESULTS_category_fix.md) 수정으로 크림이 필터링되면서
눈에 보이는 중복은 사라졌지만, 근본 원인(product_name 기준 dedup 미적용)은 그대로였다.
크림이 허용되는 고민(DRY_SKIN, SENSITIVE_SKIN 등)에서는 여전히 발생 가능한 구조.

## 수정 방법

쿼리 중간에 `product_name` 기준으로 한 번 더 집계해, 이름이 같은 제품 중
matched_count가 가장 높은(= ORDER BY 후 첫 번째) 1건만 남기도록 했다.

수정 전 쿼리 핵심:
```cypher
WITH prod,
     COUNT(DISTINCT i.inci_name) AS matched_count, ...
ORDER BY matched_count DESC, prod.product_name
LIMIT 5
-- → product_id 기준 집계라 동일 이름 제품이 LIMIT 5 안에 여러 번 등장 가능
```

수정 후 쿼리 핵심:
```cypher
WITH prod,
     COUNT(DISTINCT i.inci_name) AS matched_count, ...
ORDER BY matched_count DESC, prod.product_name
WITH prod.product_name AS product_name,
     head(collect(prod))               AS prod,
     head(collect(matched_count))      AS matched_count,
     head(collect(matched_ingredients)) AS matched_ingredients
RETURN prod.product_id AS product_id, product_name, ...
ORDER BY matched_count DESC, product_name
LIMIT 5
-- → product_name 기준 dedup 후 LIMIT → 이름 기준 고유 5개 보장
```

수정 파일:
- `4EVR0-Server/app/clients/neo4j_client.py` — `query_products_by_ingredients`

## 수정 결과

동일 이름 제품 중복 노출 해소. LIMIT 5 = 이름 기준 고유 5개 제품 보장.

## 참고

이 문제가 눈에 잘 안 띄었던 이유:
- `product_category_eval.py` 평가가 카테고리 적합성만 측정하고 중복 여부는 별도 체크 안 함
- 카테고리 필터로 크림이 제외되면서 AHC 아이크림 중복 케이스가 자연히 사라졌던 것

중복 노출이 완전히 사라졌는지 확인하려면 평가기에 `product_name` 중복 체크 컬럼 추가 검토 가능.
