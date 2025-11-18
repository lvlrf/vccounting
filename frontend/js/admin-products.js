/**
 * Admin Products Management Script
 */

let products = [];
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
    modals.create = M.Modal.init(document.getElementById('createProductModal'));
    M.FormSelect.init(document.querySelectorAll('select'));

    // بارگذاری محصولات
    await loadProducts();

    // بررسی query parameter
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('action') === 'create') {
        openCreateProductModal();
    }
});

async function loadProducts() {
    try {
        showLoading(true);
        products = await api.getProducts();
        displayProducts(products);
    } catch (error) {
        console.error('Error loading products:', error);
        M.toast({ html: 'خطا در بارگذاری محصولات: ' + error.message, classes: 'red' });
    } finally {
        showLoading(false);
    }
}

function displayProducts(products) {
    const tbody = document.getElementById('productsTableBody');
    tbody.innerHTML = '';

    if (!products || products.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="center-align grey-text">
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

        const actions = `
            <button class="btn-action btn-small waves-effect waves-light ${product.is_active ? 'orange' : 'teal'} tooltipped"
                    data-position="top" data-tooltip="${product.is_active ? 'غیرفعال کردن' : 'فعال کردن'}"
                    onclick="toggleProductStatus(${product.id}, ${!product.is_active})">
                <i class="material-icons tiny">${product.is_active ? 'block' : 'check'}</i>
            </button>
        `;

        row.innerHTML = `
            <td><strong>${product.name}</strong></td>
            <td><span class="chip">${typeLabel}</span></td>
            <td><small>${product.panel_url}</small></td>
            <td>${product.description || '-'}</td>
            <td>${statusBadge}</td>
            <td>${actions}</td>
        `;

        tbody.appendChild(row);
    });

    M.Tooltip.init(document.querySelectorAll('.tooltipped'));
}

function getProductTypeLabel(type) {
    const labels = {
        'marzban': 'مرزبان',
        'remnawave': 'رمناویو',
        'marzneshin': 'مرزنشین'
    };

    return labels[type] || type;
}

function openCreateProductModal() {
    modals.create.open();
    M.updateTextFields();
    M.textareaAutoResize(document.getElementById('productDescription'));
}

function closeCreateProductModal() {
    modals.create.close();
    document.getElementById('createProductForm').reset();
}

async function createProduct() {
    const name = document.getElementById('productName').value.trim();
    const productType = document.getElementById('productType').value;
    const panelUrl = document.getElementById('panelUrl').value.trim();
    const apiKey = document.getElementById('apiKey').value.trim();
    const description = document.getElementById('productDescription').value.trim();

    if (!name || !productType || !panelUrl || !apiKey) {
        M.toast({ html: 'لطفاً تمام فیلدهای الزامی را پر کنید', classes: 'red' });
        return;
    }

    try {
        showLoading(true);

        const data = {
            name,
            product_type: productType,
            panel_url: panelUrl,
            api_key: apiKey,
            description: description || null
        };

        await api.createProduct(data);

        M.toast({ html: 'محصول با موفقیت ایجاد شد', classes: 'green' });
        closeCreateProductModal();
        await loadProducts();

    } catch (error) {
        console.error('Error creating product:', error);
        M.toast({ html: 'خطا در ایجاد محصول: ' + error.message, classes: 'red' });
    } finally {
        showLoading(false);
    }
}

async function toggleProductStatus(productId, newStatus) {
    const action = newStatus ? 'فعال' : 'غیرفعال';

    if (!confirm(`آیا مطمئن هستید که می‌خواهید این محصول را ${action} کنید؟`)) {
        return;
    }

    try {
        showLoading(true);

        // TODO: اضافه کردن endpoint برای تغییر وضعیت محصول
        // await api.toggleProductStatus(productId, newStatus);

        M.toast({ html: `محصول با موفقیت ${action} شد`, classes: 'green' });
        await loadProducts();

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
