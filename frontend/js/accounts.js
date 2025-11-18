/**
 * Accounts Management Script
 */

let currentAccounts = [];
let products = [];
let servicePlans = [];
let currentAccountId = null;
let modals = {};

document.addEventListener('DOMContentLoaded', async function() {
    // بررسی authentication
    if (!api.token || !api.user || api.user.role !== 'reseller') {
        window.location.href = '/';
        return;
    }

    // نمایش اطلاعات کاربر
    document.getElementById('userFullName').textContent = api.user.full_name || 'نماینده';
    document.getElementById('userUsername').textContent = `@${api.user.username}`;

    // Initialize Materialize components
    modals.create = M.Modal.init(document.getElementById('createAccountModal'));
    modals.renew = M.Modal.init(document.getElementById('renewModal'));
    modals.addTraffic = M.Modal.init(document.getElementById('addTrafficModal'));

    // بارگذاری موجودی کریدیت
    await loadCreditBalance();

    // بارگذاری محصولات و پلن‌ها
    await loadProducts();

    // بارگذاری اکانت‌ها
    await loadAccounts();

    // Event listeners برای فیلترها
    document.getElementById('productFilter').addEventListener('change', filterAccounts);
    document.getElementById('statusFilter').addEventListener('change', filterAccounts);
    document.getElementById('searchInput').addEventListener('input', filterAccounts);

    // Event listener برای تغییر محصول در فرم ایجاد
    document.getElementById('newProduct').addEventListener('change', loadServicePlansForProduct);

    // بررسی query parameter برای باز کردن modal ایجاد
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('action') === 'create') {
        openCreateModal();
    }
});

async function loadCreditBalance() {
    try {
        const result = await api.getCreditBalance();
        document.getElementById('creditBalance').textContent = result.balance.toLocaleString('fa-IR');
    } catch (error) {
        console.error('Error loading credit:', error);
    }
}

async function loadProducts() {
    try {
        products = await api.getProducts();

        // پر کردن select فیلتر محصولات
        const productFilter = document.getElementById('productFilter');
        products.forEach(product => {
            const option = document.createElement('option');
            option.value = product.id;
            option.textContent = product.name;
            productFilter.appendChild(option);
        });

        // پر کردن select محصولات در modal ایجاد
        const newProductSelect = document.getElementById('newProduct');
        products.forEach(product => {
            const option = document.createElement('option');
            option.value = product.id;
            option.textContent = product.name;
            newProductSelect.appendChild(option);
        });

        M.FormSelect.init(document.querySelectorAll('select'));

    } catch (error) {
        console.error('Error loading products:', error);
        M.toast({ html: 'خطا در بارگذاری محصولات', classes: 'red' });
    }
}

async function loadServicePlansForProduct() {
    const productId = document.getElementById('newProduct').value;
    if (!productId) return;

    try {
        servicePlans = await api.getServicePlans(productId);

        const planSelect = document.getElementById('newServicePlan');
        planSelect.innerHTML = '<option value="" disabled selected>انتخاب پلن</option>';

        servicePlans.forEach(plan => {
            const option = document.createElement('option');
            option.value = plan.id;
            option.textContent = `${plan.name} - ${plan.duration_days} روز - ${plan.data_limit_gb} GB - ${plan.credit_cost} کریدیت`;
            planSelect.appendChild(option);
        });

        M.FormSelect.init(document.querySelectorAll('select'));

    } catch (error) {
        console.error('Error loading service plans:', error);
        M.toast({ html: 'خطا در بارگذاری پلن‌ها', classes: 'red' });
    }
}

async function loadAccounts() {
    try {
        showLoading(true);
        currentAccounts = await api.getAccounts();
        displayAccounts(currentAccounts);
    } catch (error) {
        console.error('Error loading accounts:', error);
        M.toast({ html: 'خطا در بارگذاری اکانت‌ها: ' + error.message, classes: 'red' });
    } finally {
        showLoading(false);
    }
}

function displayAccounts(accounts) {
    const tbody = document.getElementById('accountsTableBody');
    tbody.innerHTML = '';

    if (!accounts || accounts.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="center-align grey-text">
                    هیچ اکانتی یافت نشد
                </td>
            </tr>
        `;
        return;
    }

    accounts.forEach(account => {
        const row = document.createElement('tr');

        // محاسبه وضعیت
        const status = getAccountStatus(account);
        const statusBadge = getStatusBadge(status);

        // محاسبه مصرف
        const usedGB = ((account.data_limit_gb - account.data_remaining_gb) || 0).toFixed(2);
        const totalGB = (account.data_limit_gb || 0).toFixed(2);
        const usagePercent = account.data_limit_gb > 0 ? ((usedGB / totalGB) * 100).toFixed(0) : 0;

        // تاریخ انقضا
        const expireDate = account.expire_at ? new Date(account.expire_at).toLocaleDateString('fa-IR') : '-';

        // دکمه‌های عملیات
        const actions = `
            <button class="btn-action btn-small waves-effect waves-light blue tooltipped"
                    data-position="top" data-tooltip="تمدید"
                    onclick="openRenewModal(${account.id}, '${account.username}')">
                <i class="material-icons tiny">update</i>
            </button>
            <button class="btn-action btn-small waves-effect waves-light purple tooltipped"
                    data-position="top" data-tooltip="افزودن حجم"
                    onclick="openAddTrafficModal(${account.id}, '${account.username}')">
                <i class="material-icons tiny">add_circle</i>
            </button>
            <button class="btn-action btn-small waves-effect waves-light ${account.is_enabled ? 'orange' : 'green'} tooltipped"
                    data-position="top" data-tooltip="${account.is_enabled ? 'غیرفعال کردن' : 'فعال کردن'}"
                    onclick="toggleAccountStatus(${account.id}, ${!account.is_enabled})">
                <i class="material-icons tiny">${account.is_enabled ? 'pause' : 'play_arrow'}</i>
            </button>
            <button class="btn-action btn-small waves-effect waves-light teal tooltipped"
                    data-position="top" data-tooltip="همگام‌سازی"
                    onclick="syncAccount(${account.id})">
                <i class="material-icons tiny">sync</i>
            </button>
            <button class="btn-action btn-small waves-effect waves-light red tooltipped"
                    data-position="top" data-tooltip="حذف"
                    onclick="deleteAccount(${account.id}, '${account.username}')">
                <i class="material-icons tiny">delete</i>
            </button>
        `;

        row.innerHTML = `
            <td><strong>${account.username}</strong>${account.description ? '<br><small class="grey-text">' + account.description + '</small>' : ''}</td>
            <td>${getProductName(account.product_id)}</td>
            <td>${statusBadge}</td>
            <td>
                <div class="progress" style="height: 20px; border-radius: 5px;">
                    <div class="determinate" style="width: ${usagePercent}%"></div>
                </div>
                <small>${usedGB} / ${totalGB} GB (${usagePercent}%)</small>
            </td>
            <td>${expireDate}</td>
            <td>${actions}</td>
        `;

        tbody.appendChild(row);
    });

    // Initialize tooltips
    M.Tooltip.init(document.querySelectorAll('.tooltipped'));
}

function getAccountStatus(account) {
    if (!account.is_enabled) return 'disabled';

    const now = new Date();
    const expireDate = new Date(account.expire_at);

    if (expireDate < now) return 'expired';
    if (account.data_remaining_gb <= 0) return 'expired';

    return 'active';
}

function getStatusBadge(status) {
    const badges = {
        'active': '<span class="badge badge-active">فعال</span>',
        'expired': '<span class="badge badge-expired">منقضی شده</span>',
        'disabled': '<span class="badge badge-inactive">غیرفعال</span>'
    };
    return badges[status] || status;
}

function getProductName(productId) {
    const product = products.find(p => p.id === productId);
    return product ? product.name : 'نامشخص';
}

function filterAccounts() {
    const productFilter = document.getElementById('productFilter').value;
    const statusFilter = document.getElementById('statusFilter').value;
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();

    let filtered = currentAccounts;

    // فیلتر محصول
    if (productFilter) {
        filtered = filtered.filter(acc => acc.product_id == productFilter);
    }

    // فیلتر وضعیت
    if (statusFilter) {
        filtered = filtered.filter(acc => getAccountStatus(acc) === statusFilter);
    }

    // جستجو
    if (searchTerm) {
        filtered = filtered.filter(acc =>
            acc.username.toLowerCase().includes(searchTerm) ||
            (acc.description && acc.description.toLowerCase().includes(searchTerm))
        );
    }

    displayAccounts(filtered);
}

// ==================== Modal Functions ====================

function openCreateModal() {
    modals.create.open();
    M.updateTextFields();
}

function closeCreateModal() {
    modals.create.close();
    document.getElementById('createAccountForm').reset();
}

function openRenewModal(accountId, username) {
    currentAccountId = accountId;
    document.getElementById('renewAccountUsername').textContent = username;
    modals.renew.open();
    M.updateTextFields();
}

function closeRenewModal() {
    modals.renew.close();
    document.getElementById('renewForm').reset();
    currentAccountId = null;
}

function openAddTrafficModal(accountId, username) {
    currentAccountId = accountId;
    document.getElementById('trafficAccountUsername').textContent = username;
    modals.addTraffic.open();
    M.updateTextFields();
}

function closeAddTrafficModal() {
    modals.addTraffic.close();
    document.getElementById('addTrafficForm').reset();
    currentAccountId = null;
}

// ==================== Account Operations ====================

async function createAccount() {
    const username = document.getElementById('newUsername').value.trim();
    const productId = parseInt(document.getElementById('newProduct').value);
    const servicePlanId = parseInt(document.getElementById('newServicePlan').value);
    const description = document.getElementById('newDescription').value.trim();
    const autoRenew = document.getElementById('autoRenewCheck').checked;

    if (!username || !productId || !servicePlanId) {
        M.toast({ html: 'لطفاً تمام فیلدهای الزامی را پر کنید', classes: 'red' });
        return;
    }

    try {
        showLoading(true);

        const data = {
            username,
            product_id: productId,
            service_plan_id: servicePlanId,
            description: description || null,
            auto_renew: autoRenew
        };

        await api.createAccount(data);

        M.toast({ html: 'اکانت با موفقیت ایجاد شد', classes: 'green' });
        closeCreateModal();
        await loadAccounts();
        await loadCreditBalance();

    } catch (error) {
        console.error('Error creating account:', error);
        M.toast({ html: 'خطا در ایجاد اکانت: ' + error.message, classes: 'red' });
    } finally {
        showLoading(false);
    }
}

async function renewAccount() {
    const days = parseInt(document.getElementById('renewDays').value);

    if (!days || days < 1) {
        M.toast({ html: 'لطفاً تعداد روز معتبر وارد کنید', classes: 'red' });
        return;
    }

    try {
        showLoading(true);
        await api.renewAccount(currentAccountId, days);

        M.toast({ html: 'اکانت با موفقیت تمدید شد', classes: 'green' });
        closeRenewModal();
        await loadAccounts();
        await loadCreditBalance();

    } catch (error) {
        console.error('Error renewing account:', error);
        M.toast({ html: 'خطا در تمدید اکانت: ' + error.message, classes: 'red' });
    } finally {
        showLoading(false);
    }
}

async function addTraffic() {
    const gb = parseInt(document.getElementById('trafficGB').value);

    if (!gb || gb < 1) {
        M.toast({ html: 'لطفاً مقدار حجم معتبر وارد کنید', classes: 'red' });
        return;
    }

    try {
        showLoading(true);
        await api.addTraffic(currentAccountId, gb);

        M.toast({ html: 'حجم با موفقیت اضافه شد', classes: 'green' });
        closeAddTrafficModal();
        await loadAccounts();
        await loadCreditBalance();

    } catch (error) {
        console.error('Error adding traffic:', error);
        M.toast({ html: 'خطا در افزودن حجم: ' + error.message, classes: 'red' });
    } finally {
        showLoading(false);
    }
}

async function toggleAccountStatus(accountId, enabled) {
    const action = enabled ? 'فعال' : 'غیرفعال';

    if (!confirm(`آیا مطمئن هستید که می‌خواهید این اکانت را ${action} کنید؟`)) {
        return;
    }

    try {
        showLoading(true);
        await api.toggleStatus(accountId, enabled);

        M.toast({ html: `اکانت با موفقیت ${action} شد`, classes: 'green' });
        await loadAccounts();

    } catch (error) {
        console.error('Error toggling status:', error);
        M.toast({ html: `خطا در ${action} کردن اکانت: ` + error.message, classes: 'red' });
    } finally {
        showLoading(false);
    }
}

async function syncAccount(accountId) {
    try {
        showLoading(true);
        await api.syncAccount(accountId);

        M.toast({ html: 'اکانت با موفقیت همگام‌سازی شد', classes: 'green' });
        await loadAccounts();

    } catch (error) {
        console.error('Error syncing account:', error);
        M.toast({ html: 'خطا در همگام‌سازی: ' + error.message, classes: 'red' });
    } finally {
        showLoading(false);
    }
}

async function deleteAccount(accountId, username) {
    if (!confirm(`آیا مطمئن هستید که می‌خواهید اکانت "${username}" را حذف کنید؟\n\nتوجه: کریدیت استفاده شده برگشت داده خواهد شد.`)) {
        return;
    }

    try {
        showLoading(true);
        await api.deleteAccount(accountId);

        M.toast({ html: 'اکانت با موفقیت حذف شد', classes: 'green' });
        await loadAccounts();
        await loadCreditBalance();

    } catch (error) {
        console.error('Error deleting account:', error);
        M.toast({ html: 'خطا در حذف اکانت: ' + error.message, classes: 'red' });
    } finally {
        showLoading(false);
    }
}

// ==================== Utility Functions ====================

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
