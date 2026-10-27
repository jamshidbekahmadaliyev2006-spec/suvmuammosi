#!/usr/bin/env bash
set -euo pipefail

if [ -z "${1:-}" ]; then
  echo "Xatolik: Backup faylini ko'rsating. Masalan: ./scripts/restore.sh backups/file.sql"
  exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
  echo "Xatolik: $BACKUP_FILE topilmadi!"
  exit 1
fi

echo "OGOHLANTIRISH: Ushbu amal bazadagi ma'lumotlarni almashtiradi!"
read -p "Davom etishni xohlaysizmi? (ha/yoq): " CONFIRM
if [ "$CONFIRM" != "ha" ]; then
  echo "Bekor qilindi."
  exit 0
fi

echo "Tiklanmoqda: $BACKUP_FILE"

if command -v docker &> /dev/null && docker ps | grep -q suvnazorat-postgres; then
  docker exec -i suvnazorat-postgres psql -U suvnazorat -d suvnazorat < "$BACKUP_FILE"
else
  psql -U suvnazorat -d suvnazorat < "$BACKUP_FILE"
fi

echo "Baza muvaffaqiyatli tiklandi!"
