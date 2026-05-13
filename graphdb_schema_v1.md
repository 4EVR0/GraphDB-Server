# GraphDB 스키마 V1 (초기 설계)

> 현재 운영 중인 V2 스키마와 다름. V2로 간소화되기 전 초기 설계 히스토리 보존용.
> 현재 스키마는 `graphdb_schema.md` 참고.

---

## 변경 요약 (V1 → V2)

| 항목 | V1 | V2 |
|------|----|----|
| 노드 수 | 6개 (Product, Ingredient, Paper, Claim, Effect, Concern) | 4개 (Paper, Claim 제거) |
| Ingredient→Effect 관계 | `HAS_CLAIM → Claim → INDICATES → Effect` | `AFFECTS {type}` 직결 |
| 근거 강도 표현 | Claim 노드의 confidence_score | AFFECTS의 evidence_type, graph_score, paper_count |

---

## 노드 6개 구조

```
(Product)-[:CONTAINS]->(Ingredient)
(Ingredient)-[:HAS_CLAIM]->(Claim)<-[:SUPPORTS]-(Paper)
(Claim)-[:INDICATES]->(Effect)
(Effect)-[:RELATES_TO]->(Concern)
```

### 노드 정의

**Product**
```
(:Product {
  product_id: STRING,
  product_name: STRING,
  brand: STRING
})
```

**Ingredient**
```
(:Ingredient {
  ingredient_id: STRING,
  inci_name: STRING,
  kor_name: STRING
})
```

**Paper**
```
(:Paper {
  paper_id: STRING,
  title: STRING,
  journal: STRING,
  publication_year: INTEGER
})
```

**Claim**
```
(:Claim {
  claim_id: STRING,
  claim_text: STRING,       // "Niacinamide improves hyperpigmentation"
  verb: STRING,             // improves | reduces | prevents | is_well_tolerated_for
  effect_target: STRING,    // LLM이 추출한 raw 타겟
  confidence_score: FLOAT
})
```

**Effect**
```
(:Effect {
  effect_code: STRING,      // "BRIGHTENING"
  effect_name_en: STRING
})
```

**Concern**
```
(:Concern {
  concern_code: STRING,     // "PIGMENTATION"
  concern_name_ko: STRING   // "색소침착/기미"
})
```

---

## 관계 정의

| 관계 | 방향 | 의미 |
|------|------|------|
| `CONTAINS` | Product → Ingredient | 이 화장품에 이 성분이 들어있다 |
| `HAS_CLAIM` | Ingredient → Claim | 이 성분에 대한 주장이다 |
| `SUPPORTS` | Paper → Claim | 이 논문이 이 주장의 근거다 |
| `INDICATES` | Claim → Effect | 이 주장은 이 효능 분류와 연결된다 |
| `RELATES_TO` | Effect → Concern | 이 효능은 이 피부 고민과 관련된다 |

---

## 핵심 쿼리 예시

### 피부 고민 → 성분 추천

```cypher
MATCH (c:Concern {concern_code: 'PIGMENTATION'})
      <-[:RELATES_TO]-(e:Effect)
      <-[:INDICATES]-(cl:Claim)
      <-[:HAS_CLAIM]-(i:Ingredient)
RETURN i.inci_name AS ingredient,
       cl.claim_text AS claim,
       e.effect_name_en AS effect
```

### 고민별 성분 + 화장품 추천

```cypher
MATCH (c:Concern {concern_code: 'PIGMENTATION'})
      <-[:RELATES_TO]-(e:Effect)
      <-[:INDICATES]-(cl:Claim)
      <-[:HAS_CLAIM]-(i:Ingredient)
      <-[:CONTAINS]-(prod:Product)
RETURN prod.product_name AS product,
       collect(DISTINCT i.inci_name) AS matched_ingredients,
       collect(DISTINCT cl.claim_text) AS supporting_claims
```

### 성분 근거 논문 조회

```cypher
MATCH (i:Ingredient {inci_name: 'NIACINAMIDE'})
      -[:HAS_CLAIM]->(cl:Claim)
      <-[:SUPPORTS]-(p:Paper)
RETURN cl.claim_text, p.title, p.publication_year
ORDER BY cl.confidence_score DESC
```

---

## 제약조건 / 인덱스

```cypher
CREATE CONSTRAINT ingredient_id_unique IF NOT EXISTS
FOR (i:Ingredient) REQUIRE i.ingredient_id IS UNIQUE;

CREATE CONSTRAINT paper_id_unique IF NOT EXISTS
FOR (p:Paper) REQUIRE p.paper_id IS UNIQUE;

CREATE CONSTRAINT claim_id_unique IF NOT EXISTS
FOR (cl:Claim) REQUIRE cl.claim_id IS UNIQUE;

CREATE CONSTRAINT effect_code_unique IF NOT EXISTS
FOR (e:Effect) REQUIRE e.effect_code IS UNIQUE;

CREATE CONSTRAINT concern_code_unique IF NOT EXISTS
FOR (c:Concern) REQUIRE c.concern_code IS UNIQUE;

CREATE CONSTRAINT product_id_unique IF NOT EXISTS
FOR (p:Product) REQUIRE p.product_id IS UNIQUE;

CREATE INDEX ingredient_name_idx IF NOT EXISTS
FOR (i:Ingredient) ON (i.inci_name);

CREATE INDEX claim_target_idx IF NOT EXISTS
FOR (cl:Claim) ON (cl.effect_target);

CREATE INDEX paper_pmid_idx IF NOT EXISTS
FOR (p:Paper) ON (p.pmid);

CREATE INDEX product_name_idx IF NOT EXISTS
FOR (p:Product) ON (p.product_name);
```

> Concern에 사용자 자연어 검색 필요 시 full-text index 추가:
> ```cypher
> CREATE FULLTEXT INDEX concern_terms_ft IF NOT EXISTS
> FOR (c:Concern) ON EACH [c.concern_name_ko, c.query_terms];
> ```

---

## 나중에 추가할 것들 (MVP 이후)

| 항목 | 설명 |
|------|------|
| Alias 노드 | "Vitamin B3" → Niacinamide 별칭 처리 |
| CanonicalClaim | 같은 claim이 논문 여러 편에 나오면 evidence_count로 집계 |
| EffectTarget 노드 분리 | Claim의 effect_target 필드를 별도 노드로 분리 |
| Mechanism 노드 | "왜 효과가 있나?" 설명 생성용 |
| AdverseEffect 노드 | 성분 안전성 정보 |