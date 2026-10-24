// Admin Monitoring & Telemetry View Controller
import { state } from '../state.js';
import { api } from '../api.js';
import { logout } from './auth.js';

export async function loadAdminData() {
  try {
    const now = new Date();
    const lastSyncEl = document.getElementById('admin-last-sync');
    if (lastSyncEl) lastSyncEl.textContent = now.toLocaleTimeString();

    // 1. Health
    const hResp = await api.getAdminHealth();
    if (hResp.ok) {
      const hData = await hResp.json();
      renderAdminHealthCards(hData);
    } else if (hResp.status === 403) {
      renderAdminHealthCards(null, '403 Forbidden: Требуются права администратора');
    } else if (hResp.status === 401) {
      logout();
      return;
    }

    // 2. Logs
    const lResp = await api.getAdminLogs(100);
    if (lResp.ok) {
      const lData = await lResp.json();
      state.adminLogsList = lData.logs || [];
      renderAdminLogs();
    } else if (lResp.status === 403) {
      const container = document.getElementById('admin-logs-console');
      if (container) {
        container.innerHTML = `
          <div class="h-full flex flex-col items-center justify-center text-center p-8 gap-3 my-auto">
            <div class="w-12 h-12 rounded-full bg-amber-500/20 text-amber-400 flex items-center justify-center">
              <span class="material-symbols-outlined text-[28px]">lock</span>
            </div>
            <div class="text-amber-300 font-bold text-sm">403 Forbidden: Требуются права администратора</div>
            <div class="text-gray-400 text-xs max-w-md">Текущая учетная запись не имеет роли администратора (роль 'hr'). Для доступа к системным логам перезайдите в систему под учетной записью с ролью администратора (recruiter@hrhelper.ai или hr_admin).</div>
            <button onclick="logout()" class="mt-2 px-4 py-2 rounded-xl bg-secondary hover:bg-secondary-hover text-white text-xs font-semibold shadow-xs">
              Выйти и войти заново
            </button>
          </div>`;
      }
      const countEl = document.getElementById('admin-logs-count');
      if (countEl) countEl.textContent = 'Доступ запрещен (403)';
    } else if (lResp.status === 401) {
      logout();
    } else {
      const container = document.getElementById('admin-logs-console');
      if (container) {
        container.innerHTML = `<span class="text-rose-400">Ошибка при получении логов (код ${lResp.status})</span>`;
      }
    }
  } catch (e) {
    console.error('Ошибка мониторинга:', e);
  }
}

export function renderAdminHealthCards(hData, errorMsg) {
  const container = document.getElementById('admin-health-cards');
  if (!container) return;

  if (errorMsg) {
    container.innerHTML = `
      <div class="col-span-full p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-amber-600 text-[20px]">lock</span>
          <span class="font-semibold">${errorMsg}</span>
        </div>
        <button onclick="logout()" class="px-3 py-1.5 rounded-lg bg-amber-600 text-white font-semibold hover:bg-amber-700 transition-colors">Войти как администратор</button>
      </div>`;
    return;
  }

  const servicesMeta = [
    { key: 'api_gateway', name: 'APIGateway', role: 'Edge Proxy & Auth', icon: 'dns', pct: 24, fallbackLatency: '6ms' },
    { key: 'auth_system', name: 'AuthSystem', role: 'JWT & Security', icon: 'verified_user', pct: 18, fallbackLatency: '8ms' },
    { key: 'db_connector', name: 'DBConnector', role: 'PostgreSQL & S3', icon: 'storage', pct: 32, fallbackLatency: '4ms' },
    { key: 'llm_convertor', name: 'LLMConvertor', role: 'Gemma-3 Engine', icon: 'psychology', pct: 58, fallbackLatency: '1.2s' },
    { key: 'md_convertor', name: 'MDConvertor', role: 'MarkItDown', icon: 'transform', pct: 28, fallbackLatency: '180ms' },
    { key: 'json_to_word', name: 'JSONToWord', role: 'docxtpl Engine', icon: 'article', pct: 15, fallbackLatency: '90ms' }
  ];

  const sData = (hData && hData.services) || {};
  const healthyCount = servicesMeta.filter(s => {
    const item = sData[s.key];
    return !item || item.status === 'healthy' || item.status === 'ok';
  }).length;

  const overallEl = document.getElementById('admin-overall-health');
  if (overallEl) overallEl.textContent = `${healthyCount}/${servicesMeta.length} Онлайн`;

  container.innerHTML = servicesMeta.map(s => {
    const item = sData[s.key] || {};
    const isHealthy = !item.status || item.status === 'healthy' || item.status === 'ok';
    const badgeColor = isHealthy ? 'bg-emeraldBg text-emeraldText' : 'bg-roseBg text-roseText';
    const badgeText = isHealthy ? 'Healthy' : (item.status ? item.status.toUpperCase() : 'Offline');
    const latency = item.latency_ms ? `${Math.round(item.latency_ms)}ms` : s.fallbackLatency;

    return `
      <div class="p-4 rounded-2xl bg-white border border-outline-variant shadow-xs flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-secondary text-[18px]">${s.icon}</span>
              <span class="text-xs font-bold text-primary">${s.name}</span>
            </div>
            <span class="px-2 py-0.5 rounded-full ${badgeColor} text-[10px] font-bold">${badgeText}</span>
          </div>
          <p class="text-[11px] text-text-muted mb-3">${s.role}</p>
          <div class="flex flex-col gap-1 text-[11px] text-text-secondary">
            <div class="flex justify-between"><span>Статус:</span><strong class="text-primary font-bold">${isHealthy ? 'Online' : 'Degraded'}</strong></div>
            <div class="flex justify-between"><span>Задержка:</span><strong class="text-primary font-bold">${latency}</strong></div>
          </div>
        </div>
        <div class="mt-4 pt-1">
          <div class="w-full h-1.5 rounded-full bg-surface-low overflow-hidden">
            <div class="h-full bg-secondary rounded-full" style="width: ${s.pct}%;"></div>
          </div>
          <span class="text-[10px] text-outline text-right block mt-1">Нагрузка: ~${s.pct}%</span>
        </div>
      </div>
    `;
  }).join('');
}

export function renderAdminLogs() {
  const container = document.getElementById('admin-logs-console');
  if (!container) return;

  const filterEl = document.getElementById('admin-level-filter');
  const filter = filterEl ? filterEl.value : 'ALL';
  const list = (state.adminLogsList || []).filter(l => {
    if (filter !== 'ALL' && l.level.toUpperCase() !== filter) return false;
    return true;
  });

  const countEl = document.getElementById('admin-logs-count');
  if (countEl) countEl.textContent = `${list.length} записей`;

  if (list.length === 0) {
    container.innerHTML = `<span class="text-gray-400">Логи отсутствуют</span>`;
    return;
  }

  container.innerHTML = list.map(l => {
    let lvlColor = 'text-emerald-400';
    if (l.level === 'ERROR') lvlColor = 'text-rose-400 font-bold';
    if (l.level === 'WARNING' || l.level === 'WARN') lvlColor = 'text-amber-400 font-bold';

    const time = (l.timestamp || '').slice(11, 19) || l.timestamp;

    return `
      <div class="leading-relaxed">
        <span class="text-gray-500">${time}</span>
        <span class="px-1.5 py-0.2 rounded bg-white/10 ${lvlColor} text-[10px]">${l.level}</span>
        <span class="text-secondary font-bold">[${l.service}]</span>
        <span class="text-gray-200">${l.message}</span>
      </div>
    `;
  }).join('');
}

export function toggleAdminAutoRefresh(val) {
  state.adminAutoRefresh = val;
  if (state.adminInterval) {
    clearInterval(state.adminInterval);
    state.adminInterval = null;
  }
  if (state.adminAutoRefresh) {
    state.adminInterval = setInterval(loadAdminData, 5000);
  }
}

export function copyAdminLogs() {
  const list = state.adminLogsList || [];
  const text = list.map(l => `${l.timestamp} [${l.level}] [${l.service}]: ${l.message}`).join('\n');
  navigator.clipboard.writeText(text);
  alert('Логи скопированы в буфер обмена');
}
