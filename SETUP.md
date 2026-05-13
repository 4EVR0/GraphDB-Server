# Neo4j GraphDB 셋업 체크리스트

S3 버킷: `s3://YOUR_BUCKET/graph_gold_csvs/batch_job=YYYYMMDD_HHMMSS/`

---

## 체크리스트

### 1. 환경 준비
- [x] Docker 설치 (v29.4.3)
- [x] AWS CLI 설치 (v2)
- [x] 디렉토리 구조 생성 (`/home/graphdb/csv/`, `/home/graphdb/neo4j/`)
- [ ] AWS 인증 설정 (`aws configure`)
- [ ] docker 그룹 적용 (로그아웃 후 재로그인 또는 `newgrp docker`)

### 2. S3 → 로컬 CSV 다운로드
- [ ] `aws s3 sync` 로 CSV 전체 내려받기
  ```bash
  aws s3 sync s3://YOUR_BUCKET/graph_gold_csvs/batch_job=YYYYMMDD_HHMMSS/ /home/graphdb/csv/
  ```
- [ ] 파일 확인 (nodes/ edges/ 하위 7개 CSV)

### 3. Neo4j 컨테이너 실행
- [ ] Neo4j 이미지 pull (`neo4j:5`)
- [ ] 컨테이너 실행 (`docker compose up -d`)
- [ ] 브라우저 접속 확인: `http://localhost:7474`

### 4. ID 일치 검증 ← 임포트 전 반드시 확인
- [ ] 검증 스크립트 실행
  ```bash
  python3 /home/graphdb/validate.py
  ```
- [ ] 모든 항목 `[OK]` 확인 (불일치 있으면 해당 CSV 수정 후 재실행)

> **왜 필요한가?**
> 엣지 CSV의 `:START_ID` / `:END_ID` 값이 노드 CSV의 `:ID()` 값과 하나라도 다르면
> bulk import 시 해당 관계가 조용히 누락됨. 에러 없이 그냥 넘어가서 나중에 발견하기 어려움.

### 5. CSV → Neo4j 임포트
- [ ] CSV를 Neo4j import 디렉토리로 복사
- [ ] `neo4j-admin database import full` 실행
- [ ] 임포트 결과 확인 (노드/관계 수)

### 6. 검증 쿼리
- [ ] 노드 수 확인
  ```cypher
  MATCH (n) RETURN labels(n), count(n);
  ```
- [ ] 관계 수 확인
  ```cypher
  MATCH ()-[r]->() RETURN type(r), count(r);
  ```
- [ ] 샘플 경로 조회
  ```cypher
  MATCH (p:Product)-[:CONTAINS]->(i:Ingredient)-[:AFFECTS]->(e:Effect)-[:RELATES_TO]->(c:Concern)
  RETURN p.product_name, i.inci_name, e.effect_name_en, c.concern_name_ko LIMIT 10;
  ```

---

## 그래프 스키마

```
(Product) -[CONTAINS]-> (Ingredient) -[AFFECTS]-> (Effect) -[RELATES_TO]-> (Concern)
```

| 노드 | ID 컬럼 | 주요 속성 |
|------|---------|----------|
| Product | `product_id:ID(Product)` | product_name, brand, category |
| Ingredient | `ingredient_id:ID(Ingredient)` | inci_name, kor_name, cosing_functions |
| Effect | `effect_code:ID(Effect)` | effect_name_en |
| Concern | `concern_code:ID(Concern)` | concern_name_ko |

| 엣지 | START_ID | END_ID | 속성 |
|------|----------|--------|------|
| CONTAINS | Product | Ingredient | - |
| AFFECTS | Ingredient | Effect | type, evidence_type, graph_score, paper_count |
| RELATES_TO | Effect | Concern | - |

### AFFECTS 허용값
- **type**: `improves` \| `reduces` \| `prevents` \| `increases` \| `is_safe_for` \| `is_well_tolerated_for` \| `causes` \| `does_not_cause` \| `inhibits` \| `stimulates` \| `regulates` \| `modulates`
- **evidence_type**: `pubmed_evidence` \| `cosing_evidence` \| `brand_claim`
- **graph_score**: float (0~1, 근거 강도)
- **paper_count**: int (뒷받침 논문 수)

---

## 파일 구조

```
/home/graphdb/
├── SETUP.md             ← 이 파일
├── docker-compose.yml   ← Neo4j 컨테이너 설정
├── load.sh              ← S3 다운로드 + import 자동화 스크립트
├── validate.py          ← 임포트 전 ID 일치 검증 스크립트
├── csv/
│   ├── nodes/
│   │   ├── product.csv
│   │   ├── ingredient.csv
│   │   ├── effect.csv
│   │   └── concern.csv
│   └── edges/
│       ├── contains.csv
│       ├── affects.csv
│       └── relates_to.csv
└── neo4j/
    ├── data/            ← DB 데이터 (영구 보존)
    ├── logs/
    ├── import/          ← neo4j-admin import 시 CSV 위치
    └── plugins/
```