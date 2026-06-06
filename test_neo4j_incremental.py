"""
neo4j_incremental.py 테스트 스크립트

Iceberg 없이 Neo4j 직접 연결로 NEW / REMOVED / CHANGED 동작 검증.
"""

import os
from neo4j import GraphDatabase
from neo4j_incremental import apply_new, apply_removed, apply_changed

NEO4J_URI      = os.environ.get("NEO4J_BOLT_URI", "bolt://localhost:7687")
NEO4J_USER     = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# 테스트용 ingredient_name → inci_name 매핑
INGREDIENT_MAPPING = {
    "AQUA":     "AQUA",
    "GLYCERIN": "GLYCERIN",
    "NIACINAMIDE": "NIACINAMIDE",
}

TEST_PRODUCT_ID   = "test-product-999"
TEST_PRODUCT_NAME = "테스트 제품"

def get_node(product_id: str) -> dict | None:
    with driver.session() as session:
        result = session.run(
            "MATCH (p:Product {product_id: $id}) RETURN p",
            id=product_id,
        ).single()
        return dict(result["p"]) if result else None

def get_contains(product_id: str) -> list[str]:
    with driver.session() as session:
        result = session.run(
            "MATCH (p:Product {product_id: $id})-[:CONTAINS]->(i:Ingredient) RETURN i.ingredient_id AS inci",
            id=product_id,
        )
        return [r["inci"] for r in result]

def run_tests():
    # ==========================================
    # 1. NEW
    # ==========================================
    print("=== [1] NEW 테스트 ===")
    new_product = {
        "product_id":          TEST_PRODUCT_ID,
        "product_name":        TEST_PRODUCT_NAME,
        "product_brand":       "테스트브랜드",
        "category_id":         "TEST_CAT",
        "product_ingredients": ["AQUA", "GLYCERIN"],
    }
    with driver.session() as session:
        session.execute_write(apply_new, new_product, INGREDIENT_MAPPING)

    node = get_node(TEST_PRODUCT_ID)
    assert node is not None, "FAIL: Product 노드 생성 안 됨"
    assert node["product_name"] == TEST_PRODUCT_NAME, "FAIL: product_name 불일치"
    contains = get_contains(TEST_PRODUCT_ID)
    assert "AQUA" in contains and "GLYCERIN" in contains, f"FAIL: CONTAINS 관계 누락 {contains}"
    print(f"  Product 생성 OK: {node['product_name']}")
    print(f"  CONTAINS 관계 OK: {contains}")

    # ==========================================
    # 2. CHANGED
    # ==========================================
    print("\n=== [2] CHANGED 테스트 ===")
    changed_product = {
        "product_id":          TEST_PRODUCT_ID,
        "product_name":        TEST_PRODUCT_NAME + " (수정됨)",
        "product_brand":       "테스트브랜드",
        "category_id":         "TEST_CAT",
        "product_ingredients": ["NIACINAMIDE"],  # GLYCERIN 빠지고 NIACINAMIDE로 교체
    }
    with driver.session() as session:
        session.execute_write(apply_changed, changed_product, INGREDIENT_MAPPING)

    node = get_node(TEST_PRODUCT_ID)
    assert node["product_name"] == TEST_PRODUCT_NAME + " (수정됨)", "FAIL: product_name 업데이트 안 됨"
    contains = get_contains(TEST_PRODUCT_ID)
    assert contains == ["NIACINAMIDE"], f"FAIL: CONTAINS 관계 재계산 안 됨 {contains}"
    print(f"  product_name 업데이트 OK: {node['product_name']}")
    print(f"  CONTAINS 재계산 OK: {contains}")

    # ==========================================
    # 3. REMOVED
    # ==========================================
    print("\n=== [3] REMOVED 테스트 ===")
    with driver.session() as session:
        session.execute_write(apply_removed, TEST_PRODUCT_ID)

    node = get_node(TEST_PRODUCT_ID)
    assert node is None, "FAIL: Product 노드 삭제 안 됨"
    print(f"  Product 삭제 OK: {TEST_PRODUCT_ID}")

    print("\n=== 모든 테스트 통과 ===")
    driver.close()

if __name__ == "__main__":
    run_tests()
