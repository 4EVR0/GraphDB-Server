// 스키마 제약조건 + 인덱스.
// bulk import(neo4j-admin database import full)는 빈 DB에만 가능하므로
// 제약조건/인덱스는 임포트 후 migrate.py가 적용한다 (load.sh [7/7] 단계).
//
// Neo4j Community Edition 한계: uniqueness constraint와 인덱스만 지원.
// existence/node-key constraint는 Enterprise 전용 → 값 존재성 검증은
// 임포트 전 validate.py(CSV 검증)가 담당한다.

CREATE CONSTRAINT product_id_unique IF NOT EXISTS
FOR (p:Product) REQUIRE p.product_id IS UNIQUE;

CREATE CONSTRAINT ingredient_id_unique IF NOT EXISTS
FOR (i:Ingredient) REQUIRE i.ingredient_id IS UNIQUE;

CREATE CONSTRAINT effect_code_unique IF NOT EXISTS
FOR (e:Effect) REQUIRE e.effect_code IS UNIQUE;

CREATE CONSTRAINT concern_code_unique IF NOT EXISTS
FOR (c:Concern) REQUIRE c.concern_code IS UNIQUE;

// query_products_by_ingredients: MATCH (i:Ingredient {inci_name: ...}) 핫패스
CREATE INDEX ingredient_inci_name IF NOT EXISTS
FOR (i:Ingredient) ON (i.inci_name);

CREATE INDEX ingredient_kor_name IF NOT EXISTS
FOR (i:Ingredient) ON (i.kor_name);

// query_products_by_ingredients: WHERE prod.category IN [...] 필터
CREATE INDEX product_category IF NOT EXISTS
FOR (p:Product) ON (p.category);

CREATE INDEX product_name IF NOT EXISTS
FOR (p:Product) ON (p.product_name);
