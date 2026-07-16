"""프로덕션 Cypher 쿼리 3종(4EVR0-Server/app/clients/neo4j_client.py)과
동등한 결과를 내는 SQL을 나란히 둔다. Cypher 쪽은 원본을 그대로 복사했고
(로직을 바꾸면 벤치마크 의미가 없어지므로), SQL은 같은 schema.sql 테이블 기준으로
동일한 필터/정렬/LIMIT를 재현한 것.

원본이 바뀌면 이 파일도 다시 맞춰야 한다.
"""

# ── 1. query_products_by_ingredients ────────────────────────────────────
# 핵심 성분을 가장 많이 포함한 제품 top 5.
# Neo4j: product_name으로 dedup(head(collect())) 후 matched_count DESC, product_name 정렬.

CYPHER_PRODUCTS_BY_INGREDIENTS = """
UNWIND $ingredient_names AS ing_name
MATCH (prod:Product)-[:CONTAINS]->(i:Ingredient {inci_name: ing_name})
WHERE prod.category IN $appropriate_categories
WITH prod,
     COUNT(DISTINCT i.inci_name) AS matched_count,
     COLLECT(DISTINCT i.inci_name) AS matched_ingredients
ORDER BY matched_count DESC, prod.product_name
WITH prod.product_name AS product_name,
     head(collect(prod))          AS prod,
     head(collect(matched_count)) AS matched_count,
     head(collect(matched_ingredients)) AS matched_ingredients
RETURN
    prod.product_id     AS product_id,
    product_name        AS product_name,
    prod.brand          AS brand,
    prod.category       AS category,
    matched_count       AS matched_count,
    matched_ingredients AS matched_ingredients
ORDER BY matched_count DESC, product_name
LIMIT 5
"""

SQL_PRODUCTS_BY_INGREDIENTS = """
WITH matched AS (
    SELECT c.product_id,
           COUNT(DISTINCT c.inci_name)      AS matched_count,
           ARRAY_AGG(DISTINCT c.inci_name)  AS matched_ingredients
    FROM contains c
    JOIN product p ON p.product_id = c.product_id
    WHERE c.inci_name = ANY(%(ingredient_names)s)
      AND p.category = ANY(%(appropriate_categories)s)
    GROUP BY c.product_id
),
ranked AS (
    SELECT p.product_id, p.product_name, p.brand, p.category,
           m.matched_count, m.matched_ingredients,
           ROW_NUMBER() OVER (
               PARTITION BY p.product_name
               ORDER BY m.matched_count DESC, p.product_id
           ) AS rn
    FROM matched m
    JOIN product p ON p.product_id = m.product_id
)
SELECT product_id, product_name, brand, category, matched_count, matched_ingredients
FROM ranked
WHERE rn = 1
ORDER BY matched_count DESC, product_name COLLATE "C"
LIMIT 5
"""


# ── 2. query_ingredients_by_effects ─────────────────────────────────────
# 주어진 effect들에 대해, 성분별로 가장 강한 근거(pubmed_evidence 우선, graph_score DESC)
# 1건만 남긴 뒤 상위 20개 성분.

CYPHER_INGREDIENTS_BY_EFFECTS = """
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

SQL_INGREDIENTS_BY_EFFECTS = """
WITH candidates AS (
    SELECT a.inci_name, a.evidence_type, a.graph_score, a.paper_count,
           e.effect_name_en,
           CASE WHEN a.evidence_type = 'pubmed_evidence' THEN 0 ELSE 1 END AS ev_rank,
           ROW_NUMBER() OVER (
               PARTITION BY a.inci_name
               ORDER BY (CASE WHEN a.evidence_type = 'pubmed_evidence' THEN 0 ELSE 1 END) ASC,
                        a.graph_score DESC
           ) AS rn
    FROM affects a
    JOIN effect e ON e.effect_code = a.effect_code
    WHERE a.effect_code = ANY(%(effects)s)
)
SELECT i.inci_name       AS name,
       i.kor_name        AS kor_name,
       c.effect_name_en  AS claim,
       c.evidence_type   AS eligibility_tier,
       c.paper_count::text AS paper_ref,
       c.graph_score     AS graph_score
FROM candidates c
JOIN ingredient i ON i.inci_name = c.inci_name
WHERE c.rn = 1
ORDER BY c.ev_rank, c.graph_score DESC, i.inci_name COLLATE "C"
LIMIT 20
"""


# ── 3. query_path_by_effects ────────────────────────────────────────────
# Effect -> Ingredient -> Product 3-hop 경로, graph_score DESC top 10.

CYPHER_PATH_BY_EFFECTS = """
UNWIND $effects AS effect_code
MATCH (prod:Product)-[:CONTAINS]->(i:Ingredient)-[r:AFFECTS]->(e:Effect {effect_code: effect_code})
RETURN
    e.effect_code    AS effect_code,
    e.effect_name_en AS effect_name,
    i.inci_name      AS ingredient,
    i.kor_name       AS ingredient_kor,
    r.evidence_type  AS evidence_type,
    r.graph_score    AS graph_score,
    prod.product_name AS product_name,
    prod.brand        AS brand
ORDER BY r.graph_score DESC
LIMIT 10
"""

SQL_PATH_BY_EFFECTS = """
SELECT e.effect_code     AS effect_code,
       e.effect_name_en  AS effect_name,
       i.inci_name       AS ingredient,
       i.kor_name        AS ingredient_kor,
       a.evidence_type   AS evidence_type,
       a.graph_score     AS graph_score,
       p.product_name    AS product_name,
       p.brand           AS brand
FROM contains c
JOIN product p    ON p.product_id = c.product_id
JOIN ingredient i ON i.inci_name = c.inci_name
JOIN affects a    ON a.inci_name = i.inci_name
JOIN effect e     ON e.effect_code = a.effect_code
WHERE a.effect_code = ANY(%(effects)s)
ORDER BY a.graph_score DESC
LIMIT 10
"""
