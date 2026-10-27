# SuvNazorat — Suv Ta'minoti Muammolarini Monitoring Qilish Platformasi

SuvNazorat — Telegram kanallari va guruhlarida e'lon qilinayotgan suv ta'minoti va kanalizatsiya bilan bog'liq muammolarni real vaqt rejimida aniqlash, markaziy tizimga to'plash, dinamik kalit so'zlar orqali tahlil qilish va zamonaviy veb-dashboard orqali nazorat qilish platformasi.

---

## 1. Arxitektura va Texnologiyalar

Loyiha monorepo ko'rinishida tashkil etilgan:

```text
suvnazorat/
├── apps/
│   ├── frontend/         # Next.js 14 (App Router), React, TypeScript, Tailwind CSS
│   ├── backend/          # Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2
│   └── bot/              # Python 3.12, aiogram 3.x, HTTP API integratsiyasi
├── infrastructure/
│   └── docker/           # Backend, Bot va Frontend uchun alohida Dockerfile'lar
├── scripts/              # Bootstrap, backup va restore skriptlari (PowerShell va Bash)
├── docs/                 # Loyiha hujjatlari va texnik holat bayoni
├── docker-compose.yml    # PostgreSQL, Backend, Bot va Frontend to'liq konteynerlash
├── .env.example          # Barcha kerakli konfiguratsiyalar namunasi
└── README.md
```

### Muhim arxitektura tamoyillari:
- **Faqat bitta rol (`USER`)**: Tizimda keraksiz rollar matritsasi yo'q. Tizimga kirgan barcha vakolatli xodimlar yagona `USER` roli bilan ishlaydi.
- **Bot bevosita bazaga ulanmaydi**: Telegram bot faqat Backend HTTP API (`/api/v1/bot/*`) orqali muloqot qiladi va barcha biznes qoidalar backendda boshqariladi.
- **Dinamik kalit so'zlar**: Kalit so'zlar faqat kodda saqlanmaydi; sayt orqali qo'shiladi, tahrirlanadi va o'chiriladi. Bot yangi qoidalarni **qayta ishga tushirish (restart) talab qilinmasdan 15–30 soniya ichida** avtomatik qabul qiladi.

---

## 2. Windows PowerShell orqali Mahalliy Ishga Tushirish

### 1-qadam: Muhitni tayyorlash
Loyiha papkasiga o'ting va `.env` faylini yarating:
```powershell
Copy-Item .env.example .env
```
`.env` faylini ochib, kerakli qiymatlarni (ayniqsa, `TELEGRAM_BOT_TOKEN`) kiriting.

### 2-qadam: Avtomatik Bootstrap skripti
Barcha qadamlarni (virtual muhit, dependencylar, migratsiyalar, seed qoidalar va birinchi foydalanuvchi) bir buyruq bilan bajarish:
```powershell
.\scripts\bootstrap.ps1
```

Yoki bosqichma-bosqich qo'lda bajarish:

#### A. Backendni sozlash va ishga tushirish:
```powershell
cd apps\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# Migratsiyalarni qo'llash:
alembic upgrade head

# 16 ta boshlang'ich o'zbekcha qoidalarni kiritish:
python -m app.cli seed-rules

# Birinchi foydalanuvchini (USER) yaratish:
$env:SUVNAZORAT_PASSWORD = "kamida-12-belgili-xavfsiz-parol"
python -m app.cli create-user --username ali --email ali@suvnazorat.uz
Remove-Item Env:SUVNAZORAT_PASSWORD

# Backend serverni ishga tushirish (8000-port):
uvicorn app.main:app --reload --port 8000
```
API hujjatlari (Swagger): `http://localhost:8000/docs`

#### B. Telegram Botni ishga tushirish:
Alohida PowerShell oynasida:
```powershell
cd apps\bot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# Botni ishga tushirish:
python main.py
```

#### C. Frontendni ishga tushirish:
Alohida PowerShell oynasida:
```powershell
cd apps\frontend
npm install
npm run dev
```
Veb-sayt: `http://localhost:3000`

---

## 3. Docker Compose orqali Ishga Tushirish

Agar kompyuteringizda Docker o'rnatilgan bo'lsa, butun tizimni (PostgreSQL, Backend, Bot, Frontend) bir buyruq bilan ko'tarishingiz mumkin:

```powershell
docker compose up --build -d
```

Servislar holatini ko'rish:
```powershell
docker compose ps
docker compose logs -f
```

---

## 4. Telegram Botni Kanallarga Ulash Yo'riqnomasi

1. **Bot yaratish**: Telegramda `@BotFather` ga kiring, `/newbot` buyrug'i orqali yangi bot yarating va berilgan tokenni `.env` dagi `TELEGRAM_BOT_TOKEN` qatoriga yozing.
2. **Kanalga ulash**:
   - Monitoring qilmoqchi bo'lgan Telegram kanalingizga kiring.
   - Kanal sozlamalaridan **Administrators** bo'limiga o'ting va botingizni Administrator sifatida qo'shing.
   - Ruxsatlar orasida "Post Messages" (yoki postlarni ko'rish) yoqilgan bo'lishi kifoya.
3. **Saytda manbani ro'yxatdan o'tkazish**:
   - Veb-saytdagi `Telegram manbalari` (`/sources`) sahifasiga kiring.
   - "Yangi manba qo'shish" tugmasini bosing.
   - Kanal nomi va Chat ID sini kiriting (Chat ID odatda `-100...` bilan boshlanadi).
4. Bot kanaldagi har bir yangi postni avtomatik o'qiydi, normalizatsiya qiladi, kalit so'zlarga solishtiradi va hodisa bo'lsa dashboardda aks ettiradi.

---

## 5. Dinamik Kalit So'zlar va Aniqlash Qoidalari

Saytdagi **Kalit so'zlar** (`/detection-rules`) sahifasida:
- Istalgan vaqtda yangi kalit so'z qo'shish mumkin.
- O'zbek tilidagi barcha apostroflar (`'`, `’`, `‘`, `ʻ`, `ʼ`, `` ` ``) avtomatik tenglashtiriladi.
- Moslik turlari:
  - `PHRASE`: Iborali moslik (masalan, `quvur yorildi`).
  - `WHOLE_WORD`: To'liq so'z chegarasi (masalan, `kanalizatsiya`).
  - `CONTAINS`: Qism mosligi (masalan, `oqmoqda`).
- Kontekst tahlili:
  - Inkor xabarlar (`"muammo yo'q"`, `"avariya emas"`) yangi avariya sifatida belgilanmaydi, `REVIEW_REQUIRED` (tekshirish kerak) belgisi qo'yiladi.
  - Rejali ta'mirlash xabarlari (`"ertaga ta'mirlanadi"`, `"reja asosida"`) avtomatik `PLANNED_REPAIR` kategoriyasiga ajratiladi.
- Saytdan qoida faolsizlantirilsa (`is_active = false`), bot uni yangi xabarlarga ishlatishni darhol to'xtatadi.

---

## 6. Testlar va Sifat Nazorati

### Backend testlari (66+ ta test):
```powershell
cd apps\backend
pytest
ruff check .
```

### Bot testlari (barcha mock testlar: normalizatsiya, matcher, deduplikatsiya, cache, retry):
```powershell
cd apps\bot
pytest
```

### Frontend testlari:
```powershell
cd apps\frontend
npm test
```

---

## 7. Backup va Tiklash (Restore)

### Zaxira nusxa olish:
```powershell
.\scripts\backup.ps1
```
Nusxa sanasi bilan `backups/suvnazorat_backup_YYYYMMDD_HHMMSS.sql` faylida saqlanadi.

### Zaxiradan tiklash:
```powershell
.\scripts\restore.ps1 -BackupFile .\backups\suvnazorat_backup_xxxx.sql
```
