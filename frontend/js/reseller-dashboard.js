/**
 * Reseller Dashboard Script
 */

document.addEventListener('DOMContentLoaded', async function() {
    // بررسی authentication
    if (!api.token || !api.user || api.user.role !== 'reseller') {
        window.location.href = '/';
        return;
    }

    // نمایش اطلاعات کاربر
    document.getElementById('userFullName').textContent = api.user.full_name || 'نماینده';
    document.getElementById('userUsername').textContent = `@${api.user.username}`;

    // بارگذاری داده‌ها
    await loadDashboardData();
});

async function loadDashboardData() {
    try {
        showLoading(true);

        // دریافت موجودی کریدیت
        const creditBalance = await api.getCreditBalance();
        document.getElementById('creditBalance').textContent = creditBalance.balance.toLocaleString('fa-IR');

        // دریافت آمار
        const stats = await api.getOverviewStats();
        document.getElementById('activeAccounts').textContent = stats.active_accounts.toLocaleString('fa-IR');
        document.getElementById('expiredAccounts').textContent = stats.expired_accounts.toLocaleString('fa-IR');
        document.getElementById('totalAccounts').textContent = stats.total_accounts_created.toLocaleString('fa-IR');
        document.getElementById('spentCredit').textContent = stats.total_credit_spent.toLocaleString('fa-IR');

        // دریافت آخرین تراکنش‌ها
        const transactions = await api.getCreditTransactions(0, 10);
        displayRecentTransactions(transactions);

    } catch (error) {
        console.error('Error loading dashboard:', error);
        M.toast({ html: 'خطا در بارگذاری داده‌ها: ' + error.message, classes: 'red' });
    } finally {
        showLoading(false);
    }
}

function displayRecentTransactions(transactions) {
    const tbody = document.getElementById('transactionsBody');
    tbody.innerHTML = '';

    if (!transactions || transactions.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="center-align grey-text">
                    هیچ تراکنشی یافت نشد
                </td>
            </tr>
        `;
        return;
    }

    transactions.forEach(transaction => {
        const row = document.createElement('tr');

        const date = new Date(transaction.created_at);
        const dateStr = date.toLocaleString('fa-IR');

        const amountClass = transaction.amount >= 0 ? 'green-text' : 'red-text';
        const amountSign = transaction.amount >= 0 ? '+' : '';

        row.innerHTML = `
            <td>${dateStr}</td>
            <td><span class="chip">${getOperationLabel(transaction.operation)}</span></td>
            <td class="${amountClass}"><strong>${amountSign}${transaction.amount.toLocaleString('fa-IR')}</strong></td>
            <td>${transaction.description || '-'}</td>
        `;

        tbody.appendChild(row);
    });
}

function getOperationLabel(operation) {
    const labels = {
        'create_account': 'ایجاد اکانت',
        'renew': 'تمدید',
        'add_traffic': 'افزودن حجم',
        'delete': 'حذف اکانت',
        'manual': 'تراکنش دستی'
    };

    return labels[operation] || operation;
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
            // حتی در صورت خطا، کاربر را logout کن
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
