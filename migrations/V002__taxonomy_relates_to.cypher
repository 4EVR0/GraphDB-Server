// GENERATED FILE — 직접 수정 금지.
// 원본: GraphRAG_Pipeline/db/seed/taxonomy.yaml
// 재생성: python GraphRAG_Pipeline/scripts/generate_taxonomy_artifacts.py

// concern 노드 보장 + RELATES_TO 전량 재구축 (rank = 우선순위, 0이 최우선)

MERGE (c:Concern {concern_code: 'ACNE'})
SET c.concern_name_en = 'Acne',
    c.concern_name_ko = '여드름',
    c.concern_group = 'acne';
MATCH (c:Concern {concern_code: 'ACNE'})
OPTIONAL MATCH ()-[r:RELATES_TO]->(c) DELETE r;
MATCH (e:Effect {effect_code: 'ANTI_INFLAMMATORY'}), (c:Concern {concern_code: 'ACNE'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 0;
MATCH (e:Effect {effect_code: 'SEBUM_REGULATION'}), (c:Concern {concern_code: 'ACNE'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 1;
MATCH (e:Effect {effect_code: 'KERATOLYTIC'}), (c:Concern {concern_code: 'ACNE'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 2;
MATCH (e:Effect {effect_code: 'COMEDOLYTIC'}), (c:Concern {concern_code: 'ACNE'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 3;
MATCH (e:Effect {effect_code: 'ANTIMICROBIAL'}), (c:Concern {concern_code: 'ACNE'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 4;

MERGE (c:Concern {concern_code: 'COMEDONES'})
SET c.concern_name_en = 'Comedones',
    c.concern_name_ko = '면포',
    c.concern_group = 'acne';
MATCH (c:Concern {concern_code: 'COMEDONES'})
OPTIONAL MATCH ()-[r:RELATES_TO]->(c) DELETE r;
MATCH (e:Effect {effect_code: 'KERATOLYTIC'}), (c:Concern {concern_code: 'COMEDONES'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 0;
MATCH (e:Effect {effect_code: 'COMEDOLYTIC'}), (c:Concern {concern_code: 'COMEDONES'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 1;
MATCH (e:Effect {effect_code: 'SEBUM_REGULATION'}), (c:Concern {concern_code: 'COMEDONES'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 2;

MERGE (c:Concern {concern_code: 'PORE_CONGESTION'})
SET c.concern_name_en = 'Pore congestion',
    c.concern_name_ko = '모공 막힘',
    c.concern_group = 'acne';
MATCH (c:Concern {concern_code: 'PORE_CONGESTION'})
OPTIONAL MATCH ()-[r:RELATES_TO]->(c) DELETE r;
MATCH (e:Effect {effect_code: 'KERATOLYTIC'}), (c:Concern {concern_code: 'PORE_CONGESTION'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 0;
MATCH (e:Effect {effect_code: 'COMEDOLYTIC'}), (c:Concern {concern_code: 'PORE_CONGESTION'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 1;
MATCH (e:Effect {effect_code: 'SEBUM_REGULATION'}), (c:Concern {concern_code: 'PORE_CONGESTION'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 2;

MERGE (c:Concern {concern_code: 'ENLARGED_PORES'})
SET c.concern_name_en = 'Enlarged pores',
    c.concern_name_ko = '모공 확대',
    c.concern_group = 'oil';
MATCH (c:Concern {concern_code: 'ENLARGED_PORES'})
OPTIONAL MATCH ()-[r:RELATES_TO]->(c) DELETE r;
MATCH (e:Effect {effect_code: 'SEBUM_REGULATION'}), (c:Concern {concern_code: 'ENLARGED_PORES'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 0;
MATCH (e:Effect {effect_code: 'KERATOLYTIC'}), (c:Concern {concern_code: 'ENLARGED_PORES'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 1;

MERGE (c:Concern {concern_code: 'OILY_SKIN'})
SET c.concern_name_en = 'Oily skin',
    c.concern_name_ko = '지성 피부',
    c.concern_group = 'oil';
MATCH (c:Concern {concern_code: 'OILY_SKIN'})
OPTIONAL MATCH ()-[r:RELATES_TO]->(c) DELETE r;
MATCH (e:Effect {effect_code: 'SEBUM_REGULATION'}), (c:Concern {concern_code: 'OILY_SKIN'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 0;
MATCH (e:Effect {effect_code: 'ANTI_INFLAMMATORY'}), (c:Concern {concern_code: 'OILY_SKIN'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 1;

MERGE (c:Concern {concern_code: 'SENSITIVE_SKIN'})
SET c.concern_name_en = 'Sensitive skin',
    c.concern_name_ko = '민감성 피부',
    c.concern_group = 'sensitivity';
MATCH (c:Concern {concern_code: 'SENSITIVE_SKIN'})
OPTIONAL MATCH ()-[r:RELATES_TO]->(c) DELETE r;
MATCH (e:Effect {effect_code: 'SOOTHING'}), (c:Concern {concern_code: 'SENSITIVE_SKIN'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 0;
MATCH (e:Effect {effect_code: 'ANTI_INFLAMMATORY'}), (c:Concern {concern_code: 'SENSITIVE_SKIN'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 1;
MATCH (e:Effect {effect_code: 'BARRIER_REPAIR'}), (c:Concern {concern_code: 'SENSITIVE_SKIN'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 2;
MATCH (e:Effect {effect_code: 'HYDRATING'}), (c:Concern {concern_code: 'SENSITIVE_SKIN'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 3;

MERGE (c:Concern {concern_code: 'REDNESS'})
SET c.concern_name_en = 'Redness',
    c.concern_name_ko = '붉은기',
    c.concern_group = 'sensitivity';
MATCH (c:Concern {concern_code: 'REDNESS'})
OPTIONAL MATCH ()-[r:RELATES_TO]->(c) DELETE r;
MATCH (e:Effect {effect_code: 'ANTI_INFLAMMATORY'}), (c:Concern {concern_code: 'REDNESS'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 0;
MATCH (e:Effect {effect_code: 'SOOTHING'}), (c:Concern {concern_code: 'REDNESS'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 1;

MERGE (c:Concern {concern_code: 'IRRITATED_SKIN'})
SET c.concern_name_en = 'Irritated skin',
    c.concern_name_ko = '자극 피부',
    c.concern_group = 'sensitivity';
MATCH (c:Concern {concern_code: 'IRRITATED_SKIN'})
OPTIONAL MATCH ()-[r:RELATES_TO]->(c) DELETE r;
MATCH (e:Effect {effect_code: 'ANTI_INFLAMMATORY'}), (c:Concern {concern_code: 'IRRITATED_SKIN'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 0;
MATCH (e:Effect {effect_code: 'SOOTHING'}), (c:Concern {concern_code: 'IRRITATED_SKIN'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 1;
MATCH (e:Effect {effect_code: 'BARRIER_REPAIR'}), (c:Concern {concern_code: 'IRRITATED_SKIN'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 2;

MERGE (c:Concern {concern_code: 'ATOPIC_PRONE'})
SET c.concern_name_en = 'Atopic-prone skin',
    c.concern_name_ko = '아토피 피부 경향',
    c.concern_group = 'sensitivity';
MATCH (c:Concern {concern_code: 'ATOPIC_PRONE'})
OPTIONAL MATCH ()-[r:RELATES_TO]->(c) DELETE r;
MATCH (e:Effect {effect_code: 'ANTI_INFLAMMATORY'}), (c:Concern {concern_code: 'ATOPIC_PRONE'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 0;
MATCH (e:Effect {effect_code: 'SOOTHING'}), (c:Concern {concern_code: 'ATOPIC_PRONE'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 1;
MATCH (e:Effect {effect_code: 'BARRIER_REPAIR'}), (c:Concern {concern_code: 'ATOPIC_PRONE'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 2;
MATCH (e:Effect {effect_code: 'HYDRATING'}), (c:Concern {concern_code: 'ATOPIC_PRONE'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 3;

MERGE (c:Concern {concern_code: 'ROSACEA_PRONE'})
SET c.concern_name_en = 'Rosacea-prone skin',
    c.concern_name_ko = '주사 피부 경향',
    c.concern_group = 'sensitivity';
MATCH (c:Concern {concern_code: 'ROSACEA_PRONE'})
OPTIONAL MATCH ()-[r:RELATES_TO]->(c) DELETE r;
MATCH (e:Effect {effect_code: 'ANTI_INFLAMMATORY'}), (c:Concern {concern_code: 'ROSACEA_PRONE'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 0;
MATCH (e:Effect {effect_code: 'SOOTHING'}), (c:Concern {concern_code: 'ROSACEA_PRONE'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 1;

MERGE (c:Concern {concern_code: 'DRY_SKIN'})
SET c.concern_name_en = 'Dry skin',
    c.concern_name_ko = '건성 피부',
    c.concern_group = 'dryness';
MATCH (c:Concern {concern_code: 'DRY_SKIN'})
OPTIONAL MATCH ()-[r:RELATES_TO]->(c) DELETE r;
MATCH (e:Effect {effect_code: 'HYDRATING'}), (c:Concern {concern_code: 'DRY_SKIN'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 0;
MATCH (e:Effect {effect_code: 'MOISTURE_RETENTION'}), (c:Concern {concern_code: 'DRY_SKIN'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 1;
MATCH (e:Effect {effect_code: 'BARRIER_REPAIR'}), (c:Concern {concern_code: 'DRY_SKIN'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 2;

MERGE (c:Concern {concern_code: 'DEHYDRATED_SKIN'})
SET c.concern_name_en = 'Dehydrated skin',
    c.concern_name_ko = '수분 부족 피부',
    c.concern_group = 'dryness';
MATCH (c:Concern {concern_code: 'DEHYDRATED_SKIN'})
OPTIONAL MATCH ()-[r:RELATES_TO]->(c) DELETE r;
MATCH (e:Effect {effect_code: 'HYDRATING'}), (c:Concern {concern_code: 'DEHYDRATED_SKIN'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 0;
MATCH (e:Effect {effect_code: 'MOISTURE_RETENTION'}), (c:Concern {concern_code: 'DEHYDRATED_SKIN'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 1;

MERGE (c:Concern {concern_code: 'FLAKY_SKIN'})
SET c.concern_name_en = 'Flaky skin',
    c.concern_name_ko = '각질',
    c.concern_group = 'dryness';
MATCH (c:Concern {concern_code: 'FLAKY_SKIN'})
OPTIONAL MATCH ()-[r:RELATES_TO]->(c) DELETE r;
MATCH (e:Effect {effect_code: 'HYDRATING'}), (c:Concern {concern_code: 'FLAKY_SKIN'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 0;
MATCH (e:Effect {effect_code: 'KERATOLYTIC'}), (c:Concern {concern_code: 'FLAKY_SKIN'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 1;
MATCH (e:Effect {effect_code: 'MOISTURE_RETENTION'}), (c:Concern {concern_code: 'FLAKY_SKIN'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 2;

MERGE (c:Concern {concern_code: 'ROUGH_TEXTURE'})
SET c.concern_name_en = 'Rough texture',
    c.concern_name_ko = '피부결 거침',
    c.concern_group = 'dryness';
MATCH (c:Concern {concern_code: 'ROUGH_TEXTURE'})
OPTIONAL MATCH ()-[r:RELATES_TO]->(c) DELETE r;
MATCH (e:Effect {effect_code: 'KERATOLYTIC'}), (c:Concern {concern_code: 'ROUGH_TEXTURE'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 0;
MATCH (e:Effect {effect_code: 'MOISTURE_RETENTION'}), (c:Concern {concern_code: 'ROUGH_TEXTURE'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 1;

MERGE (c:Concern {concern_code: 'BARRIER_DAMAGE'})
SET c.concern_name_en = 'Skin barrier damage',
    c.concern_name_ko = '피부 장벽 손상',
    c.concern_group = 'barrier';
MATCH (c:Concern {concern_code: 'BARRIER_DAMAGE'})
OPTIONAL MATCH ()-[r:RELATES_TO]->(c) DELETE r;
MATCH (e:Effect {effect_code: 'BARRIER_REPAIR'}), (c:Concern {concern_code: 'BARRIER_DAMAGE'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 0;
MATCH (e:Effect {effect_code: 'HYDRATING'}), (c:Concern {concern_code: 'BARRIER_DAMAGE'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 1;
MATCH (e:Effect {effect_code: 'MOISTURE_RETENTION'}), (c:Concern {concern_code: 'BARRIER_DAMAGE'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 2;
MATCH (e:Effect {effect_code: 'SOOTHING'}), (c:Concern {concern_code: 'BARRIER_DAMAGE'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 3;

MERGE (c:Concern {concern_code: 'HYPERPIGMENTATION'})
SET c.concern_name_en = 'Hyperpigmentation',
    c.concern_name_ko = '색소침착',
    c.concern_group = 'pigmentation';
MATCH (c:Concern {concern_code: 'HYPERPIGMENTATION'})
OPTIONAL MATCH ()-[r:RELATES_TO]->(c) DELETE r;
MATCH (e:Effect {effect_code: 'DEPIGMENTING'}), (c:Concern {concern_code: 'HYPERPIGMENTATION'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 0;
MATCH (e:Effect {effect_code: 'BRIGHTENING'}), (c:Concern {concern_code: 'HYPERPIGMENTATION'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 1;
MATCH (e:Effect {effect_code: 'ANTI_INFLAMMATORY'}), (c:Concern {concern_code: 'HYPERPIGMENTATION'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 2;

MERGE (c:Concern {concern_code: 'DULLNESS'})
SET c.concern_name_en = 'Dullness',
    c.concern_name_ko = '피부 톤 저하',
    c.concern_group = 'pigmentation';
MATCH (c:Concern {concern_code: 'DULLNESS'})
OPTIONAL MATCH ()-[r:RELATES_TO]->(c) DELETE r;
MATCH (e:Effect {effect_code: 'BRIGHTENING'}), (c:Concern {concern_code: 'DULLNESS'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 0;
MATCH (e:Effect {effect_code: 'DEPIGMENTING'}), (c:Concern {concern_code: 'DULLNESS'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 1;
MATCH (e:Effect {effect_code: 'KERATOLYTIC'}), (c:Concern {concern_code: 'DULLNESS'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 2;
MATCH (e:Effect {effect_code: 'ANTIOXIDANT'}), (c:Concern {concern_code: 'DULLNESS'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 3;

MERGE (c:Concern {concern_code: 'UNEVEN_SKIN_TONE'})
SET c.concern_name_en = 'Uneven skin tone',
    c.concern_name_ko = '피부 톤 불균일',
    c.concern_group = 'pigmentation';
MATCH (c:Concern {concern_code: 'UNEVEN_SKIN_TONE'})
OPTIONAL MATCH ()-[r:RELATES_TO]->(c) DELETE r;
MATCH (e:Effect {effect_code: 'BRIGHTENING'}), (c:Concern {concern_code: 'UNEVEN_SKIN_TONE'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 0;
MATCH (e:Effect {effect_code: 'DEPIGMENTING'}), (c:Concern {concern_code: 'UNEVEN_SKIN_TONE'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 1;

MERGE (c:Concern {concern_code: 'BLEMISHES'})
SET c.concern_name_en = 'Blemishes',
    c.concern_name_ko = '잡티',
    c.concern_group = 'pigmentation';
MATCH (c:Concern {concern_code: 'BLEMISHES'})
OPTIONAL MATCH ()-[r:RELATES_TO]->(c) DELETE r;
MATCH (e:Effect {effect_code: 'DEPIGMENTING'}), (c:Concern {concern_code: 'BLEMISHES'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 0;
MATCH (e:Effect {effect_code: 'BRIGHTENING'}), (c:Concern {concern_code: 'BLEMISHES'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 1;
MATCH (e:Effect {effect_code: 'WOUND_HEALING'}), (c:Concern {concern_code: 'BLEMISHES'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 2;

MERGE (c:Concern {concern_code: 'POST_ACNE_MARKS'})
SET c.concern_name_en = 'Post-acne marks',
    c.concern_name_ko = '여드름 자국',
    c.concern_group = 'pigmentation';
MATCH (c:Concern {concern_code: 'POST_ACNE_MARKS'})
OPTIONAL MATCH ()-[r:RELATES_TO]->(c) DELETE r;
MATCH (e:Effect {effect_code: 'DEPIGMENTING'}), (c:Concern {concern_code: 'POST_ACNE_MARKS'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 0;
MATCH (e:Effect {effect_code: 'BRIGHTENING'}), (c:Concern {concern_code: 'POST_ACNE_MARKS'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 1;
MATCH (e:Effect {effect_code: 'WOUND_HEALING'}), (c:Concern {concern_code: 'POST_ACNE_MARKS'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 2;

MERGE (c:Concern {concern_code: 'DARK_CIRCLES'})
SET c.concern_name_en = 'Dark circles',
    c.concern_name_ko = '다크서클',
    c.concern_group = 'pigmentation';
MATCH (c:Concern {concern_code: 'DARK_CIRCLES'})
OPTIONAL MATCH ()-[r:RELATES_TO]->(c) DELETE r;
MATCH (e:Effect {effect_code: 'DEPIGMENTING'}), (c:Concern {concern_code: 'DARK_CIRCLES'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 0;
MATCH (e:Effect {effect_code: 'BRIGHTENING'}), (c:Concern {concern_code: 'DARK_CIRCLES'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 1;

MERGE (c:Concern {concern_code: 'SUNBURN'})
SET c.concern_name_en = 'Sun damage',
    c.concern_name_ko = '자외선 손상',
    c.concern_group = 'protection';
MATCH (c:Concern {concern_code: 'SUNBURN'})
OPTIONAL MATCH ()-[r:RELATES_TO]->(c) DELETE r;
MATCH (e:Effect {effect_code: 'PHOTOPROTECTIVE'}), (c:Concern {concern_code: 'SUNBURN'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 0;
MATCH (e:Effect {effect_code: 'ANTIOXIDANT'}), (c:Concern {concern_code: 'SUNBURN'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 1;
MATCH (e:Effect {effect_code: 'SOOTHING'}), (c:Concern {concern_code: 'SUNBURN'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 2;

MERGE (c:Concern {concern_code: 'AGING_SIGNS'})
SET c.concern_name_en = 'Aging signs',
    c.concern_name_ko = '노화 징후',
    c.concern_group = 'aging';
MATCH (c:Concern {concern_code: 'AGING_SIGNS'})
OPTIONAL MATCH ()-[r:RELATES_TO]->(c) DELETE r;
MATCH (e:Effect {effect_code: 'ANTI_AGING'}), (c:Concern {concern_code: 'AGING_SIGNS'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 0;
MATCH (e:Effect {effect_code: 'ANTIOXIDANT'}), (c:Concern {concern_code: 'AGING_SIGNS'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 1;

MERGE (c:Concern {concern_code: 'WRINKLES'})
SET c.concern_name_en = 'Wrinkles',
    c.concern_name_ko = '주름',
    c.concern_group = 'aging';
MATCH (c:Concern {concern_code: 'WRINKLES'})
OPTIONAL MATCH ()-[r:RELATES_TO]->(c) DELETE r;
MATCH (e:Effect {effect_code: 'ANTI_AGING'}), (c:Concern {concern_code: 'WRINKLES'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 0;
MATCH (e:Effect {effect_code: 'HYDRATING'}), (c:Concern {concern_code: 'WRINKLES'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 1;

MERGE (c:Concern {concern_code: 'LOSS_OF_ELASTICITY'})
SET c.concern_name_en = 'Loss of elasticity',
    c.concern_name_ko = '탄력 저하',
    c.concern_group = 'aging';
MATCH (c:Concern {concern_code: 'LOSS_OF_ELASTICITY'})
OPTIONAL MATCH ()-[r:RELATES_TO]->(c) DELETE r;
MATCH (e:Effect {effect_code: 'ANTI_AGING'}), (c:Concern {concern_code: 'LOSS_OF_ELASTICITY'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 0;
MATCH (e:Effect {effect_code: 'MOISTURE_RETENTION'}), (c:Concern {concern_code: 'LOSS_OF_ELASTICITY'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 1;

MERGE (c:Concern {concern_code: 'SAGGING_SKIN'})
SET c.concern_name_en = 'Sagging skin',
    c.concern_name_ko = '피부 처짐',
    c.concern_group = 'aging';
MATCH (c:Concern {concern_code: 'SAGGING_SKIN'})
OPTIONAL MATCH ()-[r:RELATES_TO]->(c) DELETE r;
MATCH (e:Effect {effect_code: 'ANTI_AGING'}), (c:Concern {concern_code: 'SAGGING_SKIN'})
MERGE (e)-[r:RELATES_TO]->(c) SET r.rank = 0;
