# SuvNazorat tizimini ishga tushirishga tayyorlash skripti (Bootstrap)
# PowerShell: .\scripts\bootstrap.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== SuvNazorat Tizimini Sozlash (Bootstrap) ===" -ForegroundColor Cyan

# 1. .env fayli mavjudligini tekshirish
if (!(Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "[OK] .env fayli .env.example dan nusxalandi." -ForegroundColor Green
    } else {
        Write-Host "[XATO] .env.example fayli topilmadi!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[INFO] .env fayli mavjud." -ForegroundColor Yellow
}

# 2. Backend virtual muhitini tekshirish
Write-Host "`nBackend virtual environment tekshirilmoqda..." -ForegroundColor Cyan
Set-Location "apps\backend"

if (!(Test-Path ".venv")) {
    Write-Host "Virtual environment yaratilmoqda (.venv)..."
    python -m venv .venv
}

$VenvPython = ".\.venv\Scripts\python.exe"
if (!(Test-Path $VenvPython)) {
    $VenvPython = "python"
}

Write-Host "Kutubxonalar o'rnatilmoqda..."
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -e ".[dev]"

# 3. Alembic migratsiyalarini qo'llash
Write-Host "`nMa'lumotlar bazasi migratsiyalari bajarilmoqda..." -ForegroundColor Cyan
& $VenvPython -m alembic upgrade head

# 4. Boshlang'ich qoidalarni kiritish
Write-Host "`nBoshlang'ich kalit so'zlar kiritilmoqda..." -ForegroundColor Cyan
& $VenvPython -m app.cli seed-rules

# 5. Birinchi foydalanuvchini yaratish
Write-Host "`nBirinchi foydalanuvchini (USER) yaratish:" -ForegroundColor Cyan
$Username = Read-Host "Foydalanuvchi nomini kiriting (masalan: ali)"
if ($Username) {
    & $VenvPython -m app.cli create-user --username $Username
}

Set-Location "..\.."

Write-Host "`n=== Sozlash muvaffaqiyatli yakunlandi! ===" -ForegroundColor Green
Write-Host "Backendni ishga tushirish: cd apps\backend; uvicorn app.main:app --reload" -ForegroundColor Gray
Write-Host "Botni ishga tushirish: cd apps\bot; python main.py" -ForegroundColor Gray
Write-Host "Frontendni ishga tushirish: cd apps\frontend; npm run dev" -ForegroundColor Gray
