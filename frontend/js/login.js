/**
 * Login Page Script
 */

document.addEventListener('DOMContentLoaded', function() {
    // بررسی اینکه آیا کاربر قبلاً login کرده
    if (api.token) {
        redirectToDashboard();
        return;
    }

    const loginForm = document.getElementById('loginForm');
    const errorDiv = document.getElementById('loginError');
    const errorMessage = document.getElementById('errorMessage');

    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        // مخفی کردن خطای قبلی
        errorDiv.style.display = 'none';

        try {
            showLoading(true);

            const result = await api.login(username, password);

            // موفقیت
            M.toast({ html: 'ورود موفقیت‌آمیز بود!', classes: 'green' });

            // هدایت به داشبورد مناسب
            setTimeout(() => {
                redirectToDashboard();
            }, 500);

        } catch (error) {
            errorMessage.textContent = error.message;
            errorDiv.style.display = 'block';
            M.toast({ html: 'خطا در ورود', classes: 'red' });
        } finally {
            showLoading(false);
        }
    });
});

function redirectToDashboard() {
    if (api.user && api.user.role === 'admin') {
        window.location.href = '/pages/admin/dashboard.html';
    } else {
        window.location.href = '/pages/reseller/dashboard.html';
    }
}

function showLoading(show) {
    // می‌توان یک loading overlay اضافه کرد
    const submitBtn = document.querySelector('button[type="submit"]');
    if (show) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="material-icons left">hourglass_empty</i>در حال ورود...';
    } else {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'ورود<i class="material-icons left">send</i>';
    }
}
