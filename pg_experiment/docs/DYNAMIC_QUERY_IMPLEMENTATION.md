# 가변 쿼리 생성 방식 — 구현 계획

`LLM_QUERY_GENERATION.md`가 "왜/무엇을 재야 하는가"였다면, 이 문서는 **실제로
코드를 어떻게 짤 것인가**다. 기존 4EVR0-Server 코드베이스의 패턴(`llm_client.py`,
`app/prompts/`, `neo4j_client.py`)을 그대로 따라간다. 아직 구현 전, 설계 단계.

## 1. 어디에 놓을 것인가

기존 고정 템플릿 경로(`app/clients/neo4j_client.py`, `recommend_service.py`)는
건드리지 않는다. 새 파일을 나란히 추가해서 기존 경로와 완전히 분리한다.

```
app/
├── clients/
│   ├── neo4j_client.py          # 기존, 안 건드림
│   └── dynamic_query_client.py  # 신규 — LLM에게 쿼리 생성시키고 실행
├── services/
│   ├── recommend_service.py     # 기존, 안 건드림
│   └── dynamic_recommend_service.py  # 신규 — dynamic_query_client 사용
└── prompts/
    ├── cypher_generation.txt    # 신규
    └── sql_generation.txt       # 신규
```

`app/core/config.py`에 `settings.query_mode: Literal["fixed", "dynamic"] = "fixed"`
플래그를 추가해서, `recommend_service.py`가 이 값에 따라 두 경로 중 하나를
호출하도록 라우팅한다. 기본값은 `"fixed"`라 아무것도 안 건드리면 지금과 100%
동일하게 동작한다.

## 2. 프롬프트 설계 — 기존 `app/prompts/` 관례 그대로

`profile_extraction.txt`처럼 프롬프트를 코드에 하드코딩하지 않고 별도 파일로
분리, `load_prompt()`/`prompt_version()`(sha1 해시로 버전 추적, MLflow 연동)을
그대로 재사용한다.

`app/prompts/cypher_generation.txt` 내용 구성:
1. 그래프 스키마 설명 (`README.md`의 그래프 구조 + 각 노드/관계 속성 목록)
2. 읽기 전용 제약 명시 ("MATCH만 쓰고 CREATE/MERGE/DELETE/SET은 절대 쓰지 마라")
3. 출력 형식 강제: `{"cypher": "...", "params": {...}}` 형태의 JSON만 출력
   (기존 `call_llm()`이 `response_format={"type": "json_object"}`를 쓰는 것과 동일 패턴)
4. few-shot 예시 2~3개 (짧은 질문 → 정답 Cypher)

`app/prompts/sql_generation.txt`도 구조는 동일, 스키마는 `pg_experiment/schema.sql`
DDL을 그대로 넣는다.

## 3. 쿼리 생성 클라이언트

`app/clients/dynamic_query_client.py`. `llm_client.py`의 `call_llm()`과 같은
패턴(`get_async_llm_client()`, `settings.gpu_model`, `temperature=0`)을 쓴다.

```python
async def generate_query(question: str, engine: Literal["cypher", "sql"]) -> GeneratedQuery:
    prompt_name = "cypher_generation" if engine == "cypher" else "sql_generation"
    system_prompt = load_prompt(prompt_name)
    client = get_async_llm_client()

    response = await client.chat.completions.create(
        model=settings.gpu_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    data = json.loads(response.choices[0].message.content or "{}")
    return GeneratedQuery(query=data["query"], params=data.get("params", {}))
```

## 4. 실행 전 가드레일

기존 `neo4j_client.py`가 문자열 f-string으로 파라미터 없이 쿼리를 실행하는
것과 달리(쿼리 자체가 고정 템플릿이라 안전했음), 여기서는 **쿼리 텍스트 자체가
LLM 출력**이라 방어 계층이 필수다.

1. **DB 계정 자체를 읽기 전용으로 분리** (가장 중요, 애플리케이션 레벨 필터보다
   우선):
   - Neo4j: `CREATE ROLE dynamic_query_reader; GRANT MATCH {*} ON GRAPH * NODES *, RELATIONSHIPS * TO dynamic_query_reader;` (쓰기 권한 부여 자체를 안 함)
   - Postgres: `CREATE ROLE dynamic_query_reader NOLOGIN; GRANT SELECT ON ALL TABLES IN SCHEMA public TO dynamic_query_reader;`
   - 고정 템플릿 경로(`neo4j_client.py`, 기존 Postgres 연결)는 지금 쓰는 계정
     그대로 두고, `dynamic_query_client.py`만 이 읽기 전용 계정으로 연결한다 —
     별도 `settings.neo4j_readonly_uri` / `settings.postgres_readonly_dsn` 추가.
2. **LIMIT 강제**: 생성된 쿼리 문자열에 `LIMIT`이 없으면 서버에서 `LIMIT 20`을
   덧붙인다 (정규식으로 끝에 `LIMIT \d+`가 있는지 확인 후 없으면 추가).
3. **실행 전 `EXPLAIN`**: Cypher는 `EXPLAIN <query>`, SQL은 `EXPLAIN <query>`를
   먼저 실행해서 문법 오류를 여기서 걸러낸다. 통과 못 하면 바로 5번 재시도로.
4. **타임아웃**: Neo4j는 세션에 `session.run(query, timeout=5)`, Postgres는
   `SET statement_timeout = '5s'`를 커넥션 시작 시 설정.

## 5. 재시도(self-correction) 루프

```python
async def execute_with_retry(question: str, engine: str, max_retries: int = 2):
    error_context = ""
    for attempt in range(max_retries + 1):
        generated = await generate_query(question + error_context, engine)
        try:
            validate_via_explain(generated)  # 4-3
            rows = await execute(generated)  # 4-1 read-only 계정, 4-2 LIMIT, 4-4 timeout
            return rows, generated, attempt
        except (SyntaxError, ExecutionError) as e:
            error_context = f"\n\n[이전 시도 실패: {e}] 이 오류를 피해서 다시 생성하세요."
    return [], None, max_retries  # 전부 실패 시 빈 결과 (기존 neo4j_client.py의 except 패턴과 동일)
```

기존 `neo4j_client.py`의 모든 함수가 `except Exception: return []`로 실패를
조용히 삼키는 것과 같은 원칙 — 이 경로도 실패 시 추천 자체를 막지 않고 빈
결과로 폴백한다.

## 6. 로깅 — 생성된 쿼리 텍스트 자체를 남겨야 함

기존 `_log_query()`(`neo4j_client.py`)는 `func_name`/`params`/`duration_ms`/
`result_count`만 남긴다. 고정 템플릿이라 쿼리 텍스트 자체는 코드만 봐도 알 수
있어서 안 남겨도 됐다. 가변 쿼리는 **매번 다른 텍스트가 생성**되므로, 디버깅/
사후 분석을 위해 생성된 쿼리 원문과 재시도 횟수를 반드시 로그에 남겨야 한다:

```python
logger.info(
    "event=dynamic_query func=%s engine=%s attempt=%d duration_ms=%.2f "
    "result_count=%d generated_query=%s",
    "generate_query", engine, attempt, duration_ms, len(rows), generated.query,
)
```

## 7. 단계적 롤아웃

1. **오프라인 평가만** (`LLM_QUERY_GENERATION.md` §4/§5): 이 단계에서는 프로덕션
   코드를 전혀 건드리지 않고 `pg_experiment`에서 질문 세트 → 생성 → 채점만
   돌린다. 여기서 A vs B, B vs D 품질 비교(§6)가 나온다.
2. **섀도 모드**: 1번 결과가 가변으로 갈 가치가 있다고 나오면, `dynamic_recommend_service.py`를
   추가하되 **응답에는 안 쓰고 로그만 남기는 모드**로 실제 트래픽에 붙인다
   (`generate_traffic.sh`로 흘려보내며 검증 가능). 실사용자 질문 분포에서도
   오프라인 평가와 비슷한 품질/hop 분포가 나오는지 확인.
3. **점진적 트래픽 전환**: 2번이 안정적이면 `settings.query_mode`를 트래픽의
   일부(예: 5% → 20% → 50%)에만 `"dynamic"`으로 켜서 실제 사용자 반응까지
   확인한 뒤 전체 전환 여부를 결정.

프로덕션에 한 번에 붙이지 않는 이유는 `LLM_QUERY_GENERATION.md` §7에 이미 정리한
리스크(모델 의존성, 안정성, 레이턴시 트레이드오프) 때문 — 이 계획은 그 리스크를
단계적으로 확인하면서 진행하기 위한 것이다.

## 8. 진행 여부

설계 단계 문서. 실제 코드(프롬프트 파일, `dynamic_query_client.py` 등) 작성은
`LLM_QUERY_GENERATION.md`의 오프라인 평가(1단계)에서 유의미한 품질 개선이
확인된 뒤 착수.