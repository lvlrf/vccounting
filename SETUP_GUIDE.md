# راهنمای راه‌اندازی کامل

این راهنما شما را گام به گام در راه‌اندازی پروژه همراهی می‌کند.

## فاز 1: نصب پیش‌نیازها

### نصب Docker (توصیه می‌شود)

#### Ubuntu/Debian
```bash
# حذف نسخه‌های قدیمی
sudo apt-get remove docker docker-engine docker.io containerd runc

# نصب dependencies
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg lsb-release

# اضافه کردن GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# اضافه کردن repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# نصب Docker
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# تست نصب
sudo docker run hello-world
```

### یا نصب Python و PostgreSQL (بدون Docker)

#### Ubuntu/Debian
```bash
# نصب Python 3.11
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev python3-pip

# نصب PostgreSQL
sudo apt install postgresql postgresql-contrib

# راه‌اندازی PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

## فاز 2: دانلود و تنظیم پروژه

```bash
# کلون پروژه
git clone https://github.com/lvlrf/vccounting.git
cd vccounting

# ساخت فایل .env
cp backend/.env.example backend/.env
```

## فاز 3: تنظیم فایل .env

ویرایش `backend/.env`:

```bash
nano backend/.env
```

**تنظیمات اجباری برای تغییر**:

```env
# Database - در production رمز قوی استفاده کنید
DATABASE_URL=postgresql://admin:CHANGE_THIS_PASSWORD@db:5432/reseller_panel

# Security - حتماً تولید مقادیر جدید
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Admin User - برای اولین ورود
ADMIN_USERNAME=admin
ADMIN_PASSWORD=CHANGE_THIS_PASSWORD
ADMIN_EMAIL=admin@yourdomain.com

# Application
DEBUG=False  # در production
```

**تولید کلیدهای امن**:

```bash
# SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# ENCRYPTION_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## فاز 4: راه‌اندازی

### با Docker

```bash
# ساخت و راه‌اندازی containers
docker-compose up -d

# مشاهده logs
docker-compose logs -f backend

# بررسی وضعیت
docker-compose ps
```

منتظر بمانید تا پیام زیر را ببینید:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### بدون Docker

```bash
# ایجاد دیتابیس
sudo -u postgres psql << EOF
CREATE DATABASE reseller_panel;
CREATE USER admin WITH PASSWORD 'your_password';
ALTER ROLE admin SET client_encoding TO 'utf8';
ALTER ROLE admin SET default_transaction_isolation TO 'read committed';
ALTER ROLE admin SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE reseller_panel TO admin;
\q
EOF

# ایجاد virtual environment
cd backend
python3.11 -m venv venv
source venv/bin/activate

# نصب dependencies
pip install -r requirements.txt

# اجرای migrations (بعد از ایجاد)
# alembic upgrade head

# راه‌اندازی
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## فاز 5: بررسی نصب

### تست Health Check

```bash
curl http://localhost:8000/health
```

خروجی باید مشابه زیر باشد:
```json
{
    "status": "healthy",
    "app_name": "Reseller Management Panel",
    "version": "1.0.0"
}
```

### دسترسی به API Docs

مرورگر خود را باز کنید و به آدرس زیر بروید:
```
http://localhost:8000/api/docs
```

باید صفحه Swagger UI را ببینید.

## فاز 6: ایجاد اولین Admin

### روش 1: از طریق Script (پیشنهادی)

```bash
cd backend
source venv/bin/activate  # اگر از Docker استفاده نمی‌کنید
python scripts/create_admin.py
```

### روش 2: دستی از طریق API

```bash
# ایجاد admin user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "admin123",
    "role": "admin"
  }'
```

### ورود با Admin

```bash
# دریافت token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

## فاز 7: راه‌اندازی اولیه سیستم

### 1. ایجاد محصول

```bash
# مثال: ایجاد محصول Marzban VPN
curl -X POST http://localhost:8000/api/admin/products \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Marzban VPN Premium",
    "description": "سرویس VPN پریمیوم",
    "product_type": "vpn_panel",
    "category": "vpn",
    "integration_type": "api",
    "panel_type": "marzban",
    "requires_panel_connection": true
  }'
```

### 2. ایجاد گروه محصول

```bash
curl -X POST http://localhost:8000/api/admin/product-groups \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "VPN پریمیوم",
    "description": "محصولات VPN با کیفیت بالا",
    "product_ids": ["PRODUCT_ID_FROM_STEP_1"]
  }'
```

### 3. ایجاد پلن‌های سرویس

```bash
# پلن روزانه 1GB
curl -X POST http://localhost:8000/api/admin/service-plans \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "PRODUCT_ID",
    "name": "روزانه 1GB",
    "plan_type": "daily",
    "data_limit_gb": 1,
    "duration_days": 1,
    "device_limit": 1,
    "credit_cost": 1.0
  }'

# پلن ماهانه 100GB
curl -X POST http://localhost:8000/api/admin/service-plans \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "PRODUCT_ID",
    "name": "ماهانه 100GB",
    "plan_type": "monthly",
    "data_limit_gb": 100,
    "duration_days": 30,
    "device_limit": 2,
    "credit_cost": 25.0
  }'
```

### 4. اتصال به پنل

```bash
curl -X POST http://localhost:8000/api/admin/panel-connections \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "PRODUCT_ID",
    "name": "Marzban Server 1",
    "panel_type": "marzban",
    "base_url": "https://your-panel.com",
    "credentials": {
      "username": "admin",
      "password": "panel_password"
    },
    "is_shared": true
  }'
```

### 5. ایجاد گروه نمایندگی

```bash
curl -X POST http://localhost:8000/api/admin/reseller-groups \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "نمایندگان سطح 1",
    "description": "نمایندگان با تخفیف 10%",
    "discount_percentage": 10,
    "default_credit": 100
  }'
```

### 6. ایجاد نماینده

```bash
curl -X POST http://localhost:8000/api/admin/resellers \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "reseller1",
    "email": "reseller1@example.com",
    "password": "reseller123",
    "role": "reseller",
    "full_name": "نماینده شماره 1",
    "phone": "09123456789",
    "telegram": "@reseller1",
    "group_id": "RESELLER_GROUP_ID"
  }'
```

## فاز 8: تست سیستم

### تست به عنوان Reseller

```bash
# ورود
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "reseller1", "password": "reseller123"}' \
  | jq -r '.access_token')

# دریافت موجودی کریدیت
curl -X GET http://localhost:8000/api/reseller/credit/balance \
  -H "Authorization: Bearer $TOKEN"

# ایجاد اکانت
curl -X POST http://localhost:8000/api/reseller/accounts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "PRODUCT_ID",
    "service_plan_id": "PLAN_ID",
    "username": "test_user_1",
    "customer_name": "مشتری تست"
  }'
```

## مشکلات رایج و راه‌حل‌ها

### 1. خطای اتصال به دیتابیس

**علت**: PostgreSQL در حال اجرا نیست یا تنظیمات اتصال اشتباه است.

**راه‌حل**:
```bash
# بررسی وضعیت
sudo systemctl status postgresql

# راه‌اندازی مجدد
sudo systemctl restart postgresql

# تست اتصال
psql -U admin -d reseller_panel -h localhost -W
```

### 2. خطای import OpexCore

**علت**: کتابخانه OpexCore نصب نشده.

**راه‌حل**:
```bash
pip install git+https://github.com/erfjab/OpexCore.git
```

### 3. خطای Unauthorized در API

**علت**: Token نامعتبر یا منقضی شده.

**راه‌حل**: لاگین مجدد و دریافت token جدید.

### 4. Port 8000 در حال استفاده است

**راه‌حل**:
```bash
# پیدا کردن process
sudo lsof -i :8000

# Kill کردن
sudo kill -9 PID
```

## مانیتورینگ و Logs

### Docker Logs

```bash
# تمام logs
docker-compose logs

# فقط backend
docker-compose logs backend

# Live logs
docker-compose logs -f backend
```

### Logs دستی

```bash
# مسیر logs (اگر configure کرده باشید)
tail -f backend/logs/app.log
```

## Backup و Restore

### Backup دیتابیس

```bash
# Docker
docker-compose exec db pg_dump -U admin reseller_panel > backup_$(date +%Y%m%d).sql

# بدون Docker
pg_dump -U admin -h localhost reseller_panel > backup_$(date +%Y%m%d).sql
```

### Restore

```bash
# Docker
docker-compose exec -T db psql -U admin reseller_panel < backup.sql

# بدون Docker
psql -U admin -h localhost reseller_panel < backup.sql
```

## مراحل بعدی

1. ✅ تنظیم SSL/TLS با Nginx یا Caddy
2. ✅ پیکربندی Firewall
3. ✅ تنظیم Cron jobs برای backup خودکار
4. ✅ مانیتورینگ با Prometheus/Grafana
5. ✅ تنظیم Email notifications

## پشتیبانی

اگر به مشکلی برخوردید:
1. ابتدا logs را بررسی کنید
2. در بخش Issues گیت‌هاب جستجو کنید
3. Issue جدید باز کنید با جزئیات کامل (logs, تنظیمات, ...)

---

**موفق باشید! 🚀**
