# GraphDB 스키마 (V3)

*26.05.12 기준 / 실제 CSV 기준으로 업데이트됨*

---

## 최종 그래프 구조

```
(Product)-[:CONTAINS]->(Ingredient)
(Ingredient)-[:AFFECTS {type, evidence_type, graph_score, paper_count}]->(Effect)
(Effect)-[:RELATES_TO]->(Concern)
```

---

## 설계 결정 히스토리

### AFFECTS를 관계 타입으로 쪼개지 않고 속성으로 가져간 이유

초기에 `improves`, `reduces`, `prevents` 등을 별도 관계 타입으로 두는 방식을 검토했으나, 관계 속성(`type`)으로 통합함.

- **확장성**: 새로운 type이 생겨도 관계 타입 추가 없이 enum 값만 추가하면 됨
- **쿼리 단순화**: `MATCH (i)-[r:AFFECTS]->(e)` 한 줄로 모든 관계 조회 가능
- **운영 편의**: `r.type` 값만 enum처럼 관리하면 됨

### IS_WELL_TOLERATED_FOR를 최종 스키마에서 제외한 이유

`(Ingredient)-[:IS_WELL_TOLERATED_FOR]->(Concern)` 형태를 검토했으나 미포함으로 결론.

- `improves`, `reduces`, `prevents` 는 **성분이 피부에 어떤 변화를 일으키는지** → Effect 대상
  - ex. Ceramide prevents water loss
- `is_well_tolerated_for` 는 **누가 써도 괜찮냐** → Concern 대상
  - ex. Centella is well tolerated for sensitive skin
- 즉 대상 노드 자체가 달라서(Effect vs Concern) AFFECTS와 같은 관계로 묶기 어렵고, 별도 관계로 두면 관리 포인트가 늘어남
- 현재 데이터 범위에서는 미포함, 필요 시 추후 추가 검토

---

## nodes/product.csv

```
product_id:ID(Product),product_name,brand,category
a3cfe85b-7c7a-5fe8-83b5-b38c30c2995a,유리아쥬 오떼르말,유리아쥬,미스트
d2084a81-5d1e-5b91-9c6b-27772718af13,아벤느 오떼르말 미스트,아벤느,미스트
```

## nodes/ingredient.csv

```
ingredient_id:ID(Ingredient),inci_name,kor_name,cosing_functions:string[]
AQUA,AQUA,정제수,SOLVENT
GLYCERIN,GLYCERIN,글리세린,HUMECTANT;SKIN CONDITIONING
```

> `ingredient_id` 는 `inci_name` 과 동일한 값을 사용함 (예: `AQUA`, `GLYCERIN`, `CERAMIDE NP`)

## nodes/effect.csv

```
effect_code:ID(Effect),effect_name_en
ANTI_INFLAMMATORY,Anti-inflammatory
BARRIER_REPAIR,Barrier Repair
```

## nodes/concern.csv

```
concern_code:ID(Concern),concern_name_ko
ACNE,여드름
SENSITIVITY,민감성
```

## edges/contains.csv

```
:START_ID(Product),:END_ID(Ingredient)
```

> 작업 중

## edges/affects.csv

**type 허용값:** `improves` | `reduces` | `prevents` | `increases` | `is_safe_for` | `is_well_tolerated_for` | `causes` | `does_not_cause` | `inhibits` | `stimulates` | `regulates` | `modulates`

**evidence_type 허용값:** `pubmed_evidence` | `cosing_evidence` | `brand_claim`

```
:START_ID(Ingredient),:END_ID(Effect),type,evidence_type,graph_score:float,paper_count:int
CERAMIDE NP,BARRIER_REPAIR,improves,pubmed_evidence,0.494696,5
HYALURONIC ACID,ANTI_AGING,improves,pubmed_evidence,0.451076,1
```

## edges/relates_to.csv

```
:START_ID(Effect),:END_ID(Concern)
ANTI_INFLAMMATORY,ACNE
SEBUM_REGULATION,ACNE
```

---

## Neo4j bulk import

```bash
docker run --rm \
  -v /home/graphdb/neo4j/data:/data \
  -v /home/graphdb/neo4j/import:/var/lib/neo4j/import \
  neo4j:5 \
  neo4j-admin database import full \
    --nodes=Product=/var/lib/neo4j/import/nodes/product.csv \
    --nodes=Ingredient=/var/lib/neo4j/import/nodes/ingredient.csv \
    --nodes=Effect=/var/lib/neo4j/import/nodes/effect.csv \
    --nodes=Concern=/var/lib/neo4j/import/nodes/concern.csv \
    --relationships=CONTAINS=/var/lib/neo4j/import/edges/contains.csv \
    --relationships=AFFECTS=/var/lib/neo4j/import/edges/affects.csv \
    --relationships=RELATES_TO=/var/lib/neo4j/import/edges/relates_to.csv \
    --overwrite-destination \
    neo4j
```

> `--overwrite-destination`: DB가 비어있거나 전체 재적재 시 사용. 운영 중 DB에는 쓰지 말 것.

---

## ID 매칭 규칙

| 엣지 | START_ID | END_ID |
| --- | --- | --- |
| CONTAINS | `product_id:ID(Product)` | `ingredient_id:ID(Ingredient)` |
| AFFECTS | `ingredient_id:ID(Ingredient)` | `effect_code:ID(Effect)` |
| RELATES_TO | `effect_code:ID(Effect)` | `concern_code:ID(Concern)` |

엣지의 `:START_ID` / `:END_ID` 값은 노드 CSV의 `:ID(...)` 값과 **정확히** 일치해야 한다.

**왜 일치해야 하는가?**

CSV가 여러 파일로 나뉘어 있어도 ID 값으로 노드를 연결함.

```
# nodes/ingredient.csv
CERAMIDE NP, CERAMIDE NP, ...   ← ingredient_id = CERAMIDE NP

# nodes/effect.csv
BARRIER_REPAIR, Barrier Repair  ← effect_code = BARRIER_REPAIR

# edges/affects.csv
CERAMIDE NP, BARRIER_REPAIR, improves, pubmed_evidence, 0.494696, 5
↑ ingredient_id       ↑ effect_code
```

Neo4j bulk import 실행 시 각 CSV의 `:ID()` 와 엣지 CSV의 `:START_ID()` / `:END_ID()` 를 매칭해서 자동으로 연결함.
