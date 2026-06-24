"""
"기존에 있던 모델"과의 비교 베이스라인: Oliveyoung_Pipeline/gold_pipeline에 이미 구축된
gold_ingredient_frequency Iceberg 테이블 (카테고리별 성분 사용빈도 Top-N).

한계점 (보고서에도 명시): 이 테이블은 concern(피부 고민)을 입력으로 받지 않는다.
카테고리는 상품 분류(세럼/토너/크림 등)이지 피부 고민이 아니라서, concern별로 다른 추천을
만들 수 없다. 따라서 "TOTAL" 카테고리의 성분 인기도 Top-N을 모든 concern에 대해 동일하게
적용하는 전역 인기도 베이스라인으로 비교한다 (concern-aware가 아니라는 점이 핵심 결론).
"""

import pandas as pd
from pyiceberg.catalog.glue import GlueCatalog

from gold_labels import PRODUCTION_CONCERN_EFFECT_MAP, fetch_all_affects, get_driver

GLUE_CATALOG_KWARGS = {
    "s3.region": "ap-northeast-2",
    "uri": "https://glue.ap-northeast-2.amazonaws.com",
    "warehouse": "s3://oliveyoung-crawl-data/olive_young_gold/",
}


def fetch_frequency_baseline(top_n: int = 20) -> list[str]:
    """TOTAL 카테고리 성분 사용빈도 Top-N (한글명) 반환."""
    catalog = GlueCatalog("oliveyoung_catalog", **GLUE_CATALOG_KWARGS)
    table = catalog.load_table("oliveyoung_db.gold_ingredient_frequency")
    df = table.scan().to_arrow().to_pandas()

    # Iceberg append 테이블에 과거 배치 row가 섞여 있어 최신 batch_job만 사용
    latest_batch = df["batch_job"].dropna().max()
    df = df[df["batch_job"] == latest_batch]

    total = df[df["category_id"] == "TOTAL"].drop_duplicates("ingredient_name")
    total = total.sort_values("rank").head(top_n)
    return total["ingredient_name"].tolist()


def map_kor_names_to_inci(driver, kor_names: list[str]) -> dict[str, str]:
    """그래프의 kor_name -> inci_name 매핑 (frequency 테이블은 한글명만 가지고 있음)."""
    with driver.session() as session:
        rows = session.run(
            "MATCH (i:Ingredient) WHERE i.kor_name IN $names "
            "RETURN i.kor_name AS kor_name, i.inci_name AS inci_name",
            names=kor_names,
        ).data()
    return {r["kor_name"]: r["inci_name"] for r in rows}


def evaluate_baseline(top_n: int = 20) -> list[dict]:
    driver = get_driver()
    try:
        affects_df = fetch_all_affects(driver)
        freq_kor_names = fetch_frequency_baseline(top_n=top_n)
        kor_to_inci = map_kor_names_to_inci(driver, freq_kor_names)
        baseline_inci_names = set(kor_to_inci.values())

        matched_in_graph = len(baseline_inci_names)
        print(f"빈도 Top-{top_n} 중 그래프에서 INCI 매칭된 성분 수: {matched_in_graph}/{len(freq_kor_names)}")
        print(f"  매칭된 성분: {sorted(baseline_inci_names)}")

        results = []
        for concern, effects in PRODUCTION_CONCERN_EFFECT_MAP.items():
            candidates = affects_df[affects_df["effect_code"].isin(effects)]
            gold_names = set(candidates[candidates["is_gold"]]["inci_name"])

            overlap = baseline_inci_names & gold_names
            recall = len(overlap) / len(gold_names) if gold_names else None
            precision = len(overlap) / len(baseline_inci_names) if baseline_inci_names else None

            results.append({
                "concern": concern,
                "gold_count": len(gold_names),
                "baseline_overlap": len(overlap),
                "recall": recall,
                "precision": precision,
            })
        return results
    finally:
        driver.close()


if __name__ == "__main__":
    results = evaluate_baseline(top_n=20)
    print("\n=== 빈도 베이스라인(전역 인기도 Top-20) vs concern별 gold 성분 ===")
    print(f"{'concern':20s} {'gold':>5s} {'overlap':>8s} {'recall':>7s} {'precision':>9s}")
    for r in results:
        rc = f"{r['recall']:.2f}" if r["recall"] is not None else "-"
        pr = f"{r['precision']:.2f}" if r["precision"] is not None else "-"
        print(f"{r['concern']:20s} {r['gold_count']:5d} {r['baseline_overlap']:8d} {rc:>7s} {pr:>9s}")

    avg_recall = pd.Series([r["recall"] for r in results if r["recall"] is not None]).mean()
    print(f"\n평균 recall (전역 인기도 베이스라인): {avg_recall:.3f}")
