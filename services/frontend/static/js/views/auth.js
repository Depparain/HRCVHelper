// Auth and Navigation View Controller
import { state } from '../state.js';
import { api } from '../api.js';

export function togglePassVisibility() {
  const p = document.getElementById('input-password');
  const icon = document.getElementById('eye-icon');
  if (p.type === 'password') {
    p.type = 'text';
    icon.textContent = 'visibility_off';
  } else {
    p.type = 'password';
    icon.textContent = 'visibility';
  }
}

export async function handleLogin(e) {
  if (e) e.preventDefault();
  const loginInput = document.getElementById('input-login').value.trim();
  const passInput = document.getElementById('input-password').value.trim();
  const btn = document.getElementById('login-btn');
  const errBox = document.getElementById('login-error');

  btn.disabled = true;
  btn.innerHTML = `<span class="material-symbols-outlined text-[18px] animate-spin">sync</span><span>Авторизация...</span>`;
  errBox.classList.add('hidden');

  try {
    const data = await api.login(loginInput, passInput);
    state.setToken(data.access_token);
    state.setUser(data.user);

    showDashboard();
  } catch (err) {
    document.getElementById('login-error-msg').textContent = err.message;
    errBox.classList.remove('hidden');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span>Войти</span><span class="material-symbols-outlined text-[18px]">arrow_forward</span>`;
  }
}

export function logout() {
  state.setToken(null);
  state.setUser(null);
  if (state.adminInterval) clearInterval(state.adminInterval);
  if (state.dashboardPollInterval) clearInterval(state.dashboardPollInterval);
  showLogin();
}

export function hideAllViews() {
  ['view-login', 'view-dashboard', 'view-validation', 'view-result', 'view-admin', 'view-templates'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.add('hidden');
  });
  if (state.adminInterval) {
    clearInterval(state.adminInterval);
    state.adminInterval = null;
  }
}

export function showLogin() {
  hideAllViews();
  document.getElementById('main-header').classList.add('hidden');
  document.getElementById('view-login').classList.remove('hidden');
}

export function showDashboard() {
  hideAllViews();
  document.getElementById('main-header').classList.remove('hidden');
  document.getElementById('view-dashboard').classList.remove('hidden');
  updateNavActive('nav-cv');

  if (state.currentUser) {
    document.getElementById('user-name').textContent = state.currentUser.full_name || 'HR Lead';
    const initials = (state.currentUser.full_name || 'HR').split(' ').map(s => s[0]).slice(0, 2).join('');
    document.getElementById('user-avatar').textContent = initials;
  }

  if (window.loadCVs) {
    window.loadCVs();
  }

  // Auto-polling dashboard every 4 seconds
  if (!state.dashboardPollInterval) {
    state.dashboardPollInterval = setInterval(() => {
      const dashboard = document.getElementById('view-dashboard');
      if (dashboard && !dashboard.classList.contains('hidden') && window.loadCVs) {
        window.loadCVs(true);
      }
    }, 4000);
  }
}

export function showTemplates() {
  hideAllViews();
  document.getElementById('main-header').classList.remove('hidden');
  document.getElementById('view-templates').classList.remove('hidden');
  updateNavActive('nav-templates');
  if (window.loadTemplatesData) {
    window.loadTemplatesData();
  }
}

export function showAdmin() {
  hideAllViews();
  document.getElementById('main-header').classList.remove('hidden');
  document.getElementById('view-admin').classList.remove('hidden');
  updateNavActive('nav-admin');
  if (window.loadAdminData) {
    window.loadAdminData();
  }
  if (state.adminAutoRefresh) {
    state.adminInterval = setInterval(() => {
      if (window.loadAdminData) window.loadAdminData();
    }, 5000);
  }
}

export function updateNavActive(activeId) {
  ['nav-cv', 'nav-templates', 'nav-admin'].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    if (id === activeId) {
      el.className = 'py-5 text-secondary border-b-2 border-secondary font-semibold flex items-center gap-1.5';
    } else {
      el.className = 'py-5 text-text-muted hover:text-text-primary transition-colors flex items-center gap-1.5';
    }
  });
}
