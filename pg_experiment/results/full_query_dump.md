# 쿼리별 전체 원본 결과 (파라미터 고정 1회 실행)

## products_by_ingredients
파라미터: `{'ingredient_names': ['GLYCERIN', '1,2-HEXANEDIOL', 'BUTYLENE GLYCOL'], 'appropriate_categories': ['로션', '세럼', '앰플', '크림', '기타']}`

### Neo4j 결과 (5건)
```
1. product_id='b404934a-bcad-5e25-92c5-0530ce9bc76f', product_name='AHC 365 레드세럼 랩핑 모델링', brand='AHC', category='기타', matched_count=3, matched_ingredients=['GLYCERIN', '1,2-HEXANEDIOL', 'BUTYLENE GLYCOL']
2. product_id='476a6bf3-9f00-5af4-8df3-579240ab5a2a', product_name='AHC 에이치 멜라루트 앰플 스페셜', brand='AHC', category='앰플', matched_count=3, matched_ingredients=['GLYCERIN', '1,2-HEXANEDIOL', 'BUTYLENE GLYCOL']
3. product_id='dad7b7ae-79bc-5dc1-ab5f-16c5141d7267', product_name='AHC 에이치 멜라루트 크림', brand='AHC', category='크림', matched_count=3, matched_ingredients=['GLYCERIN', '1,2-HEXANEDIOL', 'BUTYLENE GLYCOL']
4. product_id='4529246a-125a-5e09-b642-319b4dda3b8b', product_name='AHC 온리 포맨 로션', brand='AHC', category='로션', matched_count=3, matched_ingredients=['GLYCERIN', '1,2-HEXANEDIOL', 'BUTYLENE GLYCOL']
5. product_id='da16bdbf-689d-5b22-bb22-2e99111155d4', product_name='AHC 유스 래스팅 리얼 아이크림 포 페이스', brand='AHC', category='크림', matched_count=3, matched_ingredients=['GLYCERIN', '1,2-HEXANEDIOL', 'BUTYLENE GLYCOL']
```

### Postgres 결과 (5건)
```
1. product_id=UUID('b404934a-bcad-5e25-92c5-0530ce9bc76f'), product_name='AHC 365 레드세럼 랩핑 모델링', brand='AHC', category='기타', matched_count=3, matched_ingredients=['1,2-HEXANEDIOL', 'BUTYLENE GLYCOL', 'GLYCERIN']
2. product_id=UUID('476a6bf3-9f00-5af4-8df3-579240ab5a2a'), product_name='AHC 에이치 멜라루트 앰플 스페셜', brand='AHC', category='앰플', matched_count=3, matched_ingredients=['1,2-HEXANEDIOL', 'BUTYLENE GLYCOL', 'GLYCERIN']
3. product_id=UUID('dad7b7ae-79bc-5dc1-ab5f-16c5141d7267'), product_name='AHC 에이치 멜라루트 크림', brand='AHC', category='크림', matched_count=3, matched_ingredients=['1,2-HEXANEDIOL', 'BUTYLENE GLYCOL', 'GLYCERIN']
4. product_id=UUID('4529246a-125a-5e09-b642-319b4dda3b8b'), product_name='AHC 온리 포맨 로션', brand='AHC', category='로션', matched_count=3, matched_ingredients=['1,2-HEXANEDIOL', 'BUTYLENE GLYCOL', 'GLYCERIN']
5. product_id=UUID('da16bdbf-689d-5b22-bb22-2e99111155d4'), product_name='AHC 유스 래스팅 리얼 아이크림 포 페이스', brand='AHC', category='크림', matched_count=3, matched_ingredients=['1,2-HEXANEDIOL', 'BUTYLENE GLYCOL', 'GLYCERIN']
```

## ingredients_by_effects
파라미터: `{'effects': ['ANTI_INFLAMMATORY', 'SOOTHING', 'HYDRATING']}`

### Neo4j 결과 (20건)
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

### Postgres 결과 (20건)
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

## path_by_effects
파라미터: `{'effects': ['ANTI_INFLAMMATORY', 'SOOTHING', 'HYDRATING']}`

### Neo4j 결과 (10건)
```
1. effect_code='SOOTHING', effect_name='Soothing', ingredient='RETINOL', ingredient_kor='레티놀', evidence_type='pubmed_evidence', graph_score=0.71784, product_name='코스메쉐프 흑당고 진액 영양 주름앰플', brand='코스메쉐프'
2. effect_code='SOOTHING', effect_name='Soothing', ingredient='RETINOL', ingredient_kor='레티놀', evidence_type='pubmed_evidence', graph_score=0.71784, product_name='썸바이미 레티놀 인텐스 액션 아이크림', brand='썸바이미'
3. effect_code='SOOTHING', effect_name='Soothing', ingredient='RETINOL', ingredient_kor='레티놀', evidence_type='pubmed_evidence', graph_score=0.71784, product_name='마몽드 포어 슈링커 바쿠치올 레티놀 토너', brand='마몽드'
4. effect_code='SOOTHING', effect_name='Soothing', ingredient='RETINOL', ingredient_kor='레티놀', evidence_type='pubmed_evidence', graph_score=0.71784, product_name='아이디얼포맨 퍼펙트 올인원', brand='아이디얼포맨'
5. effect_code='SOOTHING', effect_name='Soothing', ingredient='RETINOL', ingredient_kor='레티놀', evidence_type='pubmed_evidence', graph_score=0.71784, product_name='마미케어 바다포도 레티놀 모공앰플', brand='마미케어'
6. effect_code='SOOTHING', effect_name='Soothing', ingredient='RETINOL', ingredient_kor='레티놀', evidence_type='pubmed_evidence', graph_score=0.71784, product_name='디오디너리 레티놀 0.5% 인 스쿠알란', brand='디오디너리'
7. effect_code='SOOTHING', effect_name='Soothing', ingredient='RETINOL', ingredient_kor='레티놀', evidence_type='pubmed_evidence', graph_score=0.71784, product_name='마몽드 레티놀 앰플 토너', brand='마몽드'
8. effect_code='SOOTHING', effect_name='Soothing', ingredient='RETINOL', ingredient_kor='레티놀', evidence_type='pubmed_evidence', graph_score=0.71784, product_name='이니스프리 레티놀 그린티 PDRN 스킨부스터 토너', brand='이니스프리'
9. effect_code='SOOTHING', effect_name='Soothing', ingredient='RETINOL', ingredient_kor='레티놀', evidence_type='pubmed_evidence', graph_score=0.71784, product_name='마몽드 포어 슈링커 바쿠치올 크림', brand='마몽드'
10. effect_code='SOOTHING', effect_name='Soothing', ingredient='RETINOL', ingredient_kor='레티놀', evidence_type='pubmed_evidence', graph_score=0.71784, product_name='아이오페 맨 프로 레티놀 올인원', brand='아이오페'
```

### Postgres 결과 (10건)
```
1. effect_code='SOOTHING', effect_name='Soothing', ingredient='RETINOL', ingredient_kor='레티놀', evidence_type='pubmed_evidence', graph_score=0.71784, product_name='토리든 셀메이징 저분자 콜라겐 탄력 아이크림', brand='토리든'
2. effect_code='SOOTHING', effect_name='Soothing', ingredient='RETINOL', ingredient_kor='레티놀', evidence_type='pubmed_evidence', graph_score=0.71784, product_name='피캄 레티놀라겐 앰플샷 폼클렌저', brand='피캄'
3. effect_code='SOOTHING', effect_name='Soothing', ingredient='RETINOL', ingredient_kor='레티놀', evidence_type='pubmed_evidence', graph_score=0.71784, product_name='폴라초이스 클리니컬 0.3% 레티놀 + 2% 바쿠치올 트리트먼트', brand='폴라초이스'
4. effect_code='SOOTHING', effect_name='Soothing', ingredient='RETINOL', ingredient_kor='레티놀', evidence_type='pubmed_evidence', graph_score=0.71784, product_name='리얼베리어 레티니올 모공 타이트닝 세럼', brand='리얼베리어'
5. effect_code='SOOTHING', effect_name='Soothing', ingredient='RETINOL', ingredient_kor='레티놀', evidence_type='pubmed_evidence', graph_score=0.71784, product_name='마몽드 포어 슈링커 바쿠치올 패드', brand='마몽드'
6. effect_code='SOOTHING', effect_name='Soothing', ingredient='RETINOL', ingredient_kor='레티놀', evidence_type='pubmed_evidence', graph_score=0.71784, product_name='마미케어 그린 콜라겐 부스팅젤', brand='마미케어'
7. effect_code='SOOTHING', effect_name='Soothing', ingredient='RETINOL', ingredient_kor='레티놀', evidence_type='pubmed_evidence', graph_score=0.71784, product_name='이니스프리 레티놀 그린티 PDRN 앰플', brand='이니스프리'
8. effect_code='SOOTHING', effect_name='Soothing', ingredient='RETINOL', ingredient_kor='레티놀', evidence_type='pubmed_evidence', graph_score=0.71784, product_name='테라로직 레티놀 안티링클3D 모공 앰플', brand='테라로직'
9. effect_code='SOOTHING', effect_name='Soothing', ingredient='RETINOL', ingredient_kor='레티놀', evidence_type='pubmed_evidence', graph_score=0.71784, product_name='아이오페 레티놀 레티젝션 세럼', brand='아이오페'
10. effect_code='SOOTHING', effect_name='Soothing', ingredient='RETINOL', ingredient_kor='레티놀', evidence_type='pubmed_evidence', graph_score=0.71784, product_name='셀퓨전씨 레이저 리쥬버네이션 크림', brand='셀퓨전씨'
```

## products_by_concern
파라미터: `{'concern_code': 'ACNE'}`

### Neo4j 결과 (10건)
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

### Postgres 결과 (10건)
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
