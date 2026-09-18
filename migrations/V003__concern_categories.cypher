// GENERATED FILE — 직접 수정 금지.
// 원본: GraphRAG_Pipeline/db/seed/taxonomy.yaml
// 재생성: python GraphRAG_Pipeline/scripts/generate_taxonomy_artifacts.py

// concern별 적합 제품 카테고리 (미지정 concern은 default_categories 적용)

MERGE (m:TaxonomyConfig {key: 'default_categories'})
SET m.values = ['크림', '세럼', '앰플', '에센스', '로션', '토너', '미스트', '올인원'];
MATCH (c:Concern {concern_code: 'ACNE'})
SET c.appropriate_categories = ['세럼', '앰플', '에센스', '로션', '토너', '미스트', '올인원', '필링스크럽'];
MATCH (c:Concern {concern_code: 'COMEDONES'})
SET c.appropriate_categories = ['세럼', '앰플', '에센스', '로션', '토너', '미스트', '올인원'];
MATCH (c:Concern {concern_code: 'PORE_CONGESTION'})
SET c.appropriate_categories = ['세럼', '앰플', '에센스', '로션', '토너', '미스트', '올인원'];
MATCH (c:Concern {concern_code: 'ENLARGED_PORES'})
SET c.appropriate_categories = ['세럼', '앰플', '에센스', '로션', '토너', '미스트', '올인원'];
MATCH (c:Concern {concern_code: 'OILY_SKIN'})
SET c.appropriate_categories = ['세럼', '앰플', '에센스', '로션', '토너', '미스트', '올인원'];
MATCH (c:Concern {concern_code: 'SENSITIVE_SKIN'})
SET c.appropriate_categories = ['크림', '세럼', '앰플', '에센스', '로션', '토너', '미스트', '올인원'];
MATCH (c:Concern {concern_code: 'REDNESS'})
SET c.appropriate_categories = ['크림', '세럼', '앰플', '에센스', '로션', '토너', '미스트', '올인원'];
MATCH (c:Concern {concern_code: 'IRRITATED_SKIN'})
SET c.appropriate_categories = ['크림', '세럼', '앰플', '에센스', '로션', '토너', '미스트', '올인원'];
MATCH (c:Concern {concern_code: 'ATOPIC_PRONE'})
SET c.appropriate_categories = ['크림', '세럼', '앰플', '에센스', '로션', '토너', '미스트', '올인원'];
MATCH (c:Concern {concern_code: 'ROSACEA_PRONE'})
SET c.appropriate_categories = ['크림', '세럼', '앰플', '에센스', '로션', '토너', '미스트', '올인원'];
MATCH (c:Concern {concern_code: 'DRY_SKIN'})
SET c.appropriate_categories = ['크림', '세럼', '앰플', '에센스', '로션', '토너', '미스트', '올인원', '페이스오일'];
MATCH (c:Concern {concern_code: 'DEHYDRATED_SKIN'})
SET c.appropriate_categories = ['크림', '세럼', '앰플', '에센스', '로션', '토너', '미스트', '올인원', '페이스오일'];
MATCH (c:Concern {concern_code: 'FLAKY_SKIN'})
SET c.appropriate_categories = ['크림', '세럼', '앰플', '에센스', '로션', '토너', '미스트', '올인원', '페이스오일', '필링스크럽'];
MATCH (c:Concern {concern_code: 'ROUGH_TEXTURE'})
SET c.appropriate_categories = ['크림', '세럼', '앰플', '에센스', '로션', '토너', '미스트', '올인원', '필링스크럽'];
MATCH (c:Concern {concern_code: 'BARRIER_DAMAGE'})
SET c.appropriate_categories = ['크림', '세럼', '앰플', '에센스', '로션', '토너', '미스트', '올인원', '페이스오일'];
MATCH (c:Concern {concern_code: 'HYPERPIGMENTATION'})
SET c.appropriate_categories = ['크림', '세럼', '앰플', '에센스', '로션', '토너', '미스트', '올인원'];
MATCH (c:Concern {concern_code: 'DULLNESS'})
SET c.appropriate_categories = ['크림', '세럼', '앰플', '에센스', '로션', '토너', '미스트', '올인원'];
MATCH (c:Concern {concern_code: 'UNEVEN_SKIN_TONE'})
SET c.appropriate_categories = ['크림', '세럼', '앰플', '에센스', '로션', '토너', '미스트', '올인원'];
MATCH (c:Concern {concern_code: 'BLEMISHES'})
SET c.appropriate_categories = ['크림', '세럼', '앰플', '에센스', '로션', '토너', '미스트', '올인원'];
MATCH (c:Concern {concern_code: 'POST_ACNE_MARKS'})
SET c.appropriate_categories = ['크림', '세럼', '앰플', '에센스', '로션', '토너', '미스트', '올인원'];
MATCH (c:Concern {concern_code: 'DARK_CIRCLES'})
SET c.appropriate_categories = ['크림', '세럼', '앰플', '에센스', '로션', '토너', '미스트', '올인원'];
MATCH (c:Concern {concern_code: 'SUNBURN'})
SET c.appropriate_categories = ['크림', '세럼', '앰플', '에센스', '로션', '토너', '미스트', '올인원'];
MATCH (c:Concern {concern_code: 'AGING_SIGNS'})
SET c.appropriate_categories = ['크림', '세럼', '앰플', '에센스', '로션', '토너', '미스트', '올인원'];
MATCH (c:Concern {concern_code: 'WRINKLES'})
SET c.appropriate_categories = ['크림', '세럼', '앰플', '에센스', '로션', '토너', '미스트', '올인원'];
MATCH (c:Concern {concern_code: 'LOSS_OF_ELASTICITY'})
SET c.appropriate_categories = ['크림', '세럼', '앰플', '에센스', '로션', '토너', '미스트', '올인원'];
MATCH (c:Concern {concern_code: 'SAGGING_SKIN'})
SET c.appropriate_categories = ['크림', '세럼', '앰플', '에센스', '로션', '토너', '미스트', '올인원'];
