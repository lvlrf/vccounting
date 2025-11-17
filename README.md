# پنل مدیریت نمایندگی محصولات (Multi-Product Reseller Management Panel)

یک پنل مدیریت نمایندگی قابل توسعه برای مدیریت محصولات مختلف با سیستم کریدیت، اتصال به APIهای مختلف و قابلیت افزودن محصولات جدید در آینده.

## ویژگی‌ها

### برای Admin
- ✅ مدیریت نمایندگان (ایجاد، ویرایش، حذف)
- ✅ مدیریت محصولات و پلن‌های سرویس
- ✅ گروه‌بندی محصولات و نمایندگان
- ✅ مدیریت کریدیت (شارژ، کسر، تاریخچه)
- ✅ قیمت‌گذاری پویا برای هر عملیات
- ✅ اتصال به پنل‌های مختلف (Marzban, Remnawave, Marzneshin)
- ✅ گزارشات و آمار

### برای Reseller (نماینده)
- ✅ ایجاد و مدیریت اکانت‌های مشتریان
- ✅ مشاهده موجودی کریدیت و تاریخچه
- ✅ عملیات روی اکانت‌ها (تمدید، افزودن حجم، فعال/غیرفعال، حذف)
- ✅ دریافت لینک اشتراک و QR کد
- ✅ برگشت کریدیت هنگام حذف اکانت

## تکنولوژی‌ها

### Backend
- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Authentication**: JWT (python-jose)
- **Panel Integration**: OpexCore library

### Frontend (در حال توسعه)
- **Template**: AdminDashboard Materialize
- **API Client**: Axios / Fetch API

## پیش‌نیازها

- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose (اختیاری)

## نصب و راه‌اندازی

### روش 1: استفاده از Docker (توصیه می‌شود)

```bash
# کلون پروژه
git clone https://github.com/lvlrf/vccounting.git
cd vccounting

# کپی فایل .env
cp backend/.env.example backend/.env

# ویرایش تنظیمات در backend/.env
nano backend/.env

# راه‌اندازی با Docker Compose
docker-compose up -d

# مشاهده logs
docker-compose logs -f backend
```

سرویس‌ها:
- Backend API: http://localhost:8000
- Frontend: http://localhost:80
- Database: postgresql://localhost:5432
- API Docs: http://localhost:8000/api/docs

### روش 2: نصب دستی

```bash
# نصب PostgreSQL
sudo apt install postgresql postgresql-contrib

# ایجاد دیتابیس
sudo -u postgres psql
CREATE DATABASE reseller_panel;
CREATE USER admin WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE reseller_panel TO admin;
\q

# نصب dependencies
cd backend
python -m venv venv
source venv/bin/activate  # در Windows: venv\Scripts\activate
pip install -r requirements.txt

# تنظیم متغیرهای محیطی
cp .env.example .env
nano .env  # ویرایش تنظیمات

# اجرای migrations (بعد از ایجاد migrations)
# alembic upgrade head

# راه‌اندازی سرور
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## ساختار پروژه

```
vccounting/
├── backend/
│   ├── app/
│   │   ├── models/          # مدل‌های دیتابیس
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── api/             # API endpoints
│   │   ├── services/        # Business logic
│   │   │   └── panel_integrations/  # اتصال به پنل‌ها
│   │   ├── utils/           # ابزارهای کمکی
│   │   ├── config.py        # تنظیمات
│   │   ├── database.py      # اتصال دیتابیس
│   │   └── main.py          # نقطه ورود
│   ├── alembic/             # Database migrations
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/                # در حال توسعه
├── docker-compose.yml
├── nginx.conf
└── README.md
```

## معماری سیستم

### سیستم محصول-محور

پروژه بر اساس معماری Product-Centric طراحی شده:

1. **محصول (Product)**: هر سرویس قابل فروش (VPN, Hosting, Domain, ...)
2. **گروه محصول (Product Group)**: دسته‌بندی محصولات مشابه
3. **پلن سرویس (Service Plan)**: تعرفه‌های مختلف هر محصول
4. **نماینده (Reseller)**: فروشنده محصولات
5. **اکانت مشتری (Customer Account)**: اکانت‌های ایجاد شده توسط نماینده

### سیستم کریدیت

- هر نماینده موجودی کریدیت دارد
- هر عملیات (ایجاد، تمدید، افزودن حجم) کریدیت مصرف می‌کند
- قیمت‌گذاری پویا بر اساس گروه محصول، نوع عملیات و گروه نماینده
- برگشت کریدیت هنگام حذف اکانت (بر اساس زمان و حجم باقیمانده)

### اتصال به پنل‌ها

سیستم از یک لایه انتزاع برای اتصال به پنل‌های مختلف استفاده می‌کند:

- **Base Interface**: `BasePanelIntegration`
- **پیاده‌سازی‌ها**: Marzban, Remnawave, Marzneshin
- **Factory Pattern**: `PanelIntegrationFactory` برای ایجاد integration مناسب

برای افزودن پنل جدید، کافی است یک کلاس جدید از `BasePanelIntegration` ایجاد کنید.

## API Documentation

بعد از راه‌اندازی، مستندات API در آدرس زیر قابل دسترس است:

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

### Endpoints اصلی

```
POST   /api/auth/login                    # ورود
GET    /api/auth/me                       # دریافت اطلاعات کاربر

# Admin
GET    /api/admin/resellers               # لیست نمایندگان
POST   /api/admin/resellers               # ایجاد نماینده
POST   /api/admin/credit/add              # شارژ کریدیت
GET    /api/admin/products                # لیست محصولات
POST   /api/admin/products                # ایجاد محصول

# Reseller
GET    /api/reseller/credit/balance       # موجودی کریدیت
GET    /api/reseller/accounts             # لیست اکانت‌ها
POST   /api/reseller/accounts             # ایجاد اکانت
DELETE /api/reseller/accounts/:id         # حذف اکانت (با برگشت کریدیت)
POST   /api/reseller/accounts/:id/renew   # تمدید اکانت
```

## تنظیمات

فایل `.env` در مسیر `backend/.env`:

```env
# Database
DATABASE_URL=postgresql://admin:password@localhost:5432/reseller_panel

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24

# Encryption
ENCRYPTION_KEY=your-encryption-key-here

# Application
DEBUG=True
APP_NAME=Reseller Management Panel

# Admin Default User
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@example.com
```

**مهم**: در production حتماً مقادیر `SECRET_KEY` و `ENCRYPTION_KEY` را تغییر دهید.

## توسعه

### افزودن پنل جدید

```python
# backend/app/services/panel_integrations/my_panel.py

from .base import BasePanelIntegration

class MyPanelIntegration(BasePanelIntegration):
    async def create_user(self, username, data_limit_gb, expire_days, device_limit):
        # پیاده‌سازی برای پنل شما
        pass

    # پیاده‌سازی بقیه متدها
```

سپس در `factory.py` ثبت کنید:

```python
PanelIntegrationFactory.register_panel("my_panel", MyPanelIntegration)
```

### ایجاد Migration

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## تست

```bash
cd backend
pytest
```

## مشکلات رایج

### خطای اتصال به دیتابیس
```bash
# بررسی وضعیت PostgreSQL
sudo systemctl status postgresql

# بررسی اتصال
psql -U admin -d reseller_panel -h localhost
```

### خطای OpexCore
```bash
# نصب مجدد OpexCore
pip uninstall opexcore
pip install git+https://github.com/erfjab/OpexCore.git
```

## مجوز

MIT License

## مشارکت

Pull Request ها و Issue ها خوش‌آمد هستند!

## تماس

برای سوالات و پشتیبانی:
- GitHub Issues: https://github.com/lvlrf/vccounting/issues

---

**نکته**: این پروژه در حال توسعه است. برای آخرین تغییرات، branch `develop` را دنبال کنید.
