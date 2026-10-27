# PostgreSQL bazasini zaxira nusxadan tiklash (restore) skripti
Param(
    [Parameter(Mandatory=$true)]
    [string]$BackupFile,
    [string]$DbUser = "suvnazorat",
    [string]$DbName = "suvnazorat"
)

$ErrorActionPreference = "Stop"

if (!(Test-Path $BackupFile)) {
    Write-Host "Xatolik: Backup fayli topilmadi: $BackupFile" -ForegroundColor Red
    exit 1
}

Write-Host "DIQQAT: Bazani tiklash joriy ma'lumotlarni o'zgartirishi yoki ustidan yozishi mumkin!" -ForegroundColor Yellow
$Confirmation = Read-Host "Haqiqatan ham tiklashni istaysizmi? (ha / yoq)"
if ($Confirmation -ne "ha") {
    Write-Host "Amal bekor qilindi." -ForegroundColor Gray
    exit 0
}

Write-Host "Tiklanmoqda: $BackupFile ..." -ForegroundColor Cyan

if (Get-Command pg_restore -ErrorAction SilentlyContinue) {
    pg_restore -U $DbUser -d $DbName -v $BackupFile
} else {
    Get-Content $BackupFile | docker exec -i suvnazorat-postgres psql -U $DbUser -d $DbName
}

Write-Host "Baza muvaffaqiyatli tiklandi!" -ForegroundColor Green
