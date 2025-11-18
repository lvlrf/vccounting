/**
 * Credit & Transactions Script
 */

let allTransactions = [];

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
    await loadCreditData();

    // Event listeners برای فیلترها
    document.getElementById('operationFilter').addEventListener('change', filterTransactions);
    document.getElementById('typeFilter').addEventListener('change', filterTransactions);
    document.getElementById('searchInput').addEventListener('input', filterTransactions);
});

async function loadCreditData() {
    try {
        showLoading(true);

        // دریافت موجودی
        const balance = await api.getCreditBalance();
        document.getElementById('creditBalance').textContent = balance.balance.toLocaleString('fa-IR');
        document.getElementById('currentBalance').textContent = balance.balance.toLocaleString('fa-IR');

        // دریافت تراکنش‌ها
        allTransactions = await api.getCreditTransactions(0, 1000);
        displayTransactions(allTransactions);

        // محاسبه آمار
        calculateStats(allTransactions, balance.balance);

    } catch (error) {
        console.error('Error loading credit data:', error);
        M.toast({ html: 'خطا در بارگذاری داده‌ها: ' + error.message, classes: 'red' });
    } finally {
        showLoading(false);
    }
}

function calculateStats(transactions, currentBalance) {
    let totalReceived = 0;
    let totalSpent = 0;

    transactions.forEach(transaction => {
        if (transaction.amount > 0) {
            totalReceived += transaction.amount;
        } else {
            totalSpent += Math.abs(transaction.amount);
        }
    });

    document.getElementById('totalReceived').textContent = totalReceived.toLocaleString('fa-IR');
    document.getElementById('totalSpent').textContent = totalSpent.toLocaleString('fa-IR');
}

function displayTransactions(transactions) {
    const tbody = document.getElementById('transactionsTableBody');
    tbody.innerHTML = '';

    if (!transactions || transactions.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="center-align grey-text">
                    هیچ تراکنشی یافت نشد
                </td>
            </tr>
        `;
        return;
    }

    transactions.forEach(transaction => {
        const row = document.createElement('tr');

        const date = new Date(transaction.created_at);
        const dateStr = date.toLocaleString('fa-IR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        const amountClass = transaction.amount >= 0 ? 'green-text' : 'red-text';
        const amountSign = transaction.amount >= 0 ? '+' : '';
        const amountIcon = transaction.amount >= 0 ? '↑' : '↓';

        row.innerHTML = `
            <td>${dateStr}</td>
            <td><span class="chip">${getOperationLabel(transaction.operation)}</span></td>
            <td class="${amountClass}">
                <strong>${amountIcon} ${amountSign}${transaction.amount.toLocaleString('fa-IR')}</strong>
            </td>
            <td><strong>${transaction.balance_after.toLocaleString('fa-IR')}</strong></td>
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

function filterTransactions() {
    const operationFilter = document.getElementById('operationFilter').value;
    const typeFilter = document.getElementById('typeFilter').value;
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();

    let filtered = allTransactions;

    // فیلتر عملیات
    if (operationFilter) {
        filtered = filtered.filter(t => t.operation === operationFilter);
    }

    // فیلتر نوع (افزایش/کاهش)
    if (typeFilter === 'positive') {
        filtered = filtered.filter(t => t.amount > 0);
    } else if (typeFilter === 'negative') {
        filtered = filtered.filter(t => t.amount < 0);
    }

    // جستجو در توضیحات
    if (searchTerm) {
        filtered = filtered.filter(t =>
            (t.description && t.description.toLowerCase().includes(searchTerm))
        );
    }

    displayTransactions(filtered);
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
