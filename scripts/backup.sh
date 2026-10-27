#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/suvnazorat_backup_$TIMESTAMP.sql"

echo "Zaxira nusxa olinmoqda: $BACKUP_FILE"

if command -v docker &> /dev/null && docker ps | grep -q suvnazorat-postgres; then
  docker exec -t suvnazorat-postgres pg_dump -U suvnazorat suvnazorat > "$BACKUP_FILE"
else
  pg_dump -U suvnazorat -d suvnazorat -F c -b -v -f "$BACKUP_FILE"
fi

echo "Muvaffaqiyatli yakunlandi: $BACKUP_FILE"
