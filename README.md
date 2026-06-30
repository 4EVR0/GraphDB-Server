# GraphDB Server

올리브영 스킨케어 상품-성분-효능-피부고민 지식 그래프 (Neo4j)

## 그래프 구조

```
(Product) -[CONTAINS]-> (Ingredient) -[AFFECTS]-> (Effect) -[RELATES_TO]-> (Concern)
```

| 노드 | 설명 |
|------|------|
| Product | 올리브영 상품 |
| Ingredient | 성분 (INCI명 기준) |
| Effect | 효능 (항염, 장벽 강화 등) |
| Concern | 피부 고민 (여드름, 민감성 등) |

## 시작하기

### 사전 준비

- Docker
- AWS CLI (`aws configure` 설정 완료)

### 환경변수 설정

```bash
cp .env.example .env
# .env에 NEO4J_PASSWORD 입력
```

### 실행

```bash
# Neo4j 컨테이너 실행
docker compose up -d

# S3에서 CSV 받아서 import까지 한 번에 (배치 미지정 시 최신 자동 선택)
bash load.sh

# 특정 gold 배치 지정 (batch_job= 접두사는 생략 가능)
bash load.sh 20260511_174455

# product / contains 버전까지 명시
bash load.sh 20260511_174455 oliveyoung_neo4j_20260510_063644 oliveyoung_neo4j_20260512_133725

# 환경변수로도 지정 가능
BATCH_JOB=20260511_174455 bash load.sh
```

배치/버전을 지정하지 않으면 각 S3 경로에서 이름 정렬 기준 최신 배치를 자동 선택합니다.
적재 직전 노드/엣지 카운트를 로그로 남기며, `validate.py` 통과가 import 전제 조건입니다.

브라우저: `http://localhost:7474`

## 검증

import 전에 노드/엣지 ID 일치 여부를 확인합니다.

```bash
python3 validate.py
```

모든 항목이 `[OK]` 여야 import 진행 가능합니다.

## 주요 쿼리

```cypher
-- 노드 수
MATCH (n) RETURN labels(n), count(n);

-- 관계 수
MATCH ()-[r]->() RETURN type(r), count(r);

-- 샘플 경로
MATCH (p:Product)-[:CONTAINS]->(i:Ingredient)-[:AFFECTS]->(e:Effect)-[:RELATES_TO]->(c:Concern)
RETURN p.product_name, i.inci_name, e.effect_name_en, c.concern_name_ko
LIMIT 10;
```