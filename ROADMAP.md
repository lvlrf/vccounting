# نقشه راه پروژه (Roadmap)

این سند نقشه راه توسعه پروژه را نشان می‌دهد.

## ✅ فاز 1: پایه و اساس (انجام شده)

- [x] طراحی معماری سیستم محصول-محور
- [x] ایجاد ساختار پروژه
- [x] تنظیم Docker و Docker Compose
- [x] مدل‌های دیتابیس (SQLAlchemy)
- [x] Pydantic Schemas
- [x] سیستم احراز هویت (JWT)
- [x] سیستم امنیتی (Encryption, Password Hashing)
- [x] لایه انتزاع پنل‌ها (Base, Marzban, Remnawave, Marzneshin)
- [x] سرویس مدیریت کریدیت
- [x] مستندات اولیه (README, SETUP_GUIDE)

## 🚧 فاز 2: سرویس‌ها و API Endpoints (در حال انجام)

### Account Service
- [ ] ایجاد سرویس مدیریت اکانت‌ها
- [ ] پیاده‌سازی عملیات CRUD
- [ ] محاسبه برگشت کریدیت
- [ ] همگام‌سازی با پنل‌ها

### API Endpoints

#### Authentication
- [ ] POST /api/auth/register (ثبت‌نام)
- [ ] POST /api/auth/login (ورود)
- [ ] POST /api/auth/refresh (تمدید token)
- [ ] GET /api/auth/me (اطلاعات کاربر)
- [ ] POST /api/auth/change-password

#### Admin Endpoints
- [ ] مدیریت محصولات (CRUD)
- [ ] مدیریت گروه محصولات
- [ ] مدیریت پلن‌های سرویس
- [ ] مدیریت نمایندگان
- [ ] مدیریت گروه‌های نمایندگی
- [ ] مدیریت کریدیت (شارژ، کسر)
- [ ] مدیریت اتصالات پنل
- [ ] قیمت‌گذاری عملیات
- [ ] گزارشات و آمار

#### Reseller Endpoints
- [ ] مشاهده محصولات در دسترس
- [ ] مدیریت اکانت‌های مشتری
- [ ] مشاهده موجودی و تاریخچه کریدیت
- [ ] آمار و گزارشات شخصی

## 📅 فاز 3: Database Migrations (برنامه‌ریزی شده)

- [ ] راه‌اندازی Alembic
- [ ] ایجاد migration اولیه
- [ ] Script های seed data
- [ ] Script ایجاد admin اولیه

## 🎨 فاز 4: Frontend (برنامه‌ریزی شده)

### پنل Admin
- [ ] صفحه ورود
- [ ] داشبورد (نمای کلی)
- [ ] مدیریت محصولات
- [ ] مدیریت نمایندگان
- [ ] مدیریت کریدیت
- [ ] صفحات گزارشات
- [ ] تنظیمات سیستم

### پنل Reseller
- [ ] صفحه ورود
- [ ] داشبورد (آمار شخصی)
- [ ] لیست اکانت‌ها
- [ ] ایجاد اکانت جدید
- [ ] جزئیات اکانت
- [ ] تاریخچه کریدیت
- [ ] پروفایل کاربری

### ویژگی‌های UI/UX
- [ ] طراحی Responsive
- [ ] Dark Mode
- [ ] چند زبانه (فارسی/انگلیسی)
- [ ] Notifications (Toast)
- [ ] Modal برای عملیات‌ها
- [ ] نمودارها و Chart ها

## ⚙️ فاز 5: ویژگی‌های پیشرفته (آینده)

### Background Jobs
- [ ] راه‌اندازی APScheduler
- [ ] Job همگام‌سازی اکانت‌ها (هر ساعت)
- [ ] Job بررسی اکانت‌های منقضی شده
- [ ] Job پاکسازی logs قدیمی
- [ ] Job گزارش‌گیری روزانه

### Notification System
- [ ] اعلان‌های درون برنامه‌ای
- [ ] ارسال ایمیل (Welcome, Credit Low, Account Expired)
- [ ] ارسال پیام تلگرام (با Bot)
- [ ] وب‌هوک‌ها برای رویدادها

### Payment Integration
- [ ] اتصال به درگاه پرداخت (ZarinPal, IDPay, ...)
- [ ] خرید خودکار کریدیت توسط نماینده
- [ ] تاریخچه پرداخت‌ها
- [ ] صدور فاکتور

### Advanced Features
- [ ] سیستم تیکتینگ (پشتیبانی)
- [ ] سیستم نوتیفیکیشن Real-time (WebSocket)
- [ ] API Rate Limiting پیشرفته
- [ ] سیستم لاگ جامع
- [ ] Multi-tenancy (چند شرکت)
- [ ] White-label (برندینگ سفارشی)

## 🔒 فاز 6: امنیت و بهینه‌سازی (آینده)

### Security
- [ ] 2FA (Two-Factor Authentication)
- [ ] IP Whitelisting
- [ ] Audit Logs (لاگ تمام عملیات)
- [ ] CSRF Protection
- [ ] SQL Injection Prevention (بررسی دوباره)
- [ ] XSS Protection
- [ ] Security Headers

### Performance
- [ ] Caching (Redis)
- [ ] Database Indexing بهینه
- [ ] Query Optimization
- [ ] CDN برای Static Files
- [ ] Load Balancing
- [ ] Database Connection Pooling

### Monitoring
- [ ] Prometheus + Grafana
- [ ] Error Tracking (Sentry)
- [ ] APM (Application Performance Monitoring)
- [ ] Health Checks پیشرفته
- [ ] Alerting System

## 📱 فاز 7: API و Integration (آینده)

- [ ] REST API Documentation (OpenAPI 3.0)
- [ ] GraphQL API
- [ ] Webhook System
- [ ] Public API برای نمایندگان
- [ ] SDKs (Python, JavaScript, PHP)
- [ ] API Versioning

## 🧪 فاز 8: Testing (آینده)

- [ ] Unit Tests (Pytest)
- [ ] Integration Tests
- [ ] End-to-End Tests
- [ ] Load Testing (Locust)
- [ ] Security Testing
- [ ] CI/CD Pipeline (GitHub Actions)

## 🌍 فاز 9: Deployment (آینده)

- [ ] Production Docker Compose
- [ ] Kubernetes Manifests
- [ ] Ansible Playbooks
- [ ] Terraform Scripts
- [ ] Auto-scaling
- [ ] Blue-Green Deployment
- [ ] Rollback Strategy

## 📚 فاز 10: مستندات (آینده)

- [ ] API Documentation کامل
- [ ] User Guide برای Admin
- [ ] User Guide برای Reseller
- [ ] Developer Documentation
- [ ] Video Tutorials
- [ ] FAQ Section

## 🆕 فاز 11: محصولات جدید (آینده)

### پشتیبانی از محصولات جدید
- [ ] Panel های VPN دیگر (v2ray-core, Xray, ...)
- [ ] Hosting (cPanel, DirectAdmin, Plesk)
- [ ] Domain Registration
- [ ] SSL Certificates
- [ ] Email Services
- [ ] Cloud Storage
- [ ] SMS Services

### Template System
- [ ] قالب‌سازی برای محصولات
- [ ] Custom Fields
- [ ] پیکربندی پویا

## 📊 Metrics و KPIs

### ردیابی موفقیت پروژه
- تعداد نمایندگان فعال
- تعداد اکانت‌های ایجاد شده
- درآمد کل (کریدیت فروخته شده)
- میانگین استفاده از کریدیت
- نرخ رضایت کاربران
- Uptime سیستم

## 🤝 مشارکت

پروژه به مشارکت‌کنندگان احتیاج دارد! اگر علاقه‌مند هستید:
1. یک آیتم از roadmap را انتخاب کنید
2. Issue مربوطه را check کنید یا ایجاد کنید
3. Fork و Pull Request ارسال کنید

## 📝 یادداشت‌ها

- این roadmap زنده است و ممکن است بر اساس نیازها تغییر کند
- اولویت‌ها بر اساس feedback جامعه تنظیم می‌شوند
- زمان‌بندی تقریبی است و قطعی نیست

---

**آخرین بروزرسانی**: 2025-11-17
**نسخه فعلی**: v0.1.0-alpha
**نسخه هدف بعدی**: v0.2.0 (با API Endpoints کامل)
