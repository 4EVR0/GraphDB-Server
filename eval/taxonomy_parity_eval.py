"""taxonomy 정합성 회귀 테스트 — 그래프 vs taxonomy.yaml(SSOT).

검증 항목:
  1. taxonomy.yaml의 26개 concern이 모두 그래프에 존재하는가
  2. concern별 RELATES_TO 엣지(effect 목록 + rank 순서)가 yaml과 일치하는가
     → "RELATES_TO 누락 8개 concern" 버그(RESULTS.md §1)의 영구 회귀 테스트
  3. concern별 appropriate_categories가 yaml(미지정 시 default)과 일치하는가
  4. 모든 concern에서 /path 스타일 순회(Concern→Effect→Ingredient)가 1행 이상
     나오는가 (그래프 네이티브 경로 탐색 커버리지)

사용법:
  NEO4J_URI=... NEO4J_PASSWORD=... python3 taxonomy_parity_eval.py [--taxonomy PATH]
실패 시 exit 1 (CI/load.sh 후속 게이트로 사용 가능).
"""

import argparse
import os
import sys
from pathlib import Path

import yaml
from neo4j import GraphDatabase

DEFAULT_TAXONOMY = (
    Path(__file__).resolve().parents[2] / "GraphRAG_Pipeline" / "db" / "seed" / "taxonomy.yaml"
)

GRAPH_TAXONOMY_QUERY = """
MATCH (c:Concern)
OPTIONAL MATCH (e:Effect)-[r:RELATES_TO]->(c)
WITH c, e, r ORDER BY r.rank
RETURN
    c.concern_code AS concern_code,
    c.appropriate_categories AS categories,
    [x IN collect(e.effect_code) WHERE x IS NOT NULL] AS effects
"""

PATH_COVERAGE_QUERY = """
MATCH (c:Concern {concern_code: $concern_code})<-[:RELATES_TO]-(e:Effect)<-[:AFFECTS]-(i:Ingredient)
RETURN count(*) AS n
"""


def get_driver():
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD")
    if not password:
        sys.exit("ERROR: NEO4J_PASSWORD 환경변수가 필요합니다")
    return GraphDatabase.driver(uri, auth=(user, password))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    args = parser.parse_args()

    data = yaml.safe_load(args.taxonomy.read_text(encoding="utf-8"))
    default_categories = data["default_categories"]
    expected = {
        code: {
            "effects": c["effects"],
            "categories": c.get("categories", default_categories),
        }
        for code, c in data["concerns"].items()
    }

    errors: list[str] = []
    driver = get_driver()
    try:
        with driver.session() as session:
            graph = {
                row["concern_code"]: {
                    "effects": row["effects"],
                    "categories": row["categories"],
                }
                for row in session.run(GRAPH_TAXONOMY_QUERY)
            }

            missing = sorted(set(expected) - set(graph))
            extra = sorted(set(graph) - set(expected))
            if missing:
                errors.append(f"그래프에 없는 concern: {missing}")
            if extra:
                errors.append(f"yaml에 없는 concern이 그래프에 존재: {extra}")

            for code in sorted(set(expected) & set(graph)):
                if graph[code]["effects"] != expected[code]["effects"]:
                    errors.append(
                        f"{code}: RELATES_TO 불일치 graph={graph[code]['effects']} "
                        f"yaml={expected[code]['effects']}"
                    )
                if list(graph[code]["categories"] or []) != expected[code]["categories"]:
                    errors.append(
                        f"{code}: categories 불일치 graph={graph[code]['categories']} "
                        f"yaml={expected[code]['categories']}"
                    )

            # 경로 탐색 커버리지: concern → effect → ingredient 1행 이상
            no_path = []
            for code in sorted(expected):
                n = session.run(PATH_COVERAGE_QUERY, concern_code=code).single()["n"]
                if n == 0:
                    no_path.append(code)
            if no_path:
                errors.append(f"Concern→Effect→Ingredient 경로 0건: {no_path}")
    finally:
        driver.close()

    print(f"검사 대상 concern: {len(expected)}개")
    if errors:
        print(f"\nFAIL — {len(errors)}건:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("PASS — 그래프 taxonomy가 yaml과 완전 일치, 전 concern 경로 탐색 가능")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
