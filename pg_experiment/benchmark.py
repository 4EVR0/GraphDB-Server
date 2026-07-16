#!/usr/bin/env python3
"""Neo4j vs Postgres 쿼리 latency 벤치마크.

4개 쿼리(프로덕션 3개 + hop-scaling 실험용 1개)를 동일한 파라미터 시퀀스로
양쪽 엔진에 반복 실행해서 p50/p95/p99를 비교한다.

측정 대상은 순수 쿼리 실행 시간(세션/커넥션은 미리 열어두고 재사용)이다.
실제 서비스도 드라이버가 커넥션을 풀링하므로 매 요청마다 핸드셰이크가
일어나지 않는 것과 같은 조건.
"""
import json
import os
import random
import time
from pathlib import Path

import numpy as np
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

WARMUP = 20
ITERATIONS = 200
SEED = 42

CONCERNS_WITH_EDGES = [
    "BARRIER_DAMAGE", "SENSITIVE_SKIN", "DRY_SKIN",
    "ACNE", "OILY_SKIN", "HYPERPIGMENTATION", "POST_ACNE_MARKS",
]


def fetch_param_pools(pg_conn):
    with pg_conn.cursor() as cur:
        cur.execute("SELECT inci_name FROM ingredient")
        ingredients = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT DISTINCT category FROM product WHERE category IS NOT NULL")
        categories = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT effect_code FROM effect")
        effects = [r[0] for r in cur.fetchall()]
    return ingredients, categories, effects


def build_param_sequences(ingredients, categories, effects, n, seed):
    rng = random.Random(seed)
    seq = {
        "products_by_ingredients": [],
        "ingredients_by_effects": [],
        "path_by_effects": [],
        "products_by_concern": [],
    }
    for _ in range(n):
        seq["products_by_ingredients"].append({
            "ingredient_names": rng.sample(ingredients, 3),
            "appropriate_categories": rng.sample(categories, min(5, len(categories))),
        })
        seq["ingredients_by_effects"].append({
            "effects": rng.sample(effects, 3),
        })
        seq["path_by_effects"].append({
            "effects": rng.sample(effects, 3),
        })
        seq["products_by_concern"].append({
            "concern_code": rng.choice(CONCERNS_WITH_EDGES),
        })
    return seq


def time_neo4j(driver, cypher, params_list):
    latencies = []
    with driver.session() as session:
        for i, params in enumerate(params_list):
            start = time.perf_counter()
            result = session.run(cypher, **params)
            _ = [dict(r) for r in result]
            elapsed_ms = (time.perf_counter() - start) * 1000
            if i >= WARMUP:
                latencies.append(elapsed_ms)
    return latencies


def time_postgres(conn, sql, params_list):
    latencies = []
    with conn.cursor() as cur:
        for i, params in enumerate(params_list):
            start = time.perf_counter()
            cur.execute(sql, params)
            _ = cur.fetchall()
            elapsed_ms = (time.perf_counter() - start) * 1000
            if i >= WARMUP:
                latencies.append(elapsed_ms)
    return latencies


def summarize(latencies):
    arr = np.array(latencies)
    return {
        "n": len(arr),
        "mean_ms": round(float(arr.mean()), 3),
        "p50_ms": round(float(np.percentile(arr, 50)), 3),
        "p95_ms": round(float(np.percentile(arr, 95)), 3),
        "p99_ms": round(float(np.percentile(arr, 99)), 3),
        "min_ms": round(float(arr.min()), 3),
        "max_ms": round(float(arr.max()), 3),
    }


def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    pg_conn = psycopg.connect(PG_DSN)

    ingredients, categories, effects = fetch_param_pools(pg_conn)
    total = WARMUP + ITERATIONS
    params = build_param_sequences(ingredients, categories, effects, total, SEED)

    query_pairs = {
        "products_by_ingredients": (CYPHER_PRODUCTS_BY_INGREDIENTS, SQL_PRODUCTS_BY_INGREDIENTS),
        "ingredients_by_effects": (CYPHER_INGREDIENTS_BY_EFFECTS, SQL_INGREDIENTS_BY_EFFECTS),
        "path_by_effects": (CYPHER_PATH_BY_EFFECTS, SQL_PATH_BY_EFFECTS),
        "products_by_concern": (CYPHER_PRODUCTS_BY_CONCERN, SQL_PRODUCTS_BY_CONCERN),
    }

    results = {}
    for name, (cypher, sql) in query_pairs.items():
        print(f"=== {name} ===")
        neo4j_lat = time_neo4j(driver, cypher, params[name])
        pg_lat = time_postgres(pg_conn, sql, params[name])
        results[name] = {"neo4j": summarize(neo4j_lat), "postgres": summarize(pg_lat)}
        print(f"  neo4j   : {results[name]['neo4j']}")
        print(f"  postgres: {results[name]['postgres']}")

    driver.close()
    pg_conn.close()

    out_dir = Path(__file__).parent / "results"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "latencies.json"
    out_path.write_text(json.dumps(
        {"warmup": WARMUP, "iterations": ITERATIONS, "seed": SEED, "results": results},
        ensure_ascii=False, indent=2,
    ))
    print(f"\n결과 저장: {out_path}")


if __name__ == "__main__":
    main()
