#!/usr/bin/env python3
"""
노드 CSV의 :ID() 값과 엣지 CSV의 :START_ID / :END_ID 값이 일치하는지 검증
"""

import csv
import sys
from pathlib import Path

CSV_DIR = Path("/home/graphdb/csv")

# 노드 CSV → (파일, ID 컬럼, 라벨)
NODE_FILES = {
    "Product":    (CSV_DIR / "nodes/product.csv",    "product_id:ID(Product)"),
    "Ingredient": (CSV_DIR / "nodes/ingredient.csv", "ingredient_id:ID(Ingredient)"),
    "Effect":     (CSV_DIR / "nodes/effect.csv",     "effect_code:ID(Effect)"),
    "Concern":    (CSV_DIR / "nodes/concern.csv",    "concern_code:ID(Concern)"),
}

# 엣지 CSV → (파일, START 라벨, END 라벨)
EDGE_FILES = {
    "CONTAINS":   (CSV_DIR / "edges/contains.csv",   "Product",    "Ingredient"),
    "AFFECTS":    (CSV_DIR / "edges/affects.csv",     "Ingredient", "Effect"),
    "RELATES_TO": (CSV_DIR / "edges/relates_to.csv", "Effect",     "Concern"),
}


def load_ids(filepath, id_col):
    ids = set()
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if id_col not in reader.fieldnames:
            print(f"  [ERROR] '{id_col}' 컬럼 없음 in {filepath.name}")
            print(f"          실제 컬럼: {reader.fieldnames}")
            sys.exit(1)
        for row in reader:
            ids.add(row[id_col].strip())
    return ids


def load_edge_ids(filepath):
    starts, ends = [], []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        start_col = ":START_ID"
        end_col   = ":END_ID"
        # 괄호 포함 형식도 허용: :START_ID(Product) 등
        for col in reader.fieldnames:
            if col.startswith(":START_ID"):
                start_col = col
            if col.startswith(":END_ID"):
                end_col = col
        for row in reader:
            starts.append(row[start_col].strip())
            ends.append(row[end_col].strip())
    return starts, ends


def main():
    errors = 0

    # 노드 ID 로드
    node_ids = {}
    for label, (path, id_col) in NODE_FILES.items():
        if not path.exists():
            print(f"[SKIP] {path} 없음 (S3 다운로드 후 실행하세요)")
            continue
        ids = load_ids(path, id_col)
        node_ids[label] = ids
        print(f"[OK] {label}: {len(ids)}개 ID 로드 ({path.name})")

    if not node_ids:
        print("\nCSV 파일이 없습니다. S3에서 먼저 다운로드하세요.")
        print("  cd /home/graphdb && ./load.sh  (또는 aws s3 sync 먼저)")
        sys.exit(0)

    print()

    # 엣지 검증
    for rel, (path, start_label, end_label) in EDGE_FILES.items():
        if not path.exists():
            print(f"[SKIP] {path} 없음")
            continue

        if start_label not in node_ids or end_label not in node_ids:
            print(f"[SKIP] {rel}: 노드 CSV 미로드")
            continue

        starts, ends = load_edge_ids(path)
        missing_starts = [v for v in starts if v not in node_ids[start_label]]
        missing_ends   = [v for v in ends   if v not in node_ids[end_label]]

        if not missing_starts and not missing_ends:
            print(f"[OK] {rel}: {len(starts)}개 관계 — ID 전부 일치")
        else:
            errors += 1
            print(f"[FAIL] {rel}: ID 불일치 발견!")
            if missing_starts:
                print(f"  START_ID({start_label}) 미매칭 {len(missing_starts)}개: {missing_starts[:5]}")
            if missing_ends:
                print(f"  END_ID({end_label}) 미매칭 {len(missing_ends)}개: {missing_ends[:5]}")

    print()
    if errors == 0:
        print("모든 ID 매칭 OK — import 진행해도 됩니다.")
    else:
        print(f"오류 {errors}개 — 위 ID 값을 CSV에서 수정 후 다시 실행하세요.")
        sys.exit(1)


if __name__ == "__main__":
    main()
