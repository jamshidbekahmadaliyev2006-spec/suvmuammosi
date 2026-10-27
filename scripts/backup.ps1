# PostgreSQL ma'lumotlar bazasidan zaxira nusxa (backup) olish skripti
Param(
    [string]$DbUser = "suvnazorat",
    [string]$DbName = "suvnazorat",
    [string]$BackupDir = ".\backups"
)

$ErrorActionPreference = "Stop"

if (!(Test-Path -Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupFile = Join-Path $BackupDir "suvnazorat_backup_$Timestamp.sql"

Write-Host "Zaxira nusxa yaratilmoqda: $BackupFile" -ForegroundColor Cyan

# Docker orqali yoki mahalliy pg_dump
if (Get-Command pg_dump -ErrorAction SilentlyContinue) {
    pg_dump -U $DbUser -d $DbName -F c -b -v -f $BackupFile
} else {
    docker exec -t suvnazorat-postgres pg_dump -U $DbUser $DbName > $BackupFile
}

if (Test-Path $BackupFile) {
    $Size = (Get-Item $BackupFile).Length
    Write-Host "Muvaffaqiyatli yakunlandi! Fayl hajmi: $Size bayt" -ForegroundColor Green
} else {
    Write-Host "Xatolik: Backup fayli yaratilmadi!" -ForegroundColor Red
}
