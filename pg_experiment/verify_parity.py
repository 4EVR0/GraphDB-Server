#!/usr/bin/env python3
"""Neo4j 결과와 SQL 결과가 실제로 일치하는지 확인하는 1회성 검증 스크립트.
벤치마크를 신뢰하려면 두 쪽이 같은 결과를 내야 한다.
"""
import os

import psycopg
from neo4j import GraphDatabase

from queries import (
    CYPHER_INGREDIENTS_BY_EFFECTS,
    CYPHER_PATH_BY_EFFECTS,
    CYPHER_PRODUCTS_BY_INGREDIENTS,
    SQL_INGREDIENTS_BY_EFFECTS,
    SQL_PATH_BY_EFFECTS,
    SQL_PRODUCTS_BY_INGREDIENTS,
)

PG_DSN = os.environ.get(
    "PG_BENCH_DSN",
    "postgresql://bench_user:bench_pass@localhost:5433/graphdb_bench",
)
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]


def run_cypher(driver, query, **params):
    with driver.session() as session:
        return [dict(r) for r in session.run(query, **params)]


def run_sql(conn, query, params):
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(query, params)
        return cur.fetchall()


def compare(name, cypher_rows, sql_rows, key_fields):
    cypher_keys = [tuple(str(r[k]) for k in key_fields) for r in cypher_rows]
    sql_keys = [tuple(str(r[k]) for k in key_fields) for r in sql_rows]
    match = cypher_keys == sql_keys
    print(f"[{'OK' if match else 'MISMATCH'}] {name}: cypher={len(cypher_rows)} rows, sql={len(sql_rows)} rows")
    if not match:
        print("  cypher:", cypher_keys)
        print("  sql   :", sql_keys)


def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with psycopg.connect(PG_DSN) as conn:
        # 1. query_products_by_ingredients
        ing_names = ["GLYCERIN", "1,2-HEXANEDIOL", "BUTYLENE GLYCOL"]
        categories = ["로션", "세럼", "앰플", "크림", "기타"]
        c_rows = run_cypher(
            driver, CYPHER_PRODUCTS_BY_INGREDIENTS,
            ingredient_names=ing_names, appropriate_categories=categories,
        )
        s_rows = run_sql(
            conn, SQL_PRODUCTS_BY_INGREDIENTS,
            {"ingredient_names": ing_names, "appropriate_categories": categories},
        )
        compare("query_products_by_ingredients", c_rows, s_rows, ["product_id"])

        # 2. query_ingredients_by_effects
        effects = ["ANTI_INFLAMMATORY", "SOOTHING", "HYDRATING"]
        c_rows = run_cypher(driver, CYPHER_INGREDIENTS_BY_EFFECTS, effects=effects)
        s_rows = run_sql(conn, SQL_INGREDIENTS_BY_EFFECTS, {"effects": effects})
        compare("query_ingredients_by_effects", c_rows, s_rows, ["name"])

        # 3. query_path_by_effects
        # 원본 Cypher가 ORDER BY graph_score DESC 하나뿐이라 동점(graph_score 같은 행)이
        # 많으면 어느 행이 LIMIT 10 안에 들지는 원본 쿼리 자체가 이미 비결정적이다.
        # (Neo4j도 재실행하면 동점 구간에서 다른 행이 나올 수 있음.)
        # 그래서 신원(product_name)이 아니라 graph_score 분포가 같은지만 비교한다.
        c_rows = run_cypher(driver, CYPHER_PATH_BY_EFFECTS, effects=effects)
        s_rows = run_sql(conn, SQL_PATH_BY_EFFECTS, {"effects": effects})
        compare(
            "query_path_by_effects (graph_score만 비교, 동점 구간 비결정적)",
            c_rows, s_rows, ["graph_score"],
        )

    driver.close()


if __name__ == "__main__":
    main()
