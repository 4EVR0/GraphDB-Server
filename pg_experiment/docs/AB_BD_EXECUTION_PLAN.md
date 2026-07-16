# A vs B, B vs D 실행 계획

`LLM_QUERY_GENERATION.md`에서 설계한 두 비교(§6)를 **실제로 어떻게 돌릴지**만
다루는 문서. 프로덕션 코드/배포/가드레일은 다루지 않는다(그건
`DYNAMIC_QUERY_IMPLEMENTATION.md`) — 여기는 순수하게 오프라인 실험 스크립트를
어떤 순서로, 뭘 재사용해서, 어디에 만들지에 대한 계획이다.

|  | 고정 쿼리 | LLM 가변 쿼리 |
|---|---|---|
| **GraphDB** | **A** (기존 쿼리) | **B** (신규) |
| **RDB** | ~~C~~ (안 씀) | **D** (신규, 조건부) |

## 1. 이미 있어서 그대로 재사용하는 것

- **gold label**: `eval/gold_labels.py`의 `PRODUCTION_CONCERN_EFFECT_MAP`
  (26개 concern → effect 정답 매핑) + 그래프에서 gold 성분/제품을 뽑는 함수.
- **채점 로직**: `eval/graphrag_ranking_eval.py`의 Precision@K / NDCG@K 계산.
  `eval/RESULTS.md`에 쓰인 방법론 그대로 재사용.
- **A(고정 쿼리) 실행**: `pg_experiment/queries.py`의 `CYPHER_*` 상수를 그대로
  Neo4j에 실행하면 됨 — 새로 만들 게 없음.
- **DB/데이터**: `pg_experiment`에 이미 떠 있는 Neo4j(기존 컨테이너)와
  Postgres(`pg_experiment/docker-compose.yml`, 5433) 그대로 사용.

## 2. 새로 만들어야 하는 것

전부 `pg_experiment/llm_eval/` 아래 새 폴더를 만들어서 넣는다(오프라인 실험용
스크립트라 프로덕션 `app/` 디렉터리와 분리).

```
pg_experiment/llm_eval/
├── questions.py           # 자연어 질문 세트 (concern별, gold_labels.py와 매칭)
├── prompts/
│   ├── cypher_generation.txt
│   └── sql_generation.txt      # B vs D 단계에서만 필요
├── generate.py             # LLM 호출 -> Cypher/SQL 생성 (+ EXPLAIN 검증만)
├── run_ab.py                # A vs B 실행 + 채점
└── run_bd.py                 # B vs D 실행 + 채점 (조건부)
```

### 2-1. `questions.py` — 질문 세트

`gold_labels.py`의 concern 코드 26개를 키로 써서, 각 concern당 자연어 질문
1~2개를 매핑한다.

```python
QUESTIONS = {
    "ACNE": ["여드름 때문에 고민이에요, 어떤 성분이 좋을까요?"],
    "DRY_SKIN": ["피부가 너무 건조해요", ...],
    ...  # 26개 전부
}
```

### 2-2. `prompts/cypher_generation.txt`

- 그래프 스키마 설명 (`README.md`의 구조 그대로)
- 출력 형식: `{"cypher": "...", "params": {...}}` JSON만
- few-shot 예시 2~3개
- **읽기 전용 안내만** (`MATCH만 써라`) — 실제 DB 권한 제한은 안 함, 실험용
  스크립트가 직접 실행 전 `EXPLAIN`으로 한 번 더 거르기 때문에 이 단계에서는
  텍스트 안내만으로 충분함.

### 2-3. `generate.py`

```python
async def generate_cypher(question: str) -> dict:
    ...  # llm_client.py의 call_llm()과 같은 패턴, get_async_llm_client() 재사용
    return {"cypher": ..., "params": ...}

def validate(cypher: str, driver) -> bool:
    with driver.session() as s:
        s.run(f"EXPLAIN {cypher}")  # 문법만 확인, 결과는 안 씀
    return True  # 실패하면 예외
```

재시도는 최소 구현으로 — 문법 오류 시 1회만 재생성 (프로덕션처럼 여러 겹
가드레일 필요 없음, 실험 스크립트가 로컬에서 도는 것뿐).

### 2-4. `run_ab.py`

1. `questions.py`의 26개 concern 질문을 순회
2. 각 질문마다:
   - A: `pg_experiment/queries.py`의 `CYPHER_INGREDIENTS_BY_EFFECTS` 등을
     해당 concern의 gold effect로 실행
   - B: `generate.py`로 Cypher 생성 → 검증 → 실행
3. A 결과, B 결과 각각 `graphrag_ranking_eval.py`의 Precision@K/NDCG@K로 채점
4. concern별 표 + 평균 요약 출력 (`RESULTS.md`와 비슷한 포맷)

### 2-5. `run_bd.py` (조건부)

`run_ab.py` 결과에서 B가 A보다 품질이 뚜렷이 높을 때만 착수.

1. `prompts/sql_generation.txt` 작성 (스키마는 `pg_experiment/schema.sql` DDL)
2. `generate.py`에 `generate_sql()` 추가, Postgres에 `EXPLAIN`으로 검증
3. B(이미 있음)와 D(신규 생성) 결과를 같은 gold label로 채점해 비교

## 3. 실행 순서 (요약)

1. `questions.py` 작성
2. `prompts/cypher_generation.txt` + `generate.py`(Cypher 부분) 작성
3. `run_ab.py` 실행 → A vs B 결과 확인
4. **여기서 판단**: B가 A보다 품질이 안 오르면 종료, 보고서만 작성
5. B가 A보다 품질이 오르면 → `prompts/sql_generation.txt` + `generate.py`(SQL
   부분) 추가 작성 → `run_bd.py` 실행 → B vs D 결과 확인
6. 두 결과 종합해서 `pg_experiment/docs/RESULTS_llm_query.md`(가칭)로 정리

## 4. 진행 여부

계획 단계. 실제 스크립트 작성은 착수 확인 후 진행.
