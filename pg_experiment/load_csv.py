#!/usr/bin/env python3
"""csv/nodes, csv/edges 데이터를 pg_experiment Postgres에 적재한다.

neo4j import용 CSV(csv/nodes/*.csv, csv/edges/*.csv)를 그대로 읽어
schema.sql로 만든 테이블에 넣는다. Neo4j import와 동일한 원본을 쓰므로
두 DB가 정확히 같은 데이터를 갖는다.
"""
import csv
import os
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parent.parent
NODES = ROOT / "csv" / "nodes"
EDGES = ROOT / "csv" / "edges"

DSN = os.environ.get(
    "PG_BENCH_DSN",
    "postgresql://bench_user:bench_pass@localhost:5433/graphdb_bench",
)


def read_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def parse_array(value: str) -> list[str] | None:
    if not value:
        return None
    return value.split(";")


def load(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        products = read_rows(NODES / "product.csv")
        cur.executemany(
            "INSERT INTO product (product_id, product_name, brand, category, goods_no) "
            "VALUES (%s, %s, %s, %s, %s)",
            [
                (r["product_id:ID(Product)"], r["product_name"], r["brand"], r["category"], r["goods_no"])
                for r in products
            ],
        )
        print(f"product: {len(products)}")

        ingredients = read_rows(NODES / "ingredient.csv")
        cur.executemany(
            "INSERT INTO ingredient (inci_name, kor_name, cosing_functions) VALUES (%s, %s, %s)",
            [
                (r["ingredient_id:ID(Ingredient)"], r["kor_name"], parse_array(r["cosing_functions:string[]"]))
                for r in ingredients
            ],
        )
        print(f"ingredient: {len(ingredients)}")

        effects = read_rows(NODES / "effect.csv")
        cur.executemany(
            "INSERT INTO effect (effect_code, effect_name_en) VALUES (%s, %s)",
            [(r["effect_code:ID(Effect)"], r["effect_name_en"]) for r in effects],
        )
        print(f"effect: {len(effects)}")

        concerns = read_rows(NODES / "concern.csv")
        cur.executemany(
            "INSERT INTO concern (concern_code, concern_name_ko) VALUES (%s, %s)",
            [(r["concern_code:ID(Concern)"], r["concern_name_ko"]) for r in concerns],
        )
        print(f"concern: {len(concerns)}")

        contains = read_rows(EDGES / "contains.csv")
        cur.executemany(
            "INSERT INTO contains (product_id, inci_name) VALUES (%s, %s)",
            [(r[":START_ID(Product)"], r[":END_ID(Ingredient)"]) for r in contains],
        )
        print(f"contains: {len(contains)}")

        affects = read_rows(EDGES / "affects.csv")
        cur.executemany(
            "INSERT INTO affects (inci_name, effect_code, type, evidence_type, graph_score, paper_count) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            [
                (
                    r[":START_ID(Ingredient)"],
                    r[":END_ID(Effect)"],
                    r["type"],
                    r["evidence_type"],
                    float(r["graph_score:float"]) if r["graph_score:float"] else None,
                    int(r["paper_count:int"]) if r["paper_count:int"] else None,
                )
                for r in affects
            ],
        )
        print(f"affects: {len(affects)}")

        relates_to = read_rows(EDGES / "relates_to.csv")
        cur.executemany(
            "INSERT INTO relates_to (effect_code, concern_code) VALUES (%s, %s)",
            [(r[":START_ID(Effect)"], r[":END_ID(Concern)"]) for r in relates_to],
        )
        print(f"relates_to: {len(relates_to)}")

    conn.commit()


def main() -> None:
    with psycopg.connect(DSN) as conn:
        load(conn)
    print("done.")


if __name__ == "__main__":
    main()
