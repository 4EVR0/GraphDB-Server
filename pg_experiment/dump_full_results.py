#!/usr/bin/env python3
"""4개 쿼리를 고정 파라미터로 1회씩 실행해서 Neo4j/Postgres 결과를 잘리지 않은
전체 raw 형태로 markdown 파일에 남긴다. RESULTS.md에 "요약 없이 원본 그대로"
붙여넣기 위한 용도.
"""
import os

import psycopg
from neo4j import GraphDatabase

from queries import (
    CYPHER_INGREDIENTS_BY_EFFECTS,
    CYPHER_PATH_BY_EFFECTS,
    CYPHER_PRODUCTS_BY_CONCERN,
    CYPHER_PRODUCTS_BY_INGREDIENTS,
    SQL_INGREDIENTS_BY_EFFECTS,
    SQL_PATH_BY_EFFECTS,
    SQL_PRODUCTS_BY_CONCERN,
    SQL_PRODUCTS_BY_INGREDIENTS,
)

PG_DSN = os.environ.get(
    "PG_BENCH_DSN",
    "postgresql://bench_user:bench_pass@localhost:5433/graphdb_bench",
)
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]

PARAMS = {
    "products_by_ingredients": {
        "cypher": {"ingredient_names": ["GLYCERIN", "1,2-HEXANEDIOL", "BUTYLENE GLYCOL"],
                   "appropriate_categories": ["로션", "세럼", "앰플", "크림", "기타"]},
        "sql": {"ingredient_names": ["GLYCERIN", "1,2-HEXANEDIOL", "BUTYLENE GLYCOL"],
                "appropriate_categories": ["로션", "세럼", "앰플", "크림", "기타"]},
    },
    "ingredients_by_effects": {
        "cypher": {"effects": ["ANTI_INFLAMMATORY", "SOOTHING", "HYDRATING"]},
        "sql": {"effects": ["ANTI_INFLAMMATORY", "SOOTHING", "HYDRATING"]},
    },
    "path_by_effects": {
        "cypher": {"effects": ["ANTI_INFLAMMATORY", "SOOTHING", "HYDRATING"]},
        "sql": {"effects": ["ANTI_INFLAMMATORY", "SOOTHING", "HYDRATING"]},
    },
    "products_by_concern": {
        "cypher": {"concern_code": "ACNE"},
        "sql": {"concern_code": "ACNE"},
    },
}

QUERY_PAIRS = {
    "products_by_ingredients": (CYPHER_PRODUCTS_BY_INGREDIENTS, SQL_PRODUCTS_BY_INGREDIENTS),
    "ingredients_by_effects": (CYPHER_INGREDIENTS_BY_EFFECTS, SQL_INGREDIENTS_BY_EFFECTS),
    "path_by_effects": (CYPHER_PATH_BY_EFFECTS, SQL_PATH_BY_EFFECTS),
    "products_by_concern": (CYPHER_PRODUCTS_BY_CONCERN, SQL_PRODUCTS_BY_CONCERN),
}


def run_cypher(driver, query, params):
    with driver.session() as session:
        return [dict(r) for r in session.run(query, **params)]


def run_sql(conn, query, params):
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(query, params)
        return cur.fetchall()


def fmt_rows(rows):
    if not rows:
        return "(결과 없음)\n"
    lines = []
    for i, row in enumerate(rows, 1):
        lines.append(f"{i}. " + ", ".join(f"{k}={v!r}" for k, v in row.items()))
    return "\n".join(lines) + "\n"


def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    pg_conn = psycopg.connect(PG_DSN)

    out = ["# 쿼리별 전체 원본 결과 (파라미터 고정 1회 실행)\n"]
    for name, (cypher, sql) in QUERY_PAIRS.items():
        c_rows = run_cypher(driver, cypher, PARAMS[name]["cypher"])
        s_rows = run_sql(pg_conn, sql, PARAMS[name]["sql"])

        out.append(f"\n## {name}\n")
        out.append(f"파라미터: `{PARAMS[name]['cypher']}`\n")
        out.append(f"\n### Neo4j 결과 ({len(c_rows)}건)\n```\n{fmt_rows(c_rows)}```\n")
        out.append(f"\n### Postgres 결과 ({len(s_rows)}건)\n```\n{fmt_rows(s_rows)}```\n")

    driver.close()
    pg_conn.close()

    text = "".join(out)
    print(text)
    with open("results/full_query_dump.md", "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    main()
