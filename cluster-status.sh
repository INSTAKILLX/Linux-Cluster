#!/usr/bin/env bash
set -euo pipefail
CASSANDRA=${CASSANDRA:-10.50.0.11}
KAFKA=${KAFKA:-10.50.0.11:9092}
CONTROLLER=${CONTROLLER:-10.50.0.10}
KAFKA_VERSION=${KAFKA_VERSION:-4.3.1}
CASSANDRA_VERSION=${CASSANDRA_VERSION:-5.0.9}

echo '=== Cassandra ==='
docker run --rm --network host cassandra:"$CASSANDRA_VERSION" nodetool -h "$CASSANDRA" status || true

echo
echo '=== Kafka ==='
docker run --rm --network host apache/kafka:"$KAFKA_VERSION" /opt/kafka/bin/kafka-metadata-quorum.sh --bootstrap-server "$KAFKA" describe --status || true

echo
echo '=== API ==='
curl -fsS "http://$CONTROLLER:8000/health" | jq . || true

echo
#echo "Spark UI: http://$CONTROLLER:8080"
#echo "SentinelFlow dashboard: http://$CONTROLLER:8088"
