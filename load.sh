#!/bin/bash
set -euo pipefail

CSV_DIR="/home/graphdb/csv"
IMPORT_DIR="/home/graphdb/neo4j/import"

# ── S3 베이스 경로 (배치/버전은 아래에서 결정) ──────────────────────────────
S3_BUCKET="s3://oliveyoung-crawl-data"
S3_GOLD_BASE="$S3_BUCKET/graph_gold_csvs"
S3_PRODUCT_BASE="$S3_BUCKET/gold/neo4j/oliveyoung/nodes/Product"
S3_CONTAINS_BASE="$S3_BUCKET/gold/neo4j/oliveyoung/rels/CONTAINS"

# ── 배치/버전 지정 (인자 > 환경변수 > 최신 자동 선택) ────────────────────────
# 사용법:
#   bash load.sh                                  # 모두 최신 자동 선택
#   bash load.sh 20260511_174455                  # 특정 gold 배치
#   bash load.sh 20260511_174455 <product> <contains>
#   BATCH_JOB=... PRODUCT_VERSION=... CONTAINS_VERSION=... bash load.sh
BATCH_JOB="${1:-${BATCH_JOB:-}}"
PRODUCT_VERSION="${2:-${PRODUCT_VERSION:-}}"
CONTAINS_VERSION="${3:-${CONTAINS_VERSION:-}}"

# 주어진 S3 prefix 아래에서 pattern으로 시작하는 하위 prefix 중 최신(이름 정렬 마지막)을 반환
latest_prefix() {
  local base="$1" pattern="$2"
  aws s3 ls "$base/" | awk '{print $2}' | grep -E "^${pattern}" | sed 's#/$##' | sort | tail -n1
}

echo "=== [0/7] 적재 대상 배치 결정 ==="

if [ -z "$BATCH_JOB" ]; then
  BATCH_JOB=$(latest_prefix "$S3_GOLD_BASE" "batch_job=")
  [ -n "$BATCH_JOB" ] || { echo "ERROR: $S3_GOLD_BASE 아래에서 batch_job=* 를 찾지 못했습니다"; exit 1; }
  echo "graph_gold 배치: $BATCH_JOB (최신 자동 선택)"
else
  case "$BATCH_JOB" in batch_job=*) ;; *) BATCH_JOB="batch_job=$BATCH_JOB";; esac
  echo "graph_gold 배치: $BATCH_JOB (지정)"
fi
S3_BATCH="$S3_GOLD_BASE/$BATCH_JOB"

if [ -z "$PRODUCT_VERSION" ]; then
  PRODUCT_VERSION=$(latest_prefix "$S3_PRODUCT_BASE" "oliveyoung_neo4j_")
  [ -n "$PRODUCT_VERSION" ] || { echo "ERROR: $S3_PRODUCT_BASE 아래에서 oliveyoung_neo4j_* 를 찾지 못했습니다"; exit 1; }
  echo "product 버전:    $PRODUCT_VERSION (최신 자동 선택)"
else
  echo "product 버전:    $PRODUCT_VERSION (지정)"
fi
S3_PRODUCT_DIR="$S3_PRODUCT_BASE/$PRODUCT_VERSION"

if [ -z "$CONTAINS_VERSION" ]; then
  CONTAINS_VERSION=$(latest_prefix "$S3_CONTAINS_BASE" "oliveyoung_neo4j_")
  [ -n "$CONTAINS_VERSION" ] || { echo "ERROR: $S3_CONTAINS_BASE 아래에서 oliveyoung_neo4j_* 를 찾지 못했습니다"; exit 1; }
  echo "contains 버전:   $CONTAINS_VERSION (최신 자동 선택)"
else
  echo "contains 버전:   $CONTAINS_VERSION (지정)"
fi
S3_CONTAINS_DIR="$S3_CONTAINS_BASE/$CONTAINS_VERSION"

echo ""
echo "  S3_BATCH=$S3_BATCH"
echo "  S3_PRODUCT_DIR=$S3_PRODUCT_DIR"
echo "  S3_CONTAINS_DIR=$S3_CONTAINS_DIR"
echo ""

echo "=== [1/7] S3에서 CSV 다운로드 ==="

# batch 경로에서 ingredient, effect, concern, affects, relates_to 받기
# product, contains는 별도 경로에서 받으므로 제외
aws s3 sync "$S3_BATCH/nodes/" "$CSV_DIR/nodes/" \
  --exclude "product.csv"
aws s3 sync "$S3_BATCH/edges/" "$CSV_DIR/edges/" \
  --exclude "contains.csv"

# product.csv (별도 경로, S3의 header.csv + part-00000.csv 결합)
echo "product.csv 다운로드..."
aws s3 cp "$S3_PRODUCT_DIR/header.csv" /tmp/product_header.csv
aws s3 cp "$S3_PRODUCT_DIR/part-00000.csv" /tmp/product_raw.csv
printf '%s\n' "$(cat /tmp/product_header.csv)" | cat - /tmp/product_raw.csv > "$CSV_DIR/nodes/product.csv"

# contains.csv (별도 경로, S3의 header.csv + part-00000.csv 결합)
echo "contains.csv 다운로드..."
aws s3 cp "$S3_CONTAINS_DIR/header.csv" /tmp/contains_header.csv
aws s3 cp "$S3_CONTAINS_DIR/part-00000.csv" /tmp/contains_raw.csv
printf '%s\n' "$(cat /tmp/contains_header.csv)" | cat - /tmp/contains_raw.csv > "$CSV_DIR/edges/contains.csv"

echo "다운로드 완료:"
find "$CSV_DIR" -name "*.csv" | sort

echo ""
echo "=== [2/7] ID 검증 ==="
python3 /home/graphdb/validate.py /home/graphdb/csv
echo ""

echo "=== [3/7] 적재 대상 카운트 (헤더 제외) ==="
for f in "$CSV_DIR"/nodes/*.csv; do
  [ -e "$f" ] || continue
  n=$(($(wc -l < "$f") - 1))
  printf "  node  %-22s %10d\n" "$(basename "$f")" "$n"
done
for f in "$CSV_DIR"/edges/*.csv; do
  [ -e "$f" ] || continue
  n=$(($(wc -l < "$f") - 1))
  printf "  edge  %-22s %10d\n" "$(basename "$f")" "$n"
done
echo ""

echo "=== [4/7] import 디렉토리로 복사 ==="
sudo chown -R jiwoo:jiwoo "$IMPORT_DIR"
cp -r "$CSV_DIR"/* "$IMPORT_DIR/"
echo "복사 완료"

echo ""
echo "=== [5/7] neo4j-admin bulk import ==="
if docker ps -q -f name=neo4j | grep -q .; then
  echo "Neo4j 컨테이너 중지 중..."
  docker stop neo4j
fi

# RELATES_TO(concern↔effect taxonomy)는 벌크 임포트에서 제외 —
# migrations/V002가 taxonomy.yaml 기준으로 전량 재구축한다 (단일 소스).
docker run --rm \
  -v /home/graphdb/neo4j/data:/data \
  -v /home/graphdb/neo4j/import:/var/lib/neo4j/import \
  neo4j:5.26 \
  neo4j-admin database import full \
    --nodes=Product=/var/lib/neo4j/import/nodes/product.csv \
    --nodes=Ingredient=/var/lib/neo4j/import/nodes/ingredient.csv \
    --nodes=Effect=/var/lib/neo4j/import/nodes/effect.csv \
    --nodes=Concern=/var/lib/neo4j/import/nodes/concern.csv \
    --relationships=CONTAINS=/var/lib/neo4j/import/edges/contains.csv \
    --relationships=AFFECTS=/var/lib/neo4j/import/edges/affects.csv \
    --overwrite-destination \
    neo4j

echo ""
echo "=== [6/7] Neo4j 재시작 ==="
docker compose -f /home/graphdb/docker-compose.yml up -d

echo ""
echo "=== [7/7] 스키마 마이그레이션 (constraints/인덱스/taxonomy) ==="
# migrate.py는 python3 + neo4j 드라이버 필요 (pip install -r requirements.txt).
# NEO4J_PASSWORD 등 접속 정보는 docker-compose와 같은 .env에서 가져온다.
set -a
. /home/graphdb/.env
set +a
python3 /home/graphdb/migrate.py --wait 180 --verify

echo ""
echo "브라우저: http://localhost:7474"
echo "인증 정보는 서버의 .env에서 관리합니다. 로그에 비밀번호를 출력하지 않습니다."
