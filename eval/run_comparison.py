"""
gold_labels / graphrag_ranking_eval / baseline_frequency_eval 결과를 모아
eval/RESULTS.md 보고서를 만든다.
"""

from pathlib import Path

import pandas as pd

from baseline_frequency_eval import evaluate_baseline
from gold_labels import compare_concern_effect_sources, get_driver
from graphrag_ranking_eval import run_all as run_graphrag_eval

RESULTS_PATH = Path(__file__).parent / "RESULTS.md"


def fmt(value, digits=2):
    return f"{value:.{digits}f}" if value is not None else "-"


def build_report() -> str:
    driver = get_driver()
    try:
        source_findings = compare_concern_effect_sources(driver)
    finally:
        driver.close()

    graphrag_results = run_graphrag_eval()
    baseline_results = evaluate_baseline(top_n=20)
    baseline_by_concern = {r["concern"]: r for r in baseline_results}

    no_relates_to = [f["concern"] for f in source_findings if f["graph_has_no_relates_to"]]
    mismatched = [f["concern"] for f in source_findings
                  if not f["graph_has_no_relates_to"] and not f["sets_match"]]

    empty_ingredient = [r["concern"] for r in graphrag_results if r["ingredient_is_empty"]]
    empty_product = [r["concern"] for r in graphrag_results if r["product_is_empty"]]
    zero_gold = [r["concern"] for r in graphrag_results if r["candidate_gold"] == 0]
    has_duplicates = [r["concern"] for r in graphrag_results if r["ingredient_distinct"] < r["ingredient_returned"]]

    lines = []
    lines.append("# 문제 3 조사 결과: 추천 결과 경로 탐색·랭킹 검증\n")

    lines.append("## 1. 그래프 RELATES_TO vs 운영 코드 CONCERN_EFFECT_MAP\n")
    lines.append(
        "운영 코드(4evr0-server)는 `(Concern)-[:RELATES_TO]->(Effect)` 그래프 관계를 쓰지 않고, "
        "`taxonomy_normalization_service.CONCERN_EFFECT_MAP`(하드코딩 dict)으로 concern→effect를 "
        "직접 매핑한다. 그래프 자체의 RELATES_TO 관계와 비교한 결과:\n"
    )
    lines.append(f"- 그래프에 RELATES_TO가 **전혀 없는** Concern: {len(no_relates_to)}/15 — `{', '.join(no_relates_to)}`")
    lines.append(
        "  → README에 문서화된 `(Effect)-[:RELATES_TO]->(Concern)` 경로 자체로 추천을 시도하면 "
        "이 8개 고민은 0건이 나온다. 실서비스는 이 경로를 쓰지 않아 영향이 없지만, "
        "그래프 데이터가 자기 문서화된 스키마와 불일치하는 상태."
    )
    if mismatched:
        lines.append(f"- 그래프와 운영 코드 매핑이 **다른** Concern: `{', '.join(mismatched)}`")
        for f in source_findings:
            if f["concern"] in mismatched:
                lines.append(
                    f"  - `{f['concern']}`: 그래프=`{f['graph_relates_to_effects']}` "
                    f"vs 운영코드=`{f['production_map_effects']}`"
                )
    lines.append("")

    lines.append("## 2. 경로 탐색 커버리지 (실제 운영 경로, 26개 concern 전체)\n")
    lines.append(f"- 성분 결과 0건 concern: **{len(empty_ingredient)}/26**")
    lines.append(f"- 제품 결과 0건 concern: **{len(empty_product)}/26**")
    lines.append(f"- 논문 근거(pubmed_evidence) 성분이 그래프에 0개인 concern: **{', '.join(zero_gold) if zero_gold else '없음'}**")
    if zero_gold:
        lines.append(
            "  → 경로 탐색 자체는 결과를 내놓지만(아래 표의 `ing`/`prod` 열 참고), "
            "전부 약한 근거(`cosing_function`)뿐이라 \"정답\"이라 부를 근거가 약함."
        )
    lines.append(
        f"- top-20 안에 **같은 성분이 중복으로 여러 줄을 차지하는** concern: "
        f"**{len(has_duplicates)}/26** — `{', '.join(has_duplicates)}`"
    )
    lines.append(
        "  → 운영 쿼리의 `RETURN DISTINCT`가 성분 이름이 아니라 (이름, effect, evidence_type, ...) "
        "행 전체를 기준으로 동작해서, 한 성분이 두 개 이상의 effect로 매치되면 LIMIT 20 중 여러 슬롯을 "
        "그 성분 하나가 차지한다. 그만큼 사용자가 실제로 보는 **distinct 성분 수는 20보다 적어진다** "
        "(`ing` vs `distinct` 열 비교)."
    )
    lines.append("")

    lines.append(
        "| concern | 후보(전체) | 후보중 gold | 성분 반환(행) | distinct 성분 | 제품 반환 | "
        "Precision@20 | Recall@20 | NDCG@20 | 빈도baseline recall |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in graphrag_results:
        b = baseline_by_concern.get(r["concern"], {})
        dup_mark = " **↑중복**" if r["ingredient_distinct"] < r["ingredient_returned"] else ""
        lines.append(
            f"| {r['concern']} | {r['candidate_total']} | {r['candidate_gold']} | "
            f"{r['ingredient_returned']} | {r['ingredient_distinct']}{dup_mark} | {r['product_returned']} | "
            f"{fmt(r['precision_at_k'])} | {fmt(r['recall_at_k'])} | {fmt(r['ndcg_at_k'])} | "
            f"{fmt(b.get('recall'))} |"
        )
    lines.append("")

    avg_precision = pd.Series([r["precision_at_k"] for r in graphrag_results if r["precision_at_k"] is not None]).mean()
    avg_recall = pd.Series([r["recall_at_k"] for r in graphrag_results if r["recall_at_k"] is not None]).mean()
    avg_ndcg = pd.Series([r["ndcg_at_k"] for r in graphrag_results if r["ndcg_at_k"] is not None]).mean()
    avg_baseline_recall = pd.Series([b["recall"] for b in baseline_results if b["recall"] is not None]).mean()

    lines.append("## 3. 요약 (GraphRAG 경로 탐색 vs 기존 빈도 베이스라인)\n")
    lines.append(f"- GraphRAG 평균 Precision@20 (LIMIT 안에 진짜 근거 있는 성분 비율): **{avg_precision:.2f}**")
    lines.append(f"- GraphRAG 평균 Recall@20 (전체 근거 있는 성분 중 LIMIT 안에 들어온 비율): **{avg_recall:.2f}**")
    lines.append(f"- GraphRAG 평균 NDCG@20 (ORDER BY가 근거 있는 성분을 앞에 배치하는 정도): **{avg_ndcg:.2f}**")
    lines.append(f"- 기존 빈도 베이스라인(`gold_ingredient_frequency`, concern 무관 전역 인기도) 평균 Recall: **{avg_baseline_recall:.3f}**")
    lines.append(
        "\n해석: ORDER BY 로직 자체(NDCG≈1.0)는 올바르게 동작한다 — 근거 있는 성분을 앞에 배치하는 데는 "
        "문제가 없다. 다만 ACNE/COMEDONES/PORE_CONGESTION/ENLARGED_PORES/OILY_SKIN/ROUGH_TEXTURE처럼 "
        "그래프에 논문 근거 성분이 원래 적은(gold 2~5개) concern은 LIMIT 20 슬롯 대부분이 약한 근거로 "
        "채워진다(Precision@20 0.10~0.25) — 이는 랭킹 버그가 아니라 데이터 자체의 근거 부족.\n\n"
        "기존의 concern-무관 인기도 베이스라인은 평균 Recall이 2.6%로, 그래프 기반 경로 탐색이 "
        "실제로 \"의미적으로 맞는\" 후보를 찾아내는 데 훨씬 효과적임을 수치로 보여준다 "
        "(다만 이 비교는 같은 그래프의 evidence_type/graph_score를 정답 기준으로 쓰기 때문에, "
        "그래프 데이터 자체가 잘못된 경우는 잡아내지 못한다 — §1의 RELATES_TO 불일치가 그런 사례)."
    )
    lines.append("")

    lines.append("## 4. 발견된 문제 정리 (4evr0-server에 수정 권고)\n")
    lines.append(
        "1. **POST_ACNE_MARKS 매핑 불일치**: `CONCERN_EFFECT_MAP`이 그래프의 RELATES_TO와 다른 "
        "effect(`WOUND_HEALING`)를 쓰고 있음 — 어느 쪽이 맞는지 도메인 검토 필요."
    )
    lines.append(
        "2. **그래프 RELATES_TO 8개 Concern 누락**: 실서비스 영향은 없지만, 그래프가 README에 문서화된 "
        "스키마와 불일치 — 데이터 정합성 문제로 별도 정리 필요."
    )
    lines.append(
        f"3. **top-20 중복 성분으로 인한 다양성 손실**: {len(has_duplicates)}/26 concern에서 발생. "
        "`query_ingredients_by_effects`의 `RETURN DISTINCT`를 성분 이름 기준으로 한 번 더 dedup하거나 "
        "(예: `WITH i, collect(...) ... `), Cypher 단계에서 성분당 가장 강한 근거 1건만 남기도록 "
        "수정하면 동일한 LIMIT 20으로 더 많은 distinct 성분을 보여줄 수 있음."
    )
    lines.append(
        "4. **DULLNESS 근거 부족**: 그래프에 pubmed_evidence 성분이 0개 — 데이터 보강(논문 근거 수집) "
        "대상으로 우선순위 검토."
    )
    lines.append("")

    lines.append("## 5. 이번에 다루지 않은 것\n")
    lines.append(
        "- **4evr0-server 코드 수정**: 위 발견(특히 POST_ACNE_MARKS 매핑 불일치, 그래프 RELATES_TO 누락)에 대한 "
        "수정은 별도 저장소(`4EVR0-Server`)에서 진행해야 함 — 이번 평가는 읽기 전용 진단."
    )
    lines.append(
        "- **RAG(벡터 검색) 베이스라인**: 생략. 이유는 평가 방법론상 `graph_score`/`evidence_type`을 "
        "정답 기준으로 쓰는 한, 구조화된 근거 신호가 없는 순수 벡터 유사도 검색은 애초에 이 정답 기준과 "
        "정합성이 낮게 나올 수밖에 없어(같은 잣대로 재면 불리), RAG 자체의 한계가 아니라 평가 설계의 "
        "편향처럼 보일 위험이 있음. 별도의 (텍스트 기반) 정답 기준을 마련한 뒤 재검토 필요."
    )

    return "\n".join(lines)


if __name__ == "__main__":
    report = build_report()
    RESULTS_PATH.write_text(report)
    print(f"작성 완료: {RESULTS_PATH}")
    print("\n" + "=" * 60)
    print(report)
