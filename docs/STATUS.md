# SuvNazorat — Tizimning Joriy Holati

| Qism / Modul | Holat | Izoh |
|---|---|---|
| **Monorepo va arxitektura** | **Tayyor** | `apps/backend`, `apps/bot`, `apps/frontend`, `infrastructure`, `scripts` |
| **Backend: Modellar, Servislar, API** | **Tayyor** | 21 ta endpoint, OpenAPI/Swagger hujjatlari ishlaydi |
| **Alembic Migratsiya (`0001`)** | **Tayyor** | SQLite va PostgreSQL uchun to'liq mos jadvallar, indekslar va constraintlar |
| **Autentifikatsiya (USER, Argon2, Cookie-Session, CSRF)** | **Tayyor** | Faqat bitta `USER` roli, xavfsiz sessiya, rate limit |
| **Dinamik Kalit So'zlar va Qoidalar** | **Tayyor** | Normalizatsiya (o'zbek apostroflari), 3 match turi, saytdan kiritish/tahrirlash |
| **Telegram Bot (aiogram 3.x, HTTP API)** | **Tayyor** | Bevosita bazaga ulanmaydi; xabarlarni normalizatsiya qiladi, keshlaydi, deduplikatsiya, retry, heartbeat |
| **Jonli Bot Tokeni** | **Tasdiqlangan** | `@hokimyatsuvnazorati_bot` Telegram API orqali faol deb tasdiqlandi |
| **Qoidalarni restartsiz yangilash (Cache)** | **Tayyor** | 15–30s avtomatik yangilanish, backend uzilsa oxirgi keshdan foydalanish |
| **Frontend (Next.js 14 App Router, TypeScript, Tailwind)** | **Tayyor** | To'liq o'zbek tilida, Light/Dark mode, responsive, jonli 15s yangilanish |
| **Frontend Sifat Nazorati** | **Tayyor** | TypeScript (0 xato), ESLint (0 xato), Next.js 14 build (10/10 marshrut tayyor) |
| **Dashboard** | **Tayyor** | 6 ta statistik karta, bot statusi, oxirgi hodisalar va xabarlar, manbalar holati |
| **Hodisalar boshqaruvi (Incidents)** | **Tayyor** | Ro'yxat, qidiruv, status/kategoriya/sana filtrlari, sahifalash, batafsil sahifa, timeline, izohlar, status o'zgartirish |
| **Telegram manbalari (Sources)** | **Tayyor** | Manba qo'shish, tahrirlash, faollashtirish/deaktivatsiya, ruxsatlar yo'riqnomasi |
| **Docker Compose va Dockerfile'lar** | **Tayyor** | PostgreSQL, Backend, Bot va Frontend to'liq konteynerlangan va tekshirilgan |
| **Zaxira nusxa va tiklash (Backup & Restore)** | **Tayyor** | PowerShell (`.ps1`) va Bash (`.sh`) skriptlari |
| **Backend testlari** | **Tayyor (67/67)** | Avtorizatsiya, hodisalar, qoidalar, ingest, dashboard, ruff va 16 bosqichli E2E |
| **Bot testlari** | **Tayyor (21/21)** | Normalizatsiya, matcher, inkor, rejali ta'mir, deduplikatsiya, kesh yangilanishi, backend retry |
| **Frontend testlari** | **Tayyor (3/3)** | O'zbek label utilitalari va formatlash testlari |
| **16 Bosqichli E2E Integratsiya** | **Tayyor** | Barcha 16 ta amaliy qadam muvaffaqiyatli avtomatlashtirilgan va tasdiqlangan |
| **Hujjatlar va yo'riqnomalar** | **Tayyor** | To'liq `README.md`, `AUDIT_REPORT.md`, `.env.example`, bootstrap skripti |
