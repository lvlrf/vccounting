/**
 * Admin Resellers Management Script
 */

let resellers = [];
let currentResellerId = null;
let modals = {};

document.addEventListener('DOMContentLoaded', async function() {
    // بررسی authentication
    if (!api.token || !api.user || api.user.role !== 'admin') {
        window.location.href = '/';
        return;
    }

    // نمایش اطلاعات کاربر
    document.getElementById('userFullName').textContent = api.user.full_name || 'مدیر سیستم';
    document.getElementById('userUsername').textContent = `@${api.user.username}`;

    // Initialize modals
    modals.create = M.Modal.init(document.getElementById('createResellerModal'));
    modals.addCredit = M.Modal.init(document.getElementById('addCreditModal'));

    // بارگذاری نمایندگان
    await loadResellers();

    // بررسی query parameter
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('action') === 'create') {
        openCreateModal();
    }
});

async function loadResellers() {
    try {
        showLoading(true);
        resellers = await api.getResellers();
        displayResellers(resellers);
    } catch (error) {
        console.error('Error loading resellers:', error);
        M.toast({ html: 'خطا در بارگذاری نمایندگان: ' + error.message, classes: 'red' });
    } finally {
        showLoading(false);
    }
}

function displayResellers(resellers) {
    const tbody = document.getElementById('resellersTableBody');
    tbody.innerHTML = '';

    if (!resellers || resellers.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="center-align grey-text">
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

        const actions = `
            <button class="btn-action btn-small waves-effect waves-light green tooltipped"
                    data-position="top" data-tooltip="افزودن کریدیت"
                    onclick="openAddCreditModal(${reseller.id}, '${reseller.full_name || reseller.username}')">
                <i class="material-icons tiny">add</i>
            </button>
            <button class="btn-action btn-small waves-effect waves-light ${reseller.is_active ? 'orange' : 'teal'} tooltipped"
                    data-position="top" data-tooltip="${reseller.is_active ? 'غیرفعال کردن' : 'فعال کردن'}"
                    onclick="toggleResellerStatus(${reseller.id}, ${!reseller.is_active})">
                <i class="material-icons tiny">${reseller.is_active ? 'block' : 'check'}</i>
            </button>
        `;

        row.innerHTML = `
            <td><strong>${reseller.full_name || '-'}</strong></td>
            <td>${reseller.username}</td>
            <td>${reseller.email || '-'}</td>
            <td><strong class="teal-text">${(reseller.credit_balance || 0).toLocaleString('fa-IR')}</strong></td>
            <td>${statusBadge}</td>
            <td>${actions}</td>
        `;

        tbody.appendChild(row);
    });

    M.Tooltip.init(document.querySelectorAll('.tooltipped'));
}

function openCreateModal() {
    modals.create.open();
    M.updateTextFields();
}

function closeCreateModal() {
    modals.create.close();
    document.getElementById('createResellerForm').reset();
}

async function createReseller() {
    const username = document.getElementById('newUsername').value.trim();
    const password = document.getElementById('newPassword').value;
    const fullName = document.getElementById('newFullName').value.trim();
    const email = document.getElementById('newEmail').value.trim();
    const phone = document.getElementById('newPhone').value.trim();
    const initialCredit = parseInt(document.getElementById('initialCredit').value) || 0;

    if (!username || !password || !fullName) {
        M.toast({ html: 'لطفاً تمام فیلدهای الزامی را پر کنید', classes: 'red' });
        return;
    }

    if (password.length < 6) {
        M.toast({ html: 'رمز عبور باید حداقل 6 کاراکتر باشد', classes: 'red' });
        return;
    }

    try {
        showLoading(true);

        const data = {
            username,
            password,
            full_name: fullName,
            email: email || null,
            phone_number: phone || null,
            initial_credit: initialCredit
        };

        await api.createReseller(data);

        M.toast({ html: 'نماینده با موفقیت ایجاد شد', classes: 'green' });
        closeCreateModal();
        await loadResellers();

    } catch (error) {
        console.error('Error creating reseller:', error);
        M.toast({ html: 'خطا در ایجاد نماینده: ' + error.message, classes: 'red' });
    } finally {
        showLoading(false);
    }
}

function openAddCreditModal(resellerId, resellerName) {
    currentResellerId = resellerId;
    document.getElementById('creditResellerName').textContent = resellerName;
    modals.addCredit.open();
    M.updateTextFields();
}

function closeAddCreditModal() {
    modals.addCredit.close();
    document.getElementById('addCreditForm').reset();
    currentResellerId = null;
}

async function addCredit() {
    const amount = parseInt(document.getElementById('creditAmount').value);
    const note = document.getElementById('creditNote').value.trim();

    if (!amount || amount < 1) {
        M.toast({ html: 'لطفاً مقدار معتبر وارد کنید', classes: 'red' });
        return;
    }

    try {
        showLoading(true);

        await api.addCredit(currentResellerId, amount, note || null);

        M.toast({ html: 'کریدیت با موفقیت اضافه شد', classes: 'green' });
        closeAddCreditModal();
        await loadResellers();

    } catch (error) {
        console.error('Error adding credit:', error);
        M.toast({ html: 'خطا در افزودن کریدیت: ' + error.message, classes: 'red' });
    } finally {
        showLoading(false);
    }
}

async function toggleResellerStatus(resellerId, newStatus) {
    const action = newStatus ? 'فعال' : 'غیرفعال';

    if (!confirm(`آیا مطمئن هستید که می‌خواهید این نماینده را ${action} کنید؟`)) {
        return;
    }

    try {
        showLoading(true);

        // TODO: اضافه کردن endpoint برای تغییر وضعیت نماینده
        // await api.toggleResellerStatus(resellerId, newStatus);

        M.toast({ html: `نماینده با موفقیت ${action} شد`, classes: 'green' });
        await loadResellers();

    } catch (error) {
        console.error('Error toggling status:', error);
        M.toast({ html: `خطا در ${action} کردن: ` + error.message, classes: 'red' });
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
