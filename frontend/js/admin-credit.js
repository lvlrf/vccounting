/**
 * Admin Credit Management Script
 */

let resellers = [];

document.addEventListener('DOMContentLoaded', async function() {
    // بررسی authentication
    if (!api.token || !api.user || api.user.role !== 'admin') {
        window.location.href = '/';
        return;
    }

    // نمایش اطلاعات کاربر
    document.getElementById('userFullName').textContent = api.user.full_name || 'مدیر سیستم';
    document.getElementById('userUsername').textContent = `@${api.user.username}`;

    // Initialize form select
    M.FormSelect.init(document.querySelectorAll('select'));

    // بارگذاری داده‌ها
    await loadResellersData();

    // Event listener برای فرم سریع
    document.getElementById('quickAddCreditForm').addEventListener('submit', handleQuickAddCredit);
});

async function loadResellersData() {
    try {
        showLoading(true);

        // دریافت نمایندگان
        resellers = await api.getResellers();

        // پر کردن select
        populateResellerSelect();

        // نمایش جدول
        displayResellersBalance(resellers);

    } catch (error) {
        console.error('Error loading data:', error);
        M.toast({ html: 'خطا در بارگذاری داده‌ها: ' + error.message, classes: 'red' });
    } finally {
        showLoading(false);
    }
}

function populateResellerSelect() {
    const select = document.getElementById('quickResellerId');
    select.innerHTML = '<option value="" disabled selected>انتخاب نماینده</option>';

    resellers.forEach(reseller => {
        const option = document.createElement('option');
        option.value = reseller.id;
        option.textContent = `${reseller.full_name || reseller.username} (@${reseller.username})`;
        select.appendChild(option);
    });

    M.FormSelect.init(document.querySelectorAll('select'));
}

function displayResellersBalance(resellers) {
    const tbody = document.getElementById('resellersBalanceBody');
    tbody.innerHTML = '';

    if (!resellers || resellers.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="center-align grey-text">
                    هیچ نماینده‌ای یافت نشد
                </td>
            </tr>
        `;
        return;
    }

    resellers.forEach(reseller => {
        const row = document.createElement('tr');

        const balance = reseller.credit_balance || 0;
        const balanceClass = balance > 0 ? 'green-text' : (balance < 0 ? 'red-text' : 'grey-text');

        const statusBadge = reseller.is_active
            ? '<span class="badge green white-text">فعال</span>'
            : '<span class="badge red white-text">غیرفعال</span>';

        // TODO: دریافت آمار کل دریافتی و خرج شده از API
        // فعلاً مقادیر پیش‌فرض نمایش می‌دهیم
        const totalReceived = 0;
        const totalSpent = 0;

        row.innerHTML = `
            <td>
                <strong>${reseller.full_name || reseller.username}</strong><br>
                <small class="grey-text">@${reseller.username}</small>
            </td>
            <td><strong class="${balanceClass}">${balance.toLocaleString('fa-IR')}</strong></td>
            <td><span class="green-text">${totalReceived.toLocaleString('fa-IR')}</span></td>
            <td><span class="orange-text">${totalSpent.toLocaleString('fa-IR')}</span></td>
            <td>${statusBadge}</td>
        `;

        tbody.appendChild(row);
    });
}

async function handleQuickAddCredit(e) {
    e.preventDefault();

    const resellerId = parseInt(document.getElementById('quickResellerId').value);
    const amount = parseInt(document.getElementById('quickAmount').value);
    const note = document.getElementById('quickNote').value.trim();

    if (!resellerId || !amount || amount < 1) {
        M.toast({ html: 'لطفاً نماینده و مقدار معتبر انتخاب کنید', classes: 'red' });
        return;
    }

    try {
        showLoading(true);

        await api.addCredit(resellerId, amount, note || null);

        M.toast({ html: 'کریدیت با موفقیت اضافه شد', classes: 'green' });

        // پاک کردن فرم
        document.getElementById('quickAddCreditForm').reset();
        M.FormSelect.init(document.querySelectorAll('select'));

        // بارگذاری مجدد داده‌ها
        await loadResellersData();

    } catch (error) {
        console.error('Error adding credit:', error);
        M.toast({ html: 'خطا در افزودن کریدیت: ' + error.message, classes: 'red' });
    } finally {
        showLoading(false);
    }
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
