#!/bin/bash
# モニタリングスクリプト: db_monitor.sh

echo 'PostgreSQL Connection Monitor';
echo '===========================';
while true; do
  echo \"\$$(date '+%Y-%m-%d %H:%M:%S') - Connection stats:\";
  echo '- Total connections:';
  psql -c 'SELECT count(*) AS total_connections FROM pg_stat_activity;';
  echo '- Connections by state:';
  psql -c 'SELECT state, count(*) FROM pg_stat_activity GROUP BY state;';
  echo '- Connections by application:';
  psql -c 'SELECT application_name, count(*) FROM pg_stat_activity GROUP BY application_name;';
  echo '- Long running queries:';
  psql -c \"SELECT pid, now() - query_start AS duration, state, query FROM pg_stat_activity WHERE state != 'idle' AND (now() - query_start) > interval '5 seconds';\";
  echo '===========================';
  sleep 10;
done