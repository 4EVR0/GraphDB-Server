#!/usr/bin/env python3
"""Neo4j 스키마 마이그레이션 러너.

migrations/*.cypher 를 파일명 순으로 적용한다. 적용 이력은 (:_Migration
{version, checksum, applied_at}) 노드로 DB 안에 기록되므로:
  - bulk import(full)로 DB가 초기화되면 전부 재적용된다 (마이그레이션은 모두
    멱등(idempotent)하게 작성돼 있어 안전).
  - 임포트 사이에 재실행하면 checksum이 같은 버전은 건너뛴다.

각 문장(;)은 개별 auto-commit 트랜잭션으로 실행한다 — 스키마 명령(CREATE
CONSTRAINT)과 데이터 쓰기를 한 트랜잭션에 섞을 수 없기 때문.

사용법:
  python3 migrate.py                 # 적용
  python3 migrate.py --dry-run       # 실행할 문장만 출력
  python3 migrate.py --verify        # 적용 후 상태 검증 (실패 시 exit 1)
  python3 migrate.py --wait 120      # Neo4j 기동 대기(초) 후 적용

접속 정보: NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD 환경변수
(기본 bolt://localhost:7687, neo4j).
"""

import argparse
import hashlib
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from neo4j import GraphDatabase

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def get_driver():
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD")
    if not password:
        sys.exit("ERROR: NEO4J_PASSWORD 환경변수가 필요합니다")
    return GraphDatabase.driver(uri, auth=(user, password))


def wait_for_neo4j(driver, timeout: int) -> None:
    deadline = time.monotonic() + timeout
    while True:
        try:
            driver.verify_connectivity()
            return
        except Exception as exc:
            if time.monotonic() >= deadline:
                sys.exit(f"ERROR: Neo4j가 {timeout}s 안에 기동하지 않음: {exc}")
            print(f"Neo4j 기동 대기 중... ({type(exc).__name__})")
            time.sleep(3)


def split_statements(cypher: str) -> list[str]:
    """// 주석 제거 후 ; 기준 분리. 값에 세미콜론이 없다는 전제(생성기가 보장)."""
    lines = [line for line in cypher.splitlines() if not line.strip().startswith("//")]
    statements = []
    for chunk in "\n".join(lines).split(";"):
        stmt = chunk.strip()
        if stmt:
            statements.append(stmt)
    return statements


def applied_versions(session) -> dict[str, str]:
    result = session.run("MATCH (m:_Migration) RETURN m.version AS v, m.checksum AS c")
    return {row["v"]: row["c"] for row in result}


def apply_migration(session, version: str, checksum: str, statements: list[str]) -> None:
    for stmt in statements:
        session.run(stmt).consume()
    session.run(
        "MERGE (m:_Migration {version: $version}) "
        "SET m.checksum = $checksum, m.applied_at = $applied_at",
        version=version,
        checksum=checksum,
        applied_at=datetime.now(timezone.utc).isoformat(),
    ).consume()


def verify(session) -> list[str]:
    """마이그레이션 후 기대 상태를 검증하고 실패 메시지 목록을 반환한다."""
    errors: list[str] = []

    constraints = {row["name"] for row in session.run("SHOW CONSTRAINTS")}
    for name in (
        "product_id_unique",
        "ingredient_id_unique",
        "effect_code_unique",
        "concern_code_unique",
    ):
        if name not in constraints:
            errors.append(f"constraint 누락: {name}")

    n_concern = session.run("MATCH (c:Concern) RETURN count(c) AS n").single()["n"]
    if n_concern < 26:
        errors.append(f"Concern 노드 {n_concern}개 (26개 이상 기대)")

    orphans = [
        row["code"]
        for row in session.run(
            "MATCH (c:Concern) WHERE NOT ()-[:RELATES_TO]->(c) RETURN c.concern_code AS code"
        )
    ]
    if orphans:
        errors.append(f"RELATES_TO 없는 concern: {orphans}")

    no_cats = [
        row["code"]
        for row in session.run(
            "MATCH (c:Concern) WHERE c.appropriate_categories IS NULL RETURN c.concern_code AS code"
        )
    ]
    if no_cats:
        errors.append(f"appropriate_categories 없는 concern: {no_cats}")

    has_default = session.run(
        "MATCH (m:TaxonomyConfig {key: 'default_categories'}) RETURN count(m) AS n"
    ).single()["n"]
    if not has_default:
        errors.append("TaxonomyConfig default_categories 누락")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--wait", type=int, default=60, help="Neo4j 기동 대기 최대 초")
    args = parser.parse_args()

    files = sorted(MIGRATIONS_DIR.glob("V*.cypher"))
    if not files:
        sys.exit(f"ERROR: {MIGRATIONS_DIR} 에 마이그레이션 파일이 없습니다")

    driver = get_driver()
    try:
        wait_for_neo4j(driver, args.wait)
        with driver.session() as session:
            done = applied_versions(session)
            for path in files:
                version = path.stem.split("__")[0]
                cypher = path.read_text(encoding="utf-8")
                checksum = hashlib.sha256(cypher.encode()).hexdigest()[:16]
                if done.get(version) == checksum:
                    print(f"[skip] {path.name} (적용됨)")
                    continue
                statements = split_statements(cypher)
                if args.dry_run:
                    print(f"[dry-run] {path.name}: {len(statements)}개 문장")
                    for stmt in statements:
                        print(f"  {stmt.splitlines()[0][:100]} ...")
                    continue
                print(f"[apply] {path.name}: {len(statements)}개 문장")
                apply_migration(session, version, checksum, statements)

            if args.verify and not args.dry_run:
                errors = verify(session)
                if errors:
                    for err in errors:
                        print(f"[verify-fail] {err}", file=sys.stderr)
                    return 1
                print("[verify] OK — constraints/taxonomy 정상")
    finally:
        driver.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
