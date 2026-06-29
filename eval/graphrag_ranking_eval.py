"""
운영 코드(4evr0-server app/clients/neo4j_client.py)의 Cypher를 그대로 복제해
26개 concern 전체에 대해 돌려보고 두 가지를 측정한다.

1. 경로 탐색 커버리지 (핵심 지표): 이 concern으로 추천을 요청하면 성분/제품이
   "한 건이라도" 나오는가? 0건이면 경로가 정답을 전혀 못 내놓는 것 (랭킹 문제 이전의 문제).
2. LIMIT 내 정렬 품질 (보조 지표): 결과가 나온다면, evidence_type/graph_score 기준으로
   좋은 항목이 상위에 오는가 (Precision@K, NDCG@K).
"""

import math

from gold_labels import PRODUCTION_CONCERN_EFFECT_MAP, fetch_all_affects, get_driver

# app/clients/neo4j_client.py query_ingredients_by_effects 그대로 복제 (2026-06-29 dedup 수정)
# 변경 이유: RETURN DISTINCT가 (이름, claim, evidence_type, ...) 행 전체 기준으로 동작해
# 한 성분이 여러 effect로 매치되면 LIMIT 20 슬롯을 중복으로 차지하는 문제를 수정.
# head(collect())로 성분당 최강 근거 1건만 남겨 LIMIT 20 = distinct 성분 20개를 보장한다.
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
RETURN
    i.inci_name           AS name,
    i.kor_name            AS kor_name,
    best.claim            AS claim,
    best.eligibility_tier AS eligibility_tier,
    best.paper_ref        AS paper_ref,
    best.graph_score      AS graph_score
ORDER BY best.ev_rank, best.graph_score DESC, i.inci_name
LIMIT 20
"""

# app/clients/neo4j_client.py query_products_by_ingredients 그대로 복제 (2026-06-24 기준)
PRODUCTS_BY_INGREDIENTS_QUERY = """
UNWIND $ingredient_names AS ing_name
MATCH (prod:Product)-[:CONTAINS]->(i:Ingredient {inci_name: ing_name})
WITH prod,
     COUNT(DISTINCT i.inci_name) AS matched_count,
     COLLECT(DISTINCT i.inci_name) AS matched_ingredients
ORDER BY matched_count DESC, prod.product_name
LIMIT 5
RETURN prod.product_id AS product_id, matched_count AS matched_count
"""


def ndcg_at_k(relevances: list[int]) -> float:
    """relevances: 반환된 순서대로의 관련성(0/1) 리스트."""
    if not relevances or sum(relevances) == 0:
        return 0.0
    dcg = sum(rel / math.log2(idx + 2) for idx, rel in enumerate(relevances))
    ideal = sorted(relevances, reverse=True)
    idcg = sum(rel / math.log2(idx + 2) for idx, rel in enumerate(ideal))
    return dcg / idcg if idcg > 0 else 0.0


def evaluate_concern(driver, affects_df, concern: str, effects: list[str]) -> dict:
    # 운영 쿼리는 UNWIND $effects + MATCH per effect_code로 (ingredient, effect) 쌍 단위 row를
    # 만든 뒤 DISTINCT를 적용한다. recall/precision을 같은 기준으로 비교하려면 여기서도
    # ingredient 이름으로 미리 dedup하면 안 된다 (해뒀다가 gold 카운트가 어긋나 recall > 1이 나왔음).
    candidates = affects_df[affects_df["effect_code"].isin(effects)]
    candidate_total = len(candidates)
    candidate_gold = int(candidates["is_gold"].sum())

    with driver.session() as session:
        ranked = session.run(INGREDIENTS_BY_EFFECTS_QUERY, effects=effects).data()

    returned_total = len(ranked)
    relevances = [1 if row["eligibility_tier"] == "pubmed_evidence" else 0 for row in ranked]
    gold_in_returned = sum(relevances)

    # 같은 성분이 서로 다른 effect를 통해 두 번 이상 매치되면 RETURN DISTINCT가 이름이 아니라
    # (이름, claim, evidence_type, ...) 전체 행 기준으로 동작해서 같은 성분이 LIMIT 20 안에
    # 중복으로 여러 줄을 차지할 수 있다. 사용자가 실제로 보는 "성분 개수"는 distinct 이름 기준.
    distinct_names = {row["name"] for row in ranked}

    precision_at_k = gold_in_returned / returned_total if returned_total else None
    recall_at_k = gold_in_returned / candidate_gold if candidate_gold else None
    ndcg = ndcg_at_k(relevances) if returned_total else None

    top10_names = [row["name"] for row in ranked[:10]]
    with driver.session() as session:
        products = session.run(PRODUCTS_BY_INGREDIENTS_QUERY, ingredient_names=top10_names).data()

    return {
        "concern": concern,
        "effects": effects,
        "candidate_total": candidate_total,
        "candidate_gold": candidate_gold,
        "ingredient_returned": returned_total,
        "ingredient_distinct": len(distinct_names),
        "ingredient_is_empty": returned_total == 0,
        "precision_at_k": precision_at_k,
        "recall_at_k": recall_at_k,
        "ndcg_at_k": ndcg,
        "product_returned": len(products),
        "product_is_empty": len(products) == 0,
    }


def run_all() -> list[dict]:
    driver = get_driver()
    try:
        affects_df = fetch_all_affects(driver)
        return [
            evaluate_concern(driver, affects_df, concern, effects)
            for concern, effects in PRODUCTION_CONCERN_EFFECT_MAP.items()
        ]
    finally:
        driver.close()


if __name__ == "__main__":
    results = run_all()

    print("=== concern별 경로 탐색 결과 ===")
    header = (f"{'concern':20s} {'cand':>5s} {'gold':>5s} {'ing':>4s} {'distinct':>8s} {'prod':>4s} "
               f"{'P@K':>6s} {'R@K':>6s} {'NDCG':>6s}")
    print(header)
    for r in results:
        p = f"{r['precision_at_k']:.2f}" if r["precision_at_k"] is not None else "-"
        rc = f"{r['recall_at_k']:.2f}" if r["recall_at_k"] is not None else "-"
        n = f"{r['ndcg_at_k']:.2f}" if r["ndcg_at_k"] is not None else "-"
        dup_flag = " <-- 중복 성분 있음" if r["ingredient_distinct"] < r["ingredient_returned"] else ""
        flag = " <-- 0건!" if r["ingredient_is_empty"] or r["product_is_empty"] else dup_flag
        print(f"{r['concern']:20s} {r['candidate_total']:5d} {r['candidate_gold']:5d} "
              f"{r['ingredient_returned']:4d} {r['ingredient_distinct']:8d} {r['product_returned']:4d} "
              f"{p:>6s} {rc:>6s} {n:>6s}{flag}")

    empty_ingredient = [r["concern"] for r in results if r["ingredient_is_empty"]]
    empty_product = [r["concern"] for r in results if r["product_is_empty"] and not r["ingredient_is_empty"]]
    has_duplicates = [r["concern"] for r in results if r["ingredient_distinct"] < r["ingredient_returned"]]
    print(f"\n성분 0건 concern: {len(empty_ingredient)}/{len(results)} -> {empty_ingredient}")
    print(f"성분은 있지만 제품 0건 concern: {len(empty_product)} -> {empty_product}")
    print(f"top-20 안에 중복 성분 있는 concern: {len(has_duplicates)}/{len(results)} -> {has_duplicates}")
