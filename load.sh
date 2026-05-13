#!/bin/bash
set -e

CSV_DIR="/home/graphdb/csv"
IMPORT_DIR="/home/graphdb/neo4j/import"

# S3 경로 (파일별로 따로 관리)
S3_BATCH="s3://oliveyoung-crawl-data/graph_gold_csvs/batch_job=20260511_174455"
S3_PRODUCT="s3://oliveyoung-crawl-data/gold/neo4j/oliveyoung/nodes/Product/oliveyoung_neo4j_20260510_063644/part-00000.csv"
S3_CONTAINS="s3://oliveyoung-crawl-data/gold/neo4j/oliveyoung/rels/CONTAINS/oliveyoung_neo4j_20260512_133725/part-00000.csv"

echo "=== [1/4] S3에서 CSV 다운로드 ==="

# batch 경로에서 ingredient, effect, concern, affects, relates_to 받기
# product, contains는 별도 경로에서 받으므로 제외
aws s3 sync "$S3_BATCH/nodes/" "$CSV_DIR/nodes/" \
  --exclude "product.csv"
aws s3 sync "$S3_BATCH/edges/" "$CSV_DIR/edges/" \
  --exclude "contains.csv"

# product.csv (별도 경로 + 헤더 추가)
echo "product.csv 다운로드..."
aws s3 cp "$S3_PRODUCT" /tmp/product_raw.csv
{ echo "product_id:ID(Product),product_name,brand,category"; cat /tmp/product_raw.csv; } > "$CSV_DIR/nodes/product.csv"

# contains.csv (별도 경로 + 헤더 추가)
echo "contains.csv 다운로드..."
aws s3 cp "$S3_CONTAINS" /tmp/contains_raw.csv
{ echo ":START_ID(Product),:END_ID(Ingredient)"; cat /tmp/contains_raw.csv; } > "$CSV_DIR/edges/contains.csv"

echo "다운로드 완료:"
find "$CSV_DIR" -name "*.csv" | sort

echo ""
echo "=== [2/4] ID 검증 ==="
python3 /home/graphdb/validate.py
echo ""

echo "=== [3/4] import 디렉토리로 복사 ==="
sudo chown -R jiwoo:jiwoo "$IMPORT_DIR"
cp -r "$CSV_DIR"/* "$IMPORT_DIR/"
echo "복사 완료"

echo ""
echo "=== [4/4] neo4j-admin bulk import ==="
if docker ps -q -f name=neo4j | grep -q .; then
  echo "Neo4j 컨테이너 중지 중..."
  docker stop neo4j
fi

docker run --rm \
  -v /home/graphdb/neo4j/data:/data \
  -v /home/graphdb/neo4j/import:/var/lib/neo4j/import \
  neo4j:5 \
  neo4j-admin database import full \
    --nodes=Product=/var/lib/neo4j/import/nodes/product.csv \
    --nodes=Ingredient=/var/lib/neo4j/import/nodes/ingredient.csv \
    --nodes=Effect=/var/lib/neo4j/import/nodes/effect.csv \
    --nodes=Concern=/var/lib/neo4j/import/nodes/concern.csv \
    --relationships=CONTAINS=/var/lib/neo4j/import/edges/contains.csv \
    --relationships=AFFECTS=/var/lib/neo4j/import/edges/affects.csv \
    --relationships=RELATES_TO=/var/lib/neo4j/import/edges/relates_to.csv \
    --overwrite-destination \
    neo4j

echo ""
echo "=== Import 완료! Neo4j 재시작 ==="
docker compose -f /home/graphdb/docker-compose.yml up -d
echo ""
echo "브라우저: http://localhost:7474"
echo "ID: neo4j / PW: graphdb1234"
