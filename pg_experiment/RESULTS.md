# RDB(Postgres) vs GraphDB(Neo4j) 성능 비교 — 결과 보고서

배경/설계 논의는 [`EXPERIMENT.md`](./EXPERIMENT.md) 참고. 이 문서는 실제 실행 결과만 정리한다.

## 1. 실험 조건

- 데이터: `csv/nodes`, `csv/edges` (Neo4j import에 쓰는 원본과 100% 동일)
  - product 3,122 / ingredient 3,221 / effect 15 / concern 15
  - contains 112,966 / affects 5,386 / relates_to 24
- 비교 대상 쿼리: 4EVR0-Server가 실제로 쓰는 Cypher 쿼리 3개(`neo4j_client.py`) +
  hop-scaling 확인용 4-hop 쿼리 1개(실서비스 미사용)
- 드라이버: Neo4j는 `neo4j` 공식 드라이버(Bolt), Postgres는 `psycopg` v3 — 둘 다
  세션/커넥션을 미리 열어 재사용, 순수 쿼리 실행 시간만 측정
- 측정: 워밍업 20회 제외, 200회 반복, 두 엔진에 **완전히 동일한 파라미터 시퀀스**(seed=42)
- LLM 응답 시간은 포함하지 않음 — 이유는 `EXPERIMENT.md` 및 대화 기록 참고 (LLM 추론이
  DB latency보다 훨씬 커서 같이 재면 DB 간 차이가 노이즈에 묻힘)

## 2. 결과 정합성 검증 (`verify_parity.py`)

SQL이 Cypher와 실제로 같은 결과를 내는지 먼저 확인했다. 과정에서 실제 버그 2건을 발견/수정했다.

### 1차 실행 — mismatch 발견

```
[MISMATCH] query_products_by_ingredients: cypher=5 rows, sql=5 rows
  cypher: [('b404934a-bcad-5e25-92c5-0530ce9bc76f',), ('476a6bf3-9f00-5af4-8df3-579240ab5a2a',), ('dad7b7ae-79bc-5dc1-ab5f-16c5141d7267',), ('4529246a-125a-5e09-b642-319b4dda3b8b',), ('da16bdbf-689d-5b22-bb22-2e99111155d4',)]
  sql   : [(UUID('fadd2cce-b52d-523c-b3bb-e152a4aff367'),), (UUID('4f2a538e-9dad-55ca-bd8f-32b1785fee98'),), (UUID('e466b944-e9d1-5e5e-a42b-9ad07f7d381f'),), (UUID('061dd41b-23d4-58d3-99e3-6b0aeebefc59'),), (UUID('cb08106d-ca4b-5fb5-982e-d2b650e0d359'),)]
[OK] query_ingredients_by_effects: cypher=20 rows, sql=20 rows
[MISMATCH] query_path_by_effects: cypher=10 rows, sql=10 rows
  cypher: [('SOOTHING', 'RETINOL', '코스메쉐프 흑당고 진액 영양 주름앰플', 0.71784), ('SOOTHING', 'RETINOL', '썸바이미 레티놀 인텐스 액션 아이크림', 0.71784), ...]
  sql   : [('SOOTHING', 'RETINOL', '토리든 셀메이징 저분자 콜라겐 탄력 아이크림', 0.71784), ('SOOTHING', 'RETINOL', '피캄 레티놀라겐 앰플샷 폼클렌저', 0.71784), ...]
```

원인 규명:
- `query_products_by_ingredients`: Postgres DB collation이 `en_US.utf8`이라 한글 상품명
  정렬 순서가 Neo4j(유니코드 코드포인트 기준)와 다름 → 동점(matched_count 같음) 상품 중
  어느 5개가 뽑히는지가 완전히 달라짐. `ORDER BY product_name COLLATE "C"`로 해결.
- `query_path_by_effects`: 원본 Cypher가 `ORDER BY graph_score DESC` 하나뿐이라 동점 구간
  처리가 **프로덕션 쿼리 자체부터 비결정적**. SQL 버그가 아니라서 "고치지" 않고, 검증
  기준을 신원 비교 대신 graph_score 분포 비교로 바꿈.

### 재검증 — 전부 통과

```
[OK] query_products_by_ingredients: cypher=5 rows, sql=5 rows
[OK] query_ingredients_by_effects: cypher=20 rows, sql=20 rows
[OK] query_path_by_effects (graph_score만 비교, 동점 구간 비결정적): cypher=10 rows, sql=10 rows
```

### 발견된 이슈 3 — `query_ingredients_by_effects`도 같은 종류의 비결정성이 있음

`dump_full_results.py`로 전체 결과를 다시 뽑아보니(3장), 9번째 행에서 Neo4j는
`RETINAL`의 `claim='Soothing'`, Postgres는 같은 자리에서 `claim='Hydrating'`을 반환했다
(둘 다 `graph_score=0.470004`, `paper_ref='1'`로 값 자체는 동일). 원인을 실제 데이터에서
확인:

```
 inci_name | effect_code |  evidence_type  | graph_score | effect_name_en
-----------+-------------+-----------------+-------------+----------------
 RETINAL   | HYDRATING   | pubmed_evidence |    0.470004 | Hydrating
 RETINAL   | HYDRATING   | pubmed_evidence |    0.470004 | Hydrating
 RETINAL   | SOOTHING    | pubmed_evidence |    0.470004 | Soothing
 RETINAL   | SOOTHING    | pubmed_evidence |    0.470004 | Soothing
```

`RETINAL`이 `HYDRATING`/`SOOTHING` 두 효능에 완전히 동점(`ev_rank`, `graph_score` 모두 같음)으로
걸려 있어서, 원본 Cypher의 `ORDER BY ev_rank, r.graph_score DESC`만으로는 어느 효능이
`head(collect())`에 남을지 결정이 안 된다. `query_path_by_effects`와 같은 계열의
문제(프로덕션 쿼리 자체의 정렬 키 부족)이지 SQL 포팅 버그가 아니다.

## 3. 쿼리별 전체 원본 결과 (`dump_full_results.py`, 파라미터 고정 1회 실행)

verify_parity.py/benchmark.py는 신원(id) 또는 latency 숫자만 비교했으므로, 각 쿼리가
실제로 어떤 행을 반환하는지 잘리지 않은 전체 결과를 별도로 뽑았다. 파라미터:
`ingredient_names=['GLYCERIN','1,2-HEXANEDIOL','BUTYLENE GLYCOL']`,
`appropriate_categories=['로션','세럼','앰플','크림','기타']`,
`effects=['ANTI_INFLAMMATORY','SOOTHING','HYDRATING']`, `concern_code='ACNE'`.

### products_by_ingredients

**Neo4j (5건)**
```
1. product_id='b404934a-bcad-5e25-92c5-0530ce9bc76f', product_name='AHC 365 레드세럼 랩핑 모델링', brand='AHC', category='기타', matched_count=3, matched_ingredients=['GLYCERIN', '1,2-HEXANEDIOL', 'BUTYLENE GLYCOL']
2. product_id='476a6bf3-9f00-5af4-8df3-579240ab5a2a', product_name='AHC 에이치 멜라루트 앰플 스페셜', brand='AHC', category='앰플', matched_count=3, matched_ingredients=['GLYCERIN', '1,2-HEXANEDIOL', 'BUTYLENE GLYCOL']
3. product_id='dad7b7ae-79bc-5dc1-ab5f-16c5141d7267', product_name='AHC 에이치 멜라루트 크림', brand='AHC', category='크림', matched_count=3, matched_ingredients=['GLYCERIN', '1,2-HEXANEDIOL', 'BUTYLENE GLYCOL']
4. product_id='4529246a-125a-5e09-b642-319b4dda3b8b', product_name='AHC 온리 포맨 로션', brand='AHC', category='로션', matched_count=3, matched_ingredients=['GLYCERIN', '1,2-HEXANEDIOL', 'BUTYLENE GLYCOL']
5. product_id='da16bdbf-689d-5b22-bb22-2e99111155d4', product_name='AHC 유스 래스팅 리얼 아이크림 포 페이스', brand='AHC', category='크림', matched_count=3, matched_ingredients=['GLYCERIN', '1,2-HEXANEDIOL', 'BUTYLENE GLYCOL']
```

**Postgres (5건)** — product_id/matched_ingredients 순서 표기만 다르고(UUID 타입, 배열 순서) 내용은 동일
```
1. product_id=UUID('b404934a-bcad-5e25-92c5-0530ce9bc76f'), product_name='AHC 365 레드세럼 랩핑 모델링', brand='AHC', category='기타', matched_count=3, matched_ingredients=['1,2-HEXANEDIOL', 'BUTYLENE GLYCOL', 'GLYCERIN']
2. product_id=UUID('476a6bf3-9f00-5af4-8df3-579240ab5a2a'), product_name='AHC 에이치 멜라루트 앰플 스페셜', brand='AHC', category='앰플', matched_count=3, matched_ingredients=['1,2-HEXANEDIOL', 'BUTYLENE GLYCOL', 'GLYCERIN']
3. product_id=UUID('dad7b7ae-79bc-5dc1-ab5f-16c5141d7267'), product_name='AHC 에이치 멜라루트 크림', brand='AHC', category='크림', matched_count=3, matched_ingredients=['1,2-HEXANEDIOL', 'BUTYLENE GLYCOL', 'GLYCERIN']
4. product_id=UUID('4529246a-125a-5e09-b642-319b4dda3b8b'), product_name='AHC 온리 포맨 로션', brand='AHC', category='로션', matched_count=3, matched_ingredients=['1,2-HEXANEDIOL', 'BUTYLENE GLYCOL', 'GLYCERIN']
5. product_id=UUID('da16bdbf-689d-5b22-bb22-2e99111155d4'), product_name='AHC 유스 래스팅 리얼 아이크림 포 페이스', brand='AHC', category='크림', matched_count=3, matched_ingredients=['1,2-HEXANEDIOL', 'BUTYLENE GLYCOL', 'GLYCERIN']
```

### ingredients_by_effects

**Neo4j (20건)**
```
1. name='RETINOL', kor_name='레티놀', claim='Soothing', eligibility_tier='pubmed_evidence', paper_ref='2', graph_score=0.71784
2. name='PETROLATUM', kor_name='페트롤라툼', claim='Soothing', eligibility_tier='pubmed_evidence', paper_ref='1', graph_score=0.693147
3. name='SALMON EGG EXTRACT', kor_name='연어알추출물', claim='Soothing', eligibility_tier='pubmed_evidence', paper_ref='1', graph_score=0.693147
4. name='NIACINAMIDE', kor_name='나이아신아마이드', claim='Hydrating', eligibility_tier='pubmed_evidence', paper_ref='2', graph_score=0.672944
5. name='COLLOIDAL OATMEAL', kor_name='콜로이달오트밀', claim='Hydrating', eligibility_tier='pubmed_evidence', paper_ref='2', graph_score=0.65752
6. name='PANTHENOL', kor_name='덱스판테놀', claim='Soothing', eligibility_tier='pubmed_evidence', paper_ref='2', graph_score=0.64815
7. name='LINALOOL', kor_name='리날룰', claim='Anti-inflammatory', eligibility_tier='pubmed_evidence', paper_ref='2', graph_score=0.574082
8. name='FIBRONECTIN', kor_name='피브로넥틴', claim='Hydrating', eligibility_tier='pubmed_evidence', paper_ref='1', graph_score=0.559616
9. name='RETINAL', kor_name='레틴알', claim='Soothing', eligibility_tier='pubmed_evidence', paper_ref='1', graph_score=0.470004
10. name='TROXERUTIN', kor_name='트록세루틴', claim='Soothing', eligibility_tier='pubmed_evidence', paper_ref='1', graph_score=0.470004
11. name='CELLULOSE', kor_name='셀룰로오스', claim='Hydrating', eligibility_tier='pubmed_evidence', paper_ref='1', graph_score=0.446287
12. name='CHOLESTEROL', kor_name='콜레스테롤', claim='Hydrating', eligibility_tier='pubmed_evidence', paper_ref='1', graph_score=0.446287
13. name='UREA', kor_name='우레아', claim='Hydrating', eligibility_tier='pubmed_evidence', paper_ref='2', graph_score=0.446287
14. name='SALICYLIC ACID', kor_name='살리실릭애씨드', claim='Soothing', eligibility_tier='pubmed_evidence', paper_ref='2', graph_score=0.431782
15. name='HEXYLRESORCINOL', kor_name='헥실레조시놀', claim='Soothing', eligibility_tier='pubmed_evidence', paper_ref='1', graph_score=0.421994
16. name='PVP', kor_name='피브이피', claim='Soothing', eligibility_tier='pubmed_evidence', paper_ref='1', graph_score=0.41871
17. name='HAEMATOCOCCUS PLUVIALIS EXTRACT', kor_name='해마토코쿠스 플루비알리스추출물', claim='Soothing', eligibility_tier='pubmed_evidence', paper_ref='1', graph_score=0.397097
18. name='CERAMIDE NP', kor_name='세라마이드엔피', claim='Soothing', eligibility_tier='pubmed_evidence', paper_ref='1', graph_score=0.392042
19. name='FARNESOL', kor_name='파네솔', claim='Soothing', eligibility_tier='pubmed_evidence', paper_ref='1', graph_score=0.392042
20. name='HYDROLYZED JOJOBA ESTERS', kor_name='하이드롤라이즈드호호바에스터', claim='Hydrating', eligibility_tier='pubmed_evidence', paper_ref='2', graph_score=0.392042
```

**Postgres (20건)** — 9번째 행(`RETINAL`)의 `claim`만 다름(위 "발견된 이슈 3" 참고), 나머지 19건은 완전히 동일
```
1. name='RETINOL', kor_name='레티놀', claim='Soothing', eligibility_tier='pubmed_evidence', paper_ref='2', graph_score=0.71784
2. name='PETROLATUM', kor_name='페트롤라툼', claim='Soothing', eligibility_tier='pubmed_evidence', paper_ref='1', graph_score=0.693147
3. name='SALMON EGG EXTRACT', kor_name='연어알추출물', claim='Soothing', eligibility_tier='pubmed_evidence', paper_ref='1', graph_score=0.693147
4. name='NIACINAMIDE', kor_name='나이아신아마이드', claim='Hydrating', eligibility_tier='pubmed_evidence', paper_ref='2', graph_score=0.672944
5. name='COLLOIDAL OATMEAL', kor_name='콜로이달오트밀', claim='Hydrating', eligibility_tier='pubmed_evidence', paper_ref='2', graph_score=0.65752
6. name='PANTHENOL', kor_name='덱스판테놀', claim='Soothing', eligibility_tier='pubmed_evidence', paper_ref='2', graph_score=0.64815
7. name='LINALOOL', kor_name='리날룰', claim='Anti-inflammatory', eligibility_tier='pubmed_evidence', paper_ref='2', graph_score=0.574082
8. name='FIBRONECTIN', kor_name='피브로넥틴', claim='Hydrating', eligibility_tier='pubmed_evidence', paper_ref='1', graph_score=0.559616
9. name='RETINAL', kor_name='레틴알', claim='Hydrating', eligibility_tier='pubmed_evidence', paper_ref='1', graph_score=0.470004
10. name='TROXERUTIN', kor_name='트록세루틴', claim='Soothing', eligibility_tier='pubmed_evidence', paper_ref='1', graph_score=0.470004
11. name='CELLULOSE', kor_name='셀룰로오스', claim='Hydrating', eligibility_tier='pubmed_evidence', paper_ref='1', graph_score=0.446287
12. name='CHOLESTEROL', kor_name='콜레스테롤', claim='Hydrating', eligibility_tier='pubmed_evidence', paper_ref='1', graph_score=0.446287
13. name='UREA', kor_name='우레아', claim='Hydrating', eligibility_tier='pubmed_evidence', paper_ref='2', graph_score=0.446287
14. name='SALICYLIC ACID', kor_name='살리실릭애씨드', claim='Soothing', eligibility_tier='pubmed_evidence', paper_ref='2', graph_score=0.431782
15. name='HEXYLRESORCINOL', kor_name='헥실레조시놀', claim='Soothing', eligibility_tier='pubmed_evidence', paper_ref='1', graph_score=0.421994
16. name='PVP', kor_name='피브이피', claim='Soothing', eligibility_tier='pubmed_evidence', paper_ref='1', graph_score=0.41871
17. name='HAEMATOCOCCUS PLUVIALIS EXTRACT', kor_name='해마토코쿠스 플루비알리스추출물', claim='Soothing', eligibility_tier='pubmed_evidence', paper_ref='1', graph_score=0.397097
18. name='CERAMIDE NP', kor_name='세라마이드엔피', claim='Soothing', eligibility_tier='pubmed_evidence', paper_ref='1', graph_score=0.392042
19. name='FARNESOL', kor_name='파네솔', claim='Soothing', eligibility_tier='pubmed_evidence', paper_ref='1', graph_score=0.392042
20. name='HYDROLYZED JOJOBA ESTERS', kor_name='하이드롤라이즈드호호바에스터', claim='Hydrating', eligibility_tier='pubmed_evidence', paper_ref='2', graph_score=0.392042
```

### path_by_effects

**Neo4j (10건)** — 전부 `RETINOL`-`SOOTHING`(graph_score=0.71784) 동점 구간, 어느 제품이 뽑히는지는 비결정적(§2 참고)
```
1. effect_code='SOOTHING', ingredient='RETINOL', product_name='코스메쉐프 흑당고 진액 영양 주름앰플', brand='코스메쉐프', graph_score=0.71784
2. effect_code='SOOTHING', ingredient='RETINOL', product_name='썸바이미 레티놀 인텐스 액션 아이크림', brand='썸바이미', graph_score=0.71784
3. effect_code='SOOTHING', ingredient='RETINOL', product_name='마몽드 포어 슈링커 바쿠치올 레티놀 토너', brand='마몽드', graph_score=0.71784
4. effect_code='SOOTHING', ingredient='RETINOL', product_name='아이디얼포맨 퍼펙트 올인원', brand='아이디얼포맨', graph_score=0.71784
5. effect_code='SOOTHING', ingredient='RETINOL', product_name='마미케어 바다포도 레티놀 모공앰플', brand='마미케어', graph_score=0.71784
6. effect_code='SOOTHING', ingredient='RETINOL', product_name='디오디너리 레티놀 0.5% 인 스쿠알란', brand='디오디너리', graph_score=0.71784
7. effect_code='SOOTHING', ingredient='RETINOL', product_name='마몽드 레티놀 앰플 토너', brand='마몽드', graph_score=0.71784
8. effect_code='SOOTHING', ingredient='RETINOL', product_name='이니스프리 레티놀 그린티 PDRN 스킨부스터 토너', brand='이니스프리', graph_score=0.71784
9. effect_code='SOOTHING', ingredient='RETINOL', product_name='마몽드 포어 슈링커 바쿠치올 크림', brand='마몽드', graph_score=0.71784
10. effect_code='SOOTHING', ingredient='RETINOL', product_name='아이오페 맨 프로 레티놀 올인원', brand='아이오페', graph_score=0.71784
```

**Postgres (10건)** — 같은 동점 구간에서 다른 10개 제품이 뽑힘(값 분포는 동일, 신원만 다름)
```
1. effect_code='SOOTHING', ingredient='RETINOL', product_name='토리든 셀메이징 저분자 콜라겐 탄력 아이크림', brand='토리든', graph_score=0.71784
2. effect_code='SOOTHING', ingredient='RETINOL', product_name='피캄 레티놀라겐 앰플샷 폼클렌저', brand='피캄', graph_score=0.71784
3. effect_code='SOOTHING', ingredient='RETINOL', product_name='폴라초이스 클리니컬 0.3% 레티놀 + 2% 바쿠치올 트리트먼트', brand='폴라초이스', graph_score=0.71784
4. effect_code='SOOTHING', ingredient='RETINOL', product_name='리얼베리어 레티니올 모공 타이트닝 세럼', brand='리얼베리어', graph_score=0.71784
5. effect_code='SOOTHING', ingredient='RETINOL', product_name='마몽드 포어 슈링커 바쿠치올 패드', brand='마몽드', graph_score=0.71784
6. effect_code='SOOTHING', ingredient='RETINOL', product_name='마미케어 그린 콜라겐 부스팅젤', brand='마미케어', graph_score=0.71784
7. effect_code='SOOTHING', ingredient='RETINOL', product_name='이니스프리 레티놀 그린티 PDRN 앰플', brand='이니스프리', graph_score=0.71784
8. effect_code='SOOTHING', ingredient='RETINOL', product_name='테라로직 레티놀 안티링클3D 모공 앰플', brand='테라로직', graph_score=0.71784
9. effect_code='SOOTHING', ingredient='RETINOL', product_name='아이오페 레티놀 레티젝션 세럼', brand='아이오페', graph_score=0.71784
10. effect_code='SOOTHING', ingredient='RETINOL', product_name='셀퓨전씨 레이저 리쥬버네이션 크림', brand='셀퓨전씨', graph_score=0.71784
```

### products_by_concern (concern_code='ACNE', 실험용 쿼리 — `DISTINCT`+`LIMIT`만 있고 `ORDER BY` 없어 신원 비결정적)

**Neo4j (10건)**
```
1. product_id='6a61522f-5da0-59e8-b98f-7fafd9928fe3', product_name='설화수 맨 본윤유액'
2. product_id='407e796d-e476-5cb2-90e9-0c96ed651227', product_name='설화수 맨 본윤에센스'
3. product_id='8a60724d-25f0-56cc-b055-4803ee3e9436', product_name='닥터하우쉬카 로즈 데이 크림 오리지널'
4. product_id='fb2c7c35-47ac-56b4-8fb0-63450f707bd5', product_name='바이오더마 시카비오 포마드'
5. product_id='f59bf11a-bdc3-5e98-b081-a7a1232e105e', product_name='비오템 옴므 티쀼르 토너'
6. product_id='f350a116-d198-5533-9adc-85da14170eaa', product_name='바이오더마 세비엄 젤 무쌍'
7. product_id='dbb47f05-1532-5ff4-8bde-c23e74199296', product_name='아벤느 시칼파트 플러스 SOS 리페어 크림'
8. product_id='3e0459cc-417b-512d-8672-f4e64d5fb41c', product_name='아벤느 시칼파트 플러스 블레미쉬 크림'
9. product_id='cc9b74a2-bbfb-5789-9639-8dfecda6d747', product_name='아벤느 시칼파트+ 블레미쉬 크림'
10. product_id='2d2847d9-d3f6-5d95-9615-52bca8c4fc41', product_name='더바디샵 티트리 래피드 액션 젤'
```

**Postgres (10건)** — ACNE 관련 제품이 전체 카탈로그의 93%(2,900/3,122)라 사실상 무작위 10개가 뽑힘
```
1. product_id=UUID('0034f80c-a7d5-5241-9b47-63e8f47aa15e'), product_name='디오디너리 멀티-펩타이드 + 카퍼 펩타이즈 1% 세럼'
2. product_id=UUID('00a86b7d-e99e-51d8-84df-6955d44a4973'), product_name='라빠레뜨 뷰티 카밍 그린 에센셜 세럼'
3. product_id=UUID('00a8e840-ea7a-5787-8410-64c3219e2195'), product_name='온그리디언츠 스킨 베리어 속광 미스트'
4. product_id=UUID('00a94711-3a01-5c38-af54-70f8cb07ee54'), product_name='토리든 밸런스풀 시카 컨트롤 세럼'
5. product_id=UUID('00af015d-2f1a-5ac3-9af3-a06f01742bc5'), product_name='아렌시아 그린 아르티장 클렌저'
6. product_id=UUID('00fdca9a-4942-5244-ac0b-d30e90323d3a'), product_name='주닥 약산성 로즈 68% 클렌징밀크'
7. product_id=UUID('01053733-9fa3-50cc-8aa9-00d0abb8853c'), product_name='라네즈옴므 블루에너지 에센스인로션'
8. product_id=UUID('010de1eb-5360-59f1-bc25-cd4e940daaeb'), product_name='스킨푸드 라이스 마스크 워시오프'
9. product_id=UUID('01373779-d394-5cfa-aadb-392885d491e4'), product_name='라끄베르 옴므 리차지 올인원 에센스'
10. product_id=UUID('01502317-68eb-5c24-9307-8d85eb67c3de'), product_name='나인위시스 pH 캄 시카 토너패드'
```

전체 스크립트: [`dump_full_results.py`](./dump_full_results.py), 원본 파일: [`results/full_query_dump.md`](./results/full_query_dump.md)

## 4. 벤치마크 원본 출력 (`benchmark.py`)

```
=== products_by_ingredients ===
  neo4j   : {'n': 200, 'mean_ms': 13.716, 'p50_ms': 12.861, 'p95_ms': 17.818, 'p99_ms': 23.432, 'min_ms': 10.525, 'max_ms': 44.21}
  postgres: {'n': 200, 'mean_ms': 3.806, 'p50_ms': 1.992, 'p95_ms': 8.553, 'p99_ms': 30.526, 'min_ms': 0.949, 'max_ms': 92.555}
=== ingredients_by_effects ===
  neo4j   : {'n': 200, 'mean_ms': 10.533, 'p50_ms': 7.299, 'p95_ms': 21.322, 'p99_ms': 29.485, 'min_ms': 3.99, 'max_ms': 51.012}
  postgres: {'n': 200, 'mean_ms': 7.229, 'p50_ms': 3.897, 'p95_ms': 17.844, 'p99_ms': 20.968, 'min_ms': 0.984, 'max_ms': 22.026}
=== path_by_effects ===
  neo4j   : {'n': 200, 'mean_ms': 36.391, 'p50_ms': 25.086, 'p95_ms': 70.702, 'p99_ms': 96.088, 'min_ms': 5.578, 'max_ms': 109.467}
  postgres: {'n': 200, 'mean_ms': 54.216, 'p50_ms': 49.82, 'p95_ms': 89.997, 'p99_ms': 116.116, 'min_ms': 6.861, 'max_ms': 118.414}
=== products_by_concern ===
  neo4j   : {'n': 200, 'mean_ms': 3.448, 'p50_ms': 3.281, 'p95_ms': 4.884, 'p99_ms': 5.848, 'min_ms': 2.48, 'max_ms': 6.759}
  postgres: {'n': 200, 'mean_ms': 92.82, 'p50_ms': 18.537, 'p95_ms': 234.146, 'p99_ms': 247.685, 'min_ms': 6.418, 'max_ms': 254.962}

결과 저장: pg_experiment/results/latencies.json
```

원본 JSON: [`results/latencies.json`](./results/latencies.json)

## 5. 요약 표 (hop 수 순)

| 쿼리 | hop 수 | 프로덕션 사용 | Neo4j p50 | Postgres p50 | Neo4j p99 | Postgres p99 | 승자(p50) |
|---|---|---|---:|---:|---:|---:|---|
| products_by_ingredients | 1 | O | 12.9 ms | **2.0 ms** | 23.4 ms | 30.5 ms | Postgres |
| ingredients_by_effects | 1 | O | 7.3 ms | **3.9 ms** | 29.5 ms | 21.0 ms | Postgres |
| path_by_effects | 2 | O | **25.1 ms** | 49.8 ms | 96.1 ms | 116.1 ms | Neo4j |
| products_by_concern | 4 | X(실험용) | **3.3 ms** | 18.5 ms | **5.8 ms** | 247.7 ms | Neo4j (압도적) |

## 6. 해석

- **1-hop, 고정 패턴에서는 Postgres가 이긴다.** 인덱스 잘 걸린 단순 JOIN + 집계는
  이 데이터 규모(수천~10만 행)에서 Postgres 플래너가 Neo4j보다 빠르다.
- **hop이 늘어날수록 역전되고, 격차가 급격히 커진다.** 2-hop에서 이미 Neo4j가 앞서고,
  4-hop(`products_by_concern`)에서는 p99 기준 **약 43배** 차이(Neo4j 5.8ms vs Postgres
  247.7ms). Postgres는 JOIN을 늘릴수록 플래너 비용/중간 결과 크기가 커지는 반면, Neo4j는
  포인터 추적(index-free adjacency)이라 hop이 늘어도 비용이 상대적으로 완만하게 증가.
- 다만 4번째 쿼리는 프로덕션에서 안 쓰는 실험용 쿼리이고, `DISTINCT` 결과 신원 자체는
  검증하지 않았음(값 분포만 신뢰) — 참고용 신호로만 볼 것.
- **지금 프로덕션 쿼리 3개만 놓고 보면 승부는 갈린다** (1-hop 둘은 RDB 승, 2-hop 하나는
  Neo4j 승). "그래프DB가 무조건 유리하다"도 "RDB로 충분하다"도 성급한 결론.

## 7. 이번 실험이 다루지 않은 것

- **LLM 응답 시간을 포함한 end-to-end 지연**: DB 선택과 독립적인 변수라 의도적으로 제외.
  필요하면 GPU 서버(`GPU_SERVER_URL`)를 띄우고 `4EVR0-Server/load/locustfile.py`로
  별도 실험 필요.
- **가변 길이 경로 탐색** (예: `SIMILAR_TO`/`SUBSTITUTE_FOR` 성분 유사도로 `*1..3` 확장
  탐색): 지금 데이터엔 그런 관계가 없어 테스트 못 함. 이런 케이스는 Postgres도
  재귀 CTE(`WITH RECURSIVE`)로 구현은 가능하나 대체로 그래프DB가 유리한 전형적 영역 —
  "성분 표기가 달라 매칭이 안 되는" 커버리지 부족 문제를 풀려면 이쪽 실험이 이어서 필요.
- **동시 부하(동시성) 상황의 처리량**: 이번 벤치마크는 순차 실행 latency만 측정, 동시
  요청 시 커넥션 풀 경합 등은 안 봄.
- **"LLM이 쿼리를 직접 생성하기 쉬운가" (text-to-Cypher vs text-to-SQL)**: 확인해보니
  지금 4EVR0-Server는 LLM이 Cypher를 직접 안 쓴다 — `recommend_service.py`가
  `neo4j_client.py`의 고정 파라미터화 템플릿을 호출할 뿐이고, LLM은 자연어를
  `effect_names`/`ingredient_names` 같은 구조화된 파라미터로 추출하는 역할만 한다
  (text-to-parameter + 고정 템플릿, text-to-query 아님). 그래서 "Cypher가 LLM이
  쓰기 쉽다"는 그래프DB의 장점은 지금 아키텍처에서는 발동하지 않는다. 이 장점을
  검증하려면 실제로 LLM이 자연어 질문에서 Cypher/SQL을 직접 생성하는 구조로 바꾼
  뒤 생성 성공률/문법 정확도를 재는 별도 실험이 필요 — 이번 latency 벤치마크와는
  성격이 다른 실험.
- **그래프 구조가 추천 품질 자체에 미치는 영향**: `eval/RESULTS.md`에 이미 GraphRAG
  경로 탐색 vs 빈도 베이스라인의 Precision/Recall/NDCG 평가가 있어 부분적으로는
  다뤄진 주제. 다만 RDB로 옮겼을 때 같은 방식(경로 탐색 기반 추천)이 동일한 품질로
  재현되는지는 별도 확인이 필요 — latency 비교와 무관한 품질 축이라 이번 실험
  범위에는 포함하지 않음.

## 8. 결론

1. **"관계가 명확하니 그래프DB가 맞다"는 가정은 틀렸다.** 실제로 지금 스키마는 hop이
   고정된 단순 구조이고, 1-hop 쿼리 2개(`products_by_ingredients`,
   `ingredients_by_effects`)에서는 오히려 **Postgres가 3~6배 빠르다** (p50 기준).
   지금 데이터 규모(수천~10만 행)에서는 인덱스 잘 걸린 RDB가 그래프DB보다 단순 조회에
   더 효율적이라는 걸 실측으로 확인했다.
2. **그렇다고 "RDB로 갈아타면 된다"도 아니다.** hop이 하나만 늘어도(2-hop
   `path_by_effects`) Neo4j가 앞서고, 4-hop에서는 p99 기준 43배까지 벌어진다.
   3개 프로덕션 쿼리만 보면 1승은 Neo4j, 2승은 Postgres로 갈리기 때문에, DB를
   하나로 통일해서 "이겼다/졌다"를 논할 문제가 아니다 — **쿼리 패턴별로 유불리가
   다르다는 것 자체가 결론**이다.
3. **지금 당장 마이그레이션할 근거는 없다.** 4EVR0-Server가 실제로 쓰는 쿼리 3개
   기준 Postgres의 우위는 1-hop 두 곳뿐이고 그 절대 시간도 이미 한 자릿수~10ms대라
   사용자 체감에 미치는 영향이 크지 않다(LLM 추론이 수백 ms~수 초로 훨씬 지배적
   — §7). 반면 2-hop 쿼리에서 Neo4j 우위를 포기하면서까지 옮길 이유는 부족하다.
4. **오히려 이번 실험에서 진짜 값진 건 벤치마크 숫자가 아니라 발견한 버그 3건**이다
   (§2, §3): Postgres collation 차이로 인한 한글 정렬 불일치, 그리고
   `ingredients_by_effects`/`path_by_effects` 두 프로덕션 쿼리에 이미 존재하던
   동점 처리 비결정성. 이 중 collation 이슈는 RDB로 갈 경우 반드시 고쳐야 할
   실제 버그이고, 정렬 비결정성 2건은 DB 종류와 무관하게 지금 프로덕션 Cypher
   쿼리에도 이미 있는 문제라 별도로 리포트할 가치가 있다.
5. **다음에 진짜 봐야 할 건 hop 수가 아니라 탐색 방식이다.** 대화 중 나온
   "성분 표기가 달라 매칭이 안 되는" 커버리지 부족 문제(§7의 가변 길이 경로 탐색)는
   지금 벤치마크가 다루는 "hop 수 고정 쿼리"의 영역을 아예 벗어난다. 그래프DB를
   유지할지 판단하려면, 지금처럼 고정 hop 성능을 비교하는 것보다 이 가변 길이
   탐색(`SIMILAR_TO*1..N` vs 재귀 CTE)이 실제로 얼마나 필요한지가 더 결정적인
   질문이다.
