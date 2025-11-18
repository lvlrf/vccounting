/**
 * Profile Page Script
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
    await loadProfileData();

    // Event listener برای فرم تغییر رمز
    document.getElementById('changePasswordForm').addEventListener('submit', handleChangePassword);
});

async function loadProfileData() {
    try {
        showLoading(true);

        // دریافت موجودی کریدیت
        const creditBalance = await api.getCreditBalance();
        document.getElementById('creditBalance').textContent = creditBalance.balance.toLocaleString('fa-IR');

        // دریافت اطلاعات کاربر
        const userInfo = await api.getMe();

        // نمایش اطلاعات پروفایل
        document.getElementById('profileFullName').textContent = userInfo.full_name || '-';
        document.getElementById('profileUsername').textContent = userInfo.username;
        document.getElementById('profileEmail').textContent = userInfo.email || '-';
        document.getElementById('profilePhone').textContent = userInfo.phone_number || '-';

        const statusBadge = userInfo.is_active
            ? '<span class="badge green white-text">فعال</span>'
            : '<span class="badge red white-text">غیرفعال</span>';
        document.getElementById('profileStatus').innerHTML = statusBadge;

        const createdDate = new Date(userInfo.created_at);
        document.getElementById('profileCreatedAt').textContent = createdDate.toLocaleDateString('fa-IR');

        // دریافت آمار
        const stats = await api.getOverviewStats();
        document.getElementById('activeAccountsCount').textContent = stats.active_accounts.toLocaleString('fa-IR');
        document.getElementById('expiredAccountsCount').textContent = stats.expired_accounts.toLocaleString('fa-IR');
        document.getElementById('totalAccountsCount').textContent = stats.total_accounts_created.toLocaleString('fa-IR');
        document.getElementById('spentCreditCount').textContent = stats.total_credit_spent.toLocaleString('fa-IR');

    } catch (error) {
        console.error('Error loading profile:', error);
        M.toast({ html: 'خطا در بارگذاری اطلاعات: ' + error.message, classes: 'red' });
    } finally {
        showLoading(false);
    }
}

async function handleChangePassword(e) {
    e.preventDefault();

    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    // اعتبارسنجی
    if (newPassword.length < 6) {
        M.toast({ html: 'رمز عبور جدید باید حداقل 6 کاراکتر باشد', classes: 'red' });
        return;
    }

    if (newPassword !== confirmPassword) {
        M.toast({ html: 'رمز عبور جدید و تکرار آن یکسان نیستند', classes: 'red' });
        return;
    }

    if (currentPassword === newPassword) {
        M.toast({ html: 'رمز عبور جدید نباید با رمز فعلی یکسان باشد', classes: 'red' });
        return;
    }

    try {
        showLoading(true);

        await api.request('POST', '/auth/change-password', {
            current_password: currentPassword,
            new_password: newPassword
        });

        M.toast({ html: 'رمز عبور با موفقیت تغییر کرد', classes: 'green' });

        // پاک کردن فرم
        document.getElementById('changePasswordForm').reset();

    } catch (error) {
        console.error('Error changing password:', error);
        M.toast({ html: 'خطا در تغییر رمز عبور: ' + error.message, classes: 'red' });
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
