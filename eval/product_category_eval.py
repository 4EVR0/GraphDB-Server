"""
작업 2: 제품 카테고리 적합성 평가

graphrag_ranking_eval.py가 측정하지 못하는 공백을 채운다.
"추천된 5개 제품의 카테고리가 고민에 맞는가?" — Category Precision@5

배경
----
query_products_by_ingredients는 matched_count(성분 일치 수)만으로 순위를 매기고
제품 카테고리를 전혀 고려하지 않는다.
클렌징폼/오일/밤 등 클렌징 계열은 씻어내는 제품이라 성분 흡수 효과가 다르고
사용자가 기대하는 "스킨케어 추천"과 거리가 멀다.
이 스크립트는 concern별로 카테고리 적합성을 측정해 문제 범위를 정량화한다.
"""

import os
import sys

from neo4j import GraphDatabase

from gold_labels import PRODUCTION_CONCERN_EFFECT_MAP

# ------------------------------------------------------------
# concern → 적합한 카테고리 집합 (도메인 룰 정의)
# 기준: 씻어내지 않는 leave-on 제품 = 기본 적합
#        클렌징 계열 = 대부분 고민에 부적합 (씻어냄)
#        필링스크럽 = 각질/피부결 고민에만 적합
#        페이스오일 = 건성/장벽 계열에 적합, 지성/여드름엔 부적합
# ------------------------------------------------------------
_LEAVE_ON = {"크림", "세럼", "앰플", "에센스", "로션", "토너", "미스트", "올인원"}
_CLEANSERS = {"클렌징폼", "클렌징오일", "클렌징밤", "클렌징젤", "클렌징워터", "클렌징밀크"}

CONCERN_CATEGORY_MAP: dict[str, set[str]] = {
    # 여드름/모공/지성 — 유분 많은 제품(크림, 페이스오일) 부적합
    "ACNE":           _LEAVE_ON - {"크림"} | {"필링스크럽"},
    "COMEDONES":      _LEAVE_ON - {"크림"},
    "PORE_CONGESTION":_LEAVE_ON - {"크림"},
    "ENLARGED_PORES": _LEAVE_ON - {"크림"},
    "OILY_SKIN":      _LEAVE_ON - {"크림"},
    # 민감성/염증 — 자극적인 필링 부적합
    "SENSITIVE_SKIN": _LEAVE_ON,
    "REDNESS":        _LEAVE_ON,
    "IRRITATED_SKIN": _LEAVE_ON,
    "ATOPIC_PRONE":   _LEAVE_ON,
    "ROSACEA_PRONE":  _LEAVE_ON,
    # 건성/수분/장벽 — 페이스오일도 적합
    "DRY_SKIN":         _LEAVE_ON | {"페이스오일"},
    "DEHYDRATED_SKIN":  _LEAVE_ON | {"페이스오일"},
    "FLAKY_SKIN":       _LEAVE_ON | {"페이스오일", "필링스크럽"},
    "ROUGH_TEXTURE":    _LEAVE_ON | {"필링스크럽"},
    "BARRIER_DAMAGE":   _LEAVE_ON | {"페이스오일"},
    # 미백/색소침착
    "HYPERPIGMENTATION": _LEAVE_ON,
    "DULLNESS":          _LEAVE_ON,
    "UNEVEN_SKIN_TONE":  _LEAVE_ON,
    "BLEMISHES":         _LEAVE_ON,
    "POST_ACNE_MARKS":   _LEAVE_ON,
    "DARK_CIRCLES":      _LEAVE_ON,
    # 선번
    "SUNBURN": _LEAVE_ON,
    # 노화
    "AGING_SIGNS":       _LEAVE_ON,
    "WRINKLES":          _LEAVE_ON,
    "LOSS_OF_ELASTICITY":_LEAVE_ON,
    "SAGGING_SKIN":      _LEAVE_ON,
}

INGREDIENTS_BY_EFFECTS_QUERY = """
UNWIND $effects AS effect_code
MATCH (i:Ingredient)-[r:AFFECTS]->(e:Effect {effect_code: effect_code})
WITH i, e, r,
     CASE r.evidence_type WHEN 'pubmed_evidence' THEN 0 ELSE 1 END AS ev_rank
ORDER BY ev_rank, r.graph_score DESC
WITH i,
     head(collect({
         claim:            e.effect_name_en,
         eligibility_tier: r.evidence_type,
         paper_ref:        toString(r.paper_count),
         graph_score:      r.graph_score,
         ev_rank:          ev_rank
     })) AS best
RETURN i.inci_name AS name
ORDER BY best.ev_rank, best.graph_score DESC, i.inci_name
LIMIT 20
"""

PRODUCTS_BY_INGREDIENTS_QUERY = """
UNWIND $ingredient_names AS ing_name
MATCH (prod:Product)-[:CONTAINS]->(i:Ingredient {inci_name: ing_name})
WITH prod,
     COUNT(DISTINCT i.inci_name) AS matched_count,
     COLLECT(DISTINCT i.inci_name) AS matched_ingredients
ORDER BY matched_count DESC, prod.product_name
LIMIT 5
RETURN
    prod.product_id   AS product_id,
    prod.product_name AS product_name,
    prod.category     AS category,
    matched_count     AS matched_count
"""

# 카테고리 필터 적용 버전 (수정 후)
PRODUCTS_BY_INGREDIENTS_QUERY_FILTERED = """
UNWIND $ingredient_names AS ing_name
MATCH (prod:Product)-[:CONTAINS]->(i:Ingredient {inci_name: ing_name})
WHERE prod.category IN $appropriate_categories
WITH prod,
     COUNT(DISTINCT i.inci_name) AS matched_count,
     COLLECT(DISTINCT i.inci_name) AS matched_ingredients
ORDER BY matched_count DESC, prod.product_name
LIMIT 5
RETURN
    prod.product_id   AS product_id,
    prod.product_name AS product_name,
    prod.category     AS category,
    matched_count     AS matched_count
"""


def get_driver():
    return GraphDatabase.driver(
        os.environ.get("NEO4J_BOLT_URI", "bolt://localhost:7687"),
        auth=(os.environ.get("NEO4J_USER", "neo4j"), os.environ["NEO4J_PASSWORD"]),
    )


def evaluate_concern(driver, concern: str, effects: list[str], use_filter: bool = False) -> dict:
    appropriate_cats = CONCERN_CATEGORY_MAP.get(concern, _LEAVE_ON)

    with driver.session() as s:
        ing_rows = s.run(INGREDIENTS_BY_EFFECTS_QUERY, effects=effects).data()

    top10_names = [r["name"] for r in ing_rows[:10]]

    if not top10_names:
        return {
            "concern": concern,
            "products": [],
            "category_precision": None,
            "inappropriate": [],
            "note": "성분 0건 — 제품 쿼리 불가",
        }

    with driver.session() as s:
        if use_filter:
            prod_rows = s.run(
                PRODUCTS_BY_INGREDIENTS_QUERY_FILTERED,
                ingredient_names=top10_names,
                appropriate_categories=list(appropriate_cats),
            ).data()
        else:
            prod_rows = s.run(PRODUCTS_BY_INGREDIENTS_QUERY, ingredient_names=top10_names).data()

    inappropriate = [
        {"name": r["product_name"], "category": r["category"]}
        for r in prod_rows
        if r["category"] not in appropriate_cats
    ]
    cp = (len(prod_rows) - len(inappropriate)) / len(prod_rows) if prod_rows else None

    return {
        "concern": concern,
        "products": [{"name": r["product_name"], "category": r["category"]} for r in prod_rows],
        "category_precision": cp,
        "inappropriate": inappropriate,
        "note": "",
    }


def run_all(use_filter: bool = False) -> list[dict]:
    driver = get_driver()
    try:
        return [
            evaluate_concern(driver, concern, effects, use_filter=use_filter)
            for concern, effects in PRODUCTION_CONCERN_EFFECT_MAP.items()
        ]
    finally:
        driver.close()


def print_results(results: list[dict], label: str) -> float:
    print(f"\n=== {label} ===\n")
    header = f"{'concern':20s}  {'CP@5':>5s}  {'부적합 제품'}"
    print(header)
    print("-" * 80)
    for r in results:
        cp = f"{r['category_precision']:.2f}" if r["category_precision"] is not None else "  -  "
        bad = ", ".join(f"{p['name'][:20]}({p['category']})" for p in r["inappropriate"])
        flag = "  <-- 주의" if r["inappropriate"] else ""
        print(f"{r['concern']:20s}  {cp:>5s}  {bad}{flag}")

    perfect = [r for r in results if r["category_precision"] == 1.0]
    imperfect = [r for r in results if r["category_precision"] is not None and r["category_precision"] < 1.0]
    avg = sum(r["category_precision"] for r in results if r["category_precision"] is not None) / len(results)
    print(f"\nCP@5 = 1.00: {len(perfect)}/{len(results)}  |  CP@5 < 1.00: {len(imperfect)}/{len(results)}  |  평균 CP@5: {avg:.2f}")
    return avg


if __name__ == "__main__":
    before = run_all(use_filter=False)
    after  = run_all(use_filter=True)

    avg_before = print_results(before, "Before — 카테고리 필터 없음 (현재 운영)")
    avg_after  = print_results(after,  "After  — concern 카테고리 필터 적용")

    print(f"\n{'='*50}")
    print(f"평균 CP@5: {avg_before:.2f} → {avg_after:.2f}  (개선 +{avg_after - avg_before:.2f})")
