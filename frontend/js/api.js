/**
 * API Client
 * مدیریت تمام درخواست‌های API
 */

const API_BASE_URL = 'http://localhost:8000/api';

class APIClient {
    constructor() {
        this.token = localStorage.getItem('access_token');
        this.user = JSON.parse(localStorage.getItem('user') || 'null');
    }

    /**
     * تنظیم token بعد از login
     */
    setAuth(token, user) {
        this.token = token;
        this.user = user;
        localStorage.setItem('access_token', token);
        localStorage.setItem('user', JSON.stringify(user));
    }

    /**
     * پاک کردن اطلاعات احراز هویت
     */
    clearAuth() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
    }

    /**
     * ارسال درخواست به API
     */
    async request(method, endpoint, data = null) {
        const url = `${API_BASE_URL}${endpoint}`;

        const headers = {
            'Content-Type': 'application/json',
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        const config = {
            method,
            headers,
        };

        if (data) {
            config.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, config);

            if (response.status === 401) {
                // Token منقضی شده
                this.clearAuth();
                window.location.href = '/';
                throw new Error('لطفاً دوباره وارد شوید');
            }

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || 'خطا در ارتباط با سرور');
            }

            return result;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // ==================== Authentication ====================

    async login(username, password) {
        const result = await this.request('POST', '/auth/login', { username, password });
        this.setAuth(result.access_token, result.user);
        return result;
    }

    async logout() {
        await this.request('POST', '/auth/logout');
        this.clearAuth();
    }

    async getMe() {
        return await this.request('GET', '/auth/me');
    }

    // ==================== Reseller - Credit ====================

    async getCreditBalance() {
        return await this.request('GET', '/reseller/credit/balance');
    }

    async getCreditTransactions(skip = 0, limit = 100) {
        return await this.request('GET', `/reseller/credit/transactions?skip=${skip}&limit=${limit}`);
    }

    // ==================== Reseller - Accounts ====================

    async getAccounts(params = {}) {
        const queryParams = new URLSearchParams(params).toString();
        return await this.request('GET', `/reseller/accounts?${queryParams}`);
    }

    async createAccount(data) {
        return await this.request('POST', '/reseller/accounts', data);
    }

    async getAccount(id) {
        return await this.request('GET', `/reseller/accounts/${id}`);
    }

    async deleteAccount(id) {
        return await this.request('DELETE', `/reseller/accounts/${id}`);
    }

    async renewAccount(id, days) {
        return await this.request('POST', `/reseller/accounts/${id}/renew`, { days });
    }

    async addTraffic(id, gb) {
        return await this.request('POST', `/reseller/accounts/${id}/add-traffic`, { gb });
    }

    async toggleStatus(id, enabled) {
        return await this.request('POST', `/reseller/accounts/${id}/toggle-status`, { enabled });
    }

    async syncAccount(id) {
        return await this.request('POST', `/reseller/accounts/${id}/sync`);
    }

    // ==================== Reseller - Stats ====================

    async getOverviewStats() {
        return await this.request('GET', '/reseller/stats/overview');
    }

    // ==================== Admin - Products ====================

    async getProducts() {
        return await this.request('GET', '/admin/products');
    }

    async createProduct(data) {
        return await this.request('POST', '/admin/products', data);
    }

    // ==================== Admin - Service Plans ====================

    async getServicePlans(productId = null) {
        const url = productId ? `/admin/service-plans?product_id=${productId}` : '/admin/service-plans';
        return await this.request('GET', url);
    }

    // ==================== Admin - Resellers ====================

    async getResellers() {
        return await this.request('GET', '/admin/resellers');
    }

    async createReseller(data) {
        return await this.request('POST', '/admin/resellers', data);
    }

    // ==================== Admin - Credit ====================

    async addCredit(resellerId, amount, note = null) {
        return await this.request('POST', '/admin/credit/add', {
            reseller_id: resellerId,
            amount,
            admin_note: note
        });
    }
}

// Instance واحد
const api = new APIClient();
