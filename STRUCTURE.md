# 폴더 구조 설명

```
/home/graphdb/
├── csv/
│   ├── nodes/
│   └── edges/
├── neo4j/
│   ├── data/
│   ├── import/
│   ├── logs/
│   └── plugins/
├── docker-compose.yml
├── load.sh
├── validate.py
└── SETUP.md
```

---

## csv/

**S3에서 받아온 원본 CSV 보관 디렉토리.**

`load.sh` 실행 시 S3 → 여기로 다운로드됨. 원본을 그대로 유지하는 용도라서 import 후에도 삭제하지 않음.

### csv/nodes/

Neo4j에서 **노드(정점)** 가 될 데이터. 각 파일이 하나의 노드 타입에 해당함.

| 파일 | 노드 타입 | 설명 |
|------|----------|------|
| `product.csv` | `Product` | 올리브영 상품 (상품ID, 상품명, 브랜드, 카테고리) |
| `ingredient.csv` | `Ingredient` | 성분 (INCI명, 한글명, COSING 기능) |
| `effect.csv` | `Effect` | 효능 (브라이트닝, 안티에이징 등) |
| `concern.csv` | `Concern` | 피부 고민 (색소침착, 여드름 등) |

헤더 형식이 `:ID(라벨명)` 이어야 Neo4j가 노드 ID로 인식함.
```
product_id:ID(Product),product_name,brand,category
```

### csv/edges/

Neo4j에서 **관계(엣지)** 가 될 데이터. 노드와 노드를 연결함.

| 파일 | 관계 타입 | 연결 |
|------|----------|------|
| `contains.csv` | `CONTAINS` | Product → Ingredient (상품이 성분을 포함) |
| `affects.csv` | `AFFECTS` | Ingredient → Effect (성분이 효능에 영향) |
| `relates_to.csv` | `RELATES_TO` | Effect → Concern (효능이 피부 고민과 연관) |

헤더 형식이 `:START_ID(라벨)` / `:END_ID(라벨)` 이어야 함.
이 값이 nodes/ CSV의 `:ID()` 값과 **정확히 일치**해야 관계가 연결됨.

---

## neo4j/

Docker 컨테이너 내부 Neo4j 디렉토리를 호스트에 마운트한 것.
컨테이너를 삭제해도 데이터가 여기 남아있어서 유실되지 않음.

### neo4j/data/

**실제 DB 파일이 저장되는 곳.** `neo4j-admin import` 실행 후 그래프 데이터가 여기 쌓임.
절대 임의로 건드리면 안 됨.

### neo4j/import/

**`neo4j-admin database import`가 읽는 디렉토리.**
Neo4j 컨테이너 내부 경로 `/var/lib/neo4j/import` 와 마운트되어 있음.

`csv/` 에서 여기로 파일을 복사한 뒤 import 명령을 실행함.
```
csv/nodes/product.csv → neo4j/import/nodes/product.csv
```

### neo4j/logs/

Neo4j 실행 로그. 오류 발생 시 여기서 확인.
```bash
tail -f /home/graphdb/neo4j/logs/neo4j.log
```

### neo4j/plugins/

APOC 등 Neo4j 플러그인 jar 파일이 들어가는 곳.
`docker-compose.yml`에서 `NEO4J_PLUGINS: '["apoc"]'` 설정 시 자동 다운로드됨.

---

## 파일 설명

| 파일 | 역할 |
|------|------|
| `docker-compose.yml` | Neo4j 컨테이너 설정 (포트, 비밀번호, 볼륨 마운트) |
| `load.sh` | S3 다운로드 → import 디렉토리 복사 → bulk import 한 번에 실행 |
| `validate.py` | import 전 노드/엣지 ID 일치 여부 검증 |
| `SETUP.md` | 전체 셋업 체크리스트 |
| `STRUCTURE.md` | 이 파일. 폴더 구조 설명 |