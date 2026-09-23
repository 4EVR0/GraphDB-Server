# GraphDB Server

**올리브영 상품–성분–효능–피부고민 지식 그래프 (Neo4j)**

피부 고민에서 역방향으로 탐색해 "왜 이 성분인가"를 근거 논문 수와 함께 설명하는, 4EVR0 KG-RAG 추천 시스템의 그래프 서빙 레이어입니다.

---

## 그래프 스키마

<div align="center">
<img src="assets/kg_schema.png" alt="지식그래프 스키마 — Product · Ingredient · Effect · Concern과 추천 탐색 흐름" width="900">
</div>

```
(Product) -[CONTAINS]-> (Ingredient) -[AFFECTS]-> (Effect) -[RELATES_TO]-> (Concern)
```

| 노드 | 설명 |
|------|------|
| **Product** | 올리브영 상품 (상품명·브랜드·가격·카테고리) |
| **Ingredient** | 성분 (INCI명 기준) |
| **Effect** | 효능 (항염, 장벽 강화, 톤 개선 등) |
| **Concern** | 피부 고민 (여드름, 민감성 피부, 색소침착 등) |

| 관계 | 설명 |
|------|------|
| **CONTAINS** | 상품이 해당 성분을 포함 |
| **AFFECTS** | 성분이 효능에 작용 — PubMed 근거 논문 수를 속성으로 보유 |
| **RELATES_TO** | 효능이 피부 고민과 연결 |

추천은 이 경로를 **역방향**으로 탐색합니다: `Concern → Effect → Ingredient → Product`

### 규모

| Product | Ingredient | CONTAINS | Claim(AFFECTS) |
|:---:|:---:|:---:|:---:|
| 3,141 | 3,221 | 112,966 | 5,387 |

---

## 데이터 적재 구조

Iceberg **Gold 레이어** 산출물을 Neo4j CSV로 내보내 적재합니다.

- **초기 적재** — `load.sh`가 S3에서 CSV를 받아 전체 import
- **증분 반영(CDC)** — 이후에는 전체 재적재 대신, Iceberg 스냅샷 비교(N-1 vs N)로 생성된 변경분(NEW / CHANGED / REMOVED)만 반영

---

## 시작하기

### 사전 준비

- Docker
- AWS CLI (`aws configure` 설정 완료)

### 환경변수 설정

```bash
cp .env.example .env
# .env에 NEO4J_PASSWORD 입력
chmod 600 .env
```

`.env`는 Git에 추가하지 않고 서버 소유자만 읽고 쓸 수 있도록 관리합니다.
기존 데이터베이스의 비밀번호를 바꿀 때는 `.env`만 수정하지 말고 Neo4j 사용자
비밀번호도 함께 변경해야 합니다. `NEO4J_AUTH`는 데이터 디렉터리를 처음 만들 때
사용되는 초기 인증 설정입니다.

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

---

## 검증

import 전에 노드/엣지 ID 일치 여부를 확인합니다.

```bash
python3 validate.py
```

모든 항목이 `[OK]` 여야 import 진행 가능합니다.

---

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
