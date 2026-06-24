"""
Concern -> Effect -> Ingredient "정답" 후보를 그래프에서 직접 뽑아낸다.

주의: 실제 운영 코드(4evr0-server)는 (Concern)-[:RELATES_TO]->(Effect) 그래프 관계를
조회하지 않는다. 사용자 텍스트 -> Concern -> Effect 매핑은
app/services/taxonomy_normalization_service.py의 CONCERN_EFFECT_MAP(하드코딩 dict)을 쓴다.
그래서 두 가지를 모두 만들어서 비교한다:
  1. PRODUCTION_CONCERN_EFFECT_MAP : 실제 운영 코드가 쓰는 매핑 (이 파일에 복제)
  2. fetch_graph_concern_effect_map() : 그래프 자체의 RELATES_TO 관계
"""

import os

import pandas as pd
from neo4j import GraphDatabase

# 4evr0-server app/services/taxonomy_normalization_service.py CONCERN_EFFECT_MAP 복제
# (2026-06-24 기준, /tmp/4evr0-server git head). 운영 코드를 수정하지 않고 비교만 하기 위해
# 여기서는 문자열 dict로 재현한다.
PRODUCTION_CONCERN_EFFECT_MAP: dict[str, list[str]] = {
    "ACNE": ["ANTI_INFLAMMATORY", "SEBUM_REGULATION", "KERATOLYTIC", "COMEDOLYTIC", "ANTIMICROBIAL"],
    "COMEDONES": ["KERATOLYTIC", "COMEDOLYTIC", "SEBUM_REGULATION"],
    "PORE_CONGESTION": ["KERATOLYTIC", "COMEDOLYTIC", "SEBUM_REGULATION"],
    "ENLARGED_PORES": ["SEBUM_REGULATION", "KERATOLYTIC"],
    "OILY_SKIN": ["SEBUM_REGULATION", "ANTI_INFLAMMATORY"],
    "SENSITIVE_SKIN": ["SOOTHING", "ANTI_INFLAMMATORY", "BARRIER_REPAIR", "HYDRATING"],
    "REDNESS": ["ANTI_INFLAMMATORY", "SOOTHING"],
    "IRRITATED_SKIN": ["ANTI_INFLAMMATORY", "SOOTHING", "BARRIER_REPAIR"],
    "ATOPIC_PRONE": ["ANTI_INFLAMMATORY", "SOOTHING", "BARRIER_REPAIR", "HYDRATING"],
    "ROSACEA_PRONE": ["ANTI_INFLAMMATORY", "SOOTHING"],
    "DRY_SKIN": ["HYDRATING", "MOISTURE_RETENTION", "BARRIER_REPAIR"],
    "DEHYDRATED_SKIN": ["HYDRATING", "MOISTURE_RETENTION"],
    "FLAKY_SKIN": ["HYDRATING", "KERATOLYTIC", "MOISTURE_RETENTION"],
    "ROUGH_TEXTURE": ["KERATOLYTIC", "MOISTURE_RETENTION"],
    "BARRIER_DAMAGE": ["BARRIER_REPAIR", "HYDRATING", "MOISTURE_RETENTION", "SOOTHING"],
    "HYPERPIGMENTATION": ["DEPIGMENTING", "BRIGHTENING", "ANTI_INFLAMMATORY"],
    "DULLNESS": ["BRIGHTENING", "KERATOLYTIC", "ANTIOXIDANT"],
    "UNEVEN_SKIN_TONE": ["BRIGHTENING", "DEPIGMENTING"],
    "BLEMISHES": ["DEPIGMENTING", "BRIGHTENING", "WOUND_HEALING"],
    "POST_ACNE_MARKS": ["DEPIGMENTING", "BRIGHTENING", "WOUND_HEALING"],
    "DARK_CIRCLES": ["DEPIGMENTING", "BRIGHTENING"],
    "SUNBURN": ["PHOTOPROTECTIVE", "ANTIOXIDANT", "SOOTHING"],
    "AGING_SIGNS": ["ANTI_AGING", "ANTIOXIDANT"],
    "WRINKLES": ["ANTI_AGING", "HYDRATING"],
    "LOSS_OF_ELASTICITY": ["ANTI_AGING", "MOISTURE_RETENTION"],
    "SAGGING_SKIN": ["ANTI_AGING"],
}


def get_driver() -> GraphDatabase.driver:
    return GraphDatabase.driver(
        os.environ.get("NEO4J_BOLT_URI", "bolt://localhost:7687"),
        auth=(os.environ.get("NEO4J_USER", "neo4j"), os.environ["NEO4J_PASSWORD"]),
    )


def fetch_graph_concern_effect_map(driver) -> dict[str, set[str]]:
    """그래프 자체의 (Effect)-[:RELATES_TO]->(Concern) 관계 기준 매핑."""
    with driver.session() as session:
        rows = session.run(
            "MATCH (e:Effect)-[:RELATES_TO]->(c:Concern) "
            "RETURN c.concern_code AS concern, e.effect_code AS effect"
        ).data()
    result: dict[str, set[str]] = {}
    for row in rows:
        result.setdefault(row["concern"], set()).add(row["effect"])
    return result


def fetch_all_concern_nodes(driver) -> set[str]:
    with driver.session() as session:
        rows = session.run("MATCH (c:Concern) RETURN c.concern_code AS code").data()
    return {r["code"] for r in rows}


def compare_concern_effect_sources(driver) -> list[dict]:
    """그래프 RELATES_TO vs 운영 코드 CONCERN_EFFECT_MAP 불일치를 찾는다."""
    graph_map = fetch_graph_concern_effect_map(driver)
    graph_concerns = fetch_all_concern_nodes(driver)

    findings = []
    for concern in sorted(graph_concerns):
        graph_effects = graph_map.get(concern, set())
        prod_effects = set(PRODUCTION_CONCERN_EFFECT_MAP.get(concern, []))
        findings.append({
            "concern": concern,
            "graph_relates_to_effects": sorted(graph_effects),
            "production_map_effects": sorted(prod_effects),
            "graph_has_no_relates_to": len(graph_effects) == 0,
            "sets_match": graph_effects == prod_effects,
            "only_in_graph": sorted(graph_effects - prod_effects),
            "only_in_production": sorted(prod_effects - graph_effects),
        })
    return findings


def fetch_all_affects(driver) -> pd.DataFrame:
    """(Ingredient)-[:AFFECTS]->(Effect) 전체를 LIMIT 없이 가져온다 (후보 전체 집합)."""
    with driver.session() as session:
        rows = session.run(
            """
            MATCH (i:Ingredient)-[r:AFFECTS]->(e:Effect)
            RETURN i.inci_name AS inci_name, i.kor_name AS kor_name,
                   e.effect_code AS effect_code,
                   r.evidence_type AS evidence_type,
                   r.graph_score AS graph_score,
                   r.paper_count AS paper_count
            """
        ).data()
    df = pd.DataFrame(rows)
    df["is_gold"] = df["evidence_type"] == "pubmed_evidence"
    return df


def build_gold_ingredients_per_concern(affects_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """운영 코드의 CONCERN_EFFECT_MAP을 기준으로, concern별 후보 성분 전체(LIMIT 없음)를 만든다."""
    result = {}
    for concern, effects in PRODUCTION_CONCERN_EFFECT_MAP.items():
        subset = affects_df[affects_df["effect_code"].isin(effects)].drop_duplicates("inci_name")
        result[concern] = subset
    return result


if __name__ == "__main__":
    driver = get_driver()
    try:
        print("=== 1. 그래프 RELATES_TO vs 운영 코드 CONCERN_EFFECT_MAP 비교 ===")
        findings = compare_concern_effect_sources(driver)
        for f in findings:
            if f["graph_has_no_relates_to"]:
                print(f"  [그래프에 RELATES_TO 없음] {f['concern']}")
            elif not f["sets_match"]:
                print(f"  [불일치] {f['concern']}: graph={f['graph_relates_to_effects']} "
                      f"vs production={f['production_map_effects']}")
        no_relates_to = [f["concern"] for f in findings if f["graph_has_no_relates_to"]]
        mismatched = [f["concern"] for f in findings if not f["graph_has_no_relates_to"] and not f["sets_match"]]
        print(f"\n  RELATES_TO 없는 Concern: {len(no_relates_to)}/{len(findings)} -> {no_relates_to}")
        print(f"  매핑 불일치 Concern: {len(mismatched)} -> {mismatched}")

        print("\n=== 2. AFFECTS 전체 후보 집합 ===")
        affects_df = fetch_all_affects(driver)
        print(f"  AFFECTS 전체 row 수: {len(affects_df)}")
        print(f"  pubmed_evidence(gold) row 수: {affects_df['is_gold'].sum()}")
    finally:
        driver.close()
