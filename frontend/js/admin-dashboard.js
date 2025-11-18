/**
 * Admin Dashboard Script
 */

document.addEventListener('DOMContentLoaded', async function() {
    // بررسی authentication
    if (!api.token || !api.user || api.user.role !== 'admin') {
        window.location.href = '/';
        return;
    }

    // نمایش اطلاعات کاربر
    document.getElementById('userFullName').textContent = api.user.full_name || 'مدیر سیستم';
    document.getElementById('userUsername').textContent = `@${api.user.username}`;

    // بارگذاری داده‌ها
    await loadDashboardData();
});

async function loadDashboardData() {
    try {
        showLoading(true);

        // دریافت نمایندگان
        const resellers = await api.getResellers();
        document.getElementById('totalResellers').textContent = resellers.length.toLocaleString('fa-IR');
        displayRecentResellers(resellers.slice(0, 5));

        // دریافت محصولات
        const products = await api.getProducts();
        document.getElementById('totalProducts').textContent = products.length.toLocaleString('fa-IR');
        displayProducts(products);

        // محاسبه آمار کلی
        let totalActiveAccounts = 0;
        let totalCreditDistributed = 0;

        resellers.forEach(reseller => {
            if (reseller.credit_balance) {
                totalCreditDistributed += reseller.credit_balance;
            }
        });

        // TODO: دریافت تعداد کل اکانت‌های فعال از API
        // فعلاً یک مقدار نمونه قرار می‌دهیم
        document.getElementById('totalActiveAccounts').textContent = totalActiveAccounts.toLocaleString('fa-IR');
        document.getElementById('totalCreditDistributed').textContent = totalCreditDistributed.toLocaleString('fa-IR');

    } catch (error) {
        console.error('Error loading dashboard:', error);
        M.toast({ html: 'خطا در بارگذاری داده‌ها: ' + error.message, classes: 'red' });
    } finally {
        showLoading(false);
    }
}

function displayRecentResellers(resellers) {
    const tbody = document.getElementById('recentResellersBody');
    tbody.innerHTML = '';

    if (!resellers || resellers.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="3" class="center-align grey-text">
                    هیچ نماینده‌ای یافت نشد
                </td>
            </tr>
        `;
        return;
    }

    resellers.forEach(reseller => {
        const row = document.createElement('tr');

        const statusBadge = reseller.is_active
            ? '<span class="badge green white-text">فعال</span>'
            : '<span class="badge red white-text">غیرفعال</span>';

        row.innerHTML = `
            <td>${reseller.full_name || '-'}</td>
            <td>${reseller.username}</td>
            <td>${statusBadge}</td>
        `;

        tbody.appendChild(row);
    });
}

function displayProducts(products) {
    const tbody = document.getElementById('productsBody');
    tbody.innerHTML = '';

    if (!products || products.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="3" class="center-align grey-text">
                    هیچ محصولی یافت نشد
                </td>
            </tr>
        `;
        return;
    }

    products.forEach(product => {
        const row = document.createElement('tr');

        const statusBadge = product.is_active
            ? '<span class="badge green white-text">فعال</span>'
            : '<span class="badge red white-text">غیرفعال</span>';

        const typeLabel = getProductTypeLabel(product.product_type);

        row.innerHTML = `
            <td>${product.name}</td>
            <td><span class="chip">${typeLabel}</span></td>
            <td>${statusBadge}</td>
        `;

        tbody.appendChild(row);
    });
}

function getProductTypeLabel(type) {
    const labels = {
        'marzban': 'مرزبان',
        'remnawave': 'رمناویو',
        'marzneshin': 'مرزنشین'
    };

    return labels[type] || type;
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('active');
}

async function logout() {
    if (confirm('آیا مطمئن هستید که می‌خواهید خارج شوید؟')) {
        try {
            await api.logout();
            window.location.href = '/';
        } catch (error) {
            api.clearAuth();
            window.location.href = '/';
        }
    }
}

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.add('active');
    } else {
        overlay.classList.remove('active');
    }
}
