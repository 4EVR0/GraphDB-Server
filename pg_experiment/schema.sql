-- Neo4j 그래프(Product-CONTAINS->Ingredient-AFFECTS->Effect-RELATES_TO->Concern)와
-- 동일한 개체/관계를 정규화된 관계형 스키마로 옮긴 것.
-- 원본: csv/nodes/*.csv, csv/edges/*.csv (README.md 그래프 구조 참고)

DROP TABLE IF EXISTS relates_to;
DROP TABLE IF EXISTS affects;
DROP TABLE IF EXISTS contains;
DROP TABLE IF EXISTS concern;
DROP TABLE IF EXISTS effect;
DROP TABLE IF EXISTS ingredient;
DROP TABLE IF EXISTS product;

CREATE TABLE product (
    product_id   UUID PRIMARY KEY,
    product_name TEXT NOT NULL,
    brand        TEXT,
    category     TEXT,
    goods_no     TEXT
);

CREATE TABLE ingredient (
    inci_name        TEXT PRIMARY KEY,
    kor_name         TEXT,
    cosing_functions TEXT[]
);

CREATE TABLE effect (
    effect_code    TEXT PRIMARY KEY,
    effect_name_en TEXT
);

CREATE TABLE concern (
    concern_code    TEXT PRIMARY KEY,
    concern_name_ko TEXT
);

-- (Product)-[:CONTAINS]->(Ingredient)
CREATE TABLE contains (
    product_id UUID NOT NULL REFERENCES product(product_id),
    inci_name  TEXT NOT NULL REFERENCES ingredient(inci_name),
    PRIMARY KEY (product_id, inci_name)
);

-- (Ingredient)-[:AFFECTS]->(Effect)
CREATE TABLE affects (
    inci_name     TEXT NOT NULL REFERENCES ingredient(inci_name),
    effect_code   TEXT NOT NULL REFERENCES effect(effect_code),
    type          TEXT,
    evidence_type TEXT,
    graph_score   DOUBLE PRECISION,
    paper_count   INT,
    PRIMARY KEY (inci_name, effect_code)
);

-- (Effect)-[:RELATES_TO]->(Concern)
CREATE TABLE relates_to (
    effect_code  TEXT NOT NULL REFERENCES effect(effect_code),
    concern_code TEXT NOT NULL REFERENCES concern(concern_code),
    PRIMARY KEY (effect_code, concern_code)
);

-- 프로덕션 3개 쿼리(neo4j_client.py)가 실제로 타는 조인/필터 컬럼 기준 인덱스.
-- contains.product_id, affects.inci_name은 각 PK의 첫 컬럼이라 이미 인덱스로 커버됨.
CREATE INDEX idx_contains_inci_name  ON contains (inci_name);
CREATE INDEX idx_product_category    ON product (category);
CREATE INDEX idx_affects_effect_code ON affects (effect_code);
