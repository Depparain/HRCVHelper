// Notifications System for HRCVHelper
import { state } from './state.js';

export function toggleNotificationsMenu(e) {
  if (e) e.stopPropagation();
  const dropdown = document.getElementById('notifications-dropdown');
  if (!dropdown) return;
  dropdown.classList.toggle('hidden');
}

export function formatTimeAgo(ts) {
  if (!ts) return 'Только что';
  const diffSec = Math.floor((Date.now() - new Date(ts).getTime()) / 1000);
  if (isNaN(diffSec) || diffSec < 60) return 'Только что';
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin} мин назад`;
  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return `${diffHours} ч назад`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays} д назад`;
}

export function updateNotificationsFromCVs(list) {
  const generated = [];

  (list || []).forEach(c => {
    const fio = c.jsonb?.fio || `Кандидат #${c.cv_id}`;
    const vac = c.jsonb?.vacancy ? ` (${c.jsonb.vacancy})` : '';

    if (c.status === 'Ожидает проверки HR') {
      generated.push({
        id: `cv_${c.cv_id}_pending`,
        cvId: c.cv_id,
        type: 'pending',
        title: 'Ожидает проверки HR',
        message: `${fio}${vac} — распознавание завершено, подтвердите данные для DOCX`,
        timestamp: c.updated_at || Date.now(),
        badge: 'Проверка',
        badgeClass: 'bg-amber-100 text-amber-800',
        icon: 'rule',
        iconBg: 'bg-amber-50 text-amber-600',
        actionLabel: 'Проверить'
      });
    } else if (c.status === 'Обработка резюме') {
      const reworkComment = c.jsonb?._rework_comment;
      generated.push({
        id: `cv_${c.cv_id}_processing`,
        cvId: c.cv_id,
        type: 'processing',
        title: reworkComment ? 'На доработке у ИИ' : 'Обработка резюме',
        message: reworkComment ? `${fio}: «${reworkComment}»` : `${fio}${vac} — выполняется извлечение структуры`,
        timestamp: c.updated_at || Date.now(),
        badge: reworkComment ? 'Доработка' : 'В процессе',
        badgeClass: 'bg-blue-100 text-blue-800',
        icon: 'sync',
        iconBg: 'bg-blue-50 text-secondary',
        actionLabel: 'Смотреть'
      });
    } else if (c.status === 'Готово') {
      generated.push({
        id: `cv_${c.cv_id}_ready`,
        cvId: c.cv_id,
        type: 'ready',
        title: 'Резюме готово',
        message: `${fio}${vac} — DOCX успешно сформирован и доступен для скачивания`,
        timestamp: c.updated_at || Date.now(),
        badge: 'Готово',
        badgeClass: 'bg-emerald-100 text-emerald-800',
        icon: 'task_alt',
        iconBg: 'bg-emerald-50 text-emerald-600',
        actionLabel: 'Скачать'
      });
    } else if (c.status && c.status.includes('Ошибк')) {
      generated.push({
        id: `cv_${c.cv_id}_error`,
        cvId: c.cv_id,
        type: 'error',
        title: 'Ошибка обработки',
        message: `${fio} — возникла ошибка при конвертации документа`,
        timestamp: c.updated_at || Date.now(),
        badge: 'Ошибка',
        badgeClass: 'bg-rose-100 text-roseText',
        icon: 'error',
        iconBg: 'bg-rose-50 text-roseText',
        actionLabel: 'Подробнее'
      });
    }
  });

  const sessionNotes = state.notificationsList.filter(n => n.isSession);
  state.notificationsList = [...sessionNotes, ...generated];
  renderNotificationsUI();
}

export function addSessionNotification({ title, message, type = 'info', cvId = null, badge = null }) {
  const id = `session_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;
  state.notificationsList.unshift({
    id,
    cvId,
    type,
    title,
    message,
    timestamp: Date.now(),
    badge: badge || 'Событие',
    badgeClass: 'bg-surface-container text-text-secondary',
    icon: type === 'upload' ? 'upload_file' : type === 'rework' ? 'rate_review' : type === 'ready' ? 'task_alt' : 'notifications',
    iconBg: type === 'upload' ? 'bg-secondary/10 text-secondary' : type === 'rework' ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800',
    actionLabel: cvId ? 'Открыть' : 'Понятно',
    isSession: true
  });
  renderNotificationsUI();
}

export function renderNotificationsUI() {
  const badge = document.getElementById('notifications-badge');
  const badgeHeader = document.getElementById('notifications-badge-header');
  const listEl = document.getElementById('notifications-list');
  const totalLabel = document.getElementById('notifications-total-label');

  if (!badge || !listEl) return;

  const unreadCount = state.notificationsList.filter(n => !state.readNotificationIds.has(n.id)).length;

  if (unreadCount > 0) {
    badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
    badge.classList.remove('hidden');
    badgeHeader.textContent = `${unreadCount} новых`;
    badgeHeader.className = 'px-2 py-0.5 rounded-full bg-secondary/10 text-secondary text-[11px] font-semibold';
  } else {
    badge.classList.add('hidden');
    badgeHeader.textContent = 'Все прочитаны';
    badgeHeader.className = 'px-2 py-0.5 rounded-full bg-surface-low text-text-muted text-[11px] font-semibold';
  }

  totalLabel.textContent = `Всего: ${state.notificationsList.length}`;

  if (state.notificationsList.length === 0) {
    listEl.innerHTML = `
      <div class="p-8 text-center flex flex-col items-center justify-center text-text-muted">
        <span class="material-symbols-outlined text-[36px] text-outline mb-2">notifications_off</span>
        <span class="text-xs font-semibold text-text-primary">Новых уведомлений нет</span>
        <span class="text-[11px] text-text-muted mt-1 max-w-[220px]">Здесь будут отображаться статусы обработки резюме и напоминания о проверке</span>
      </div>
    `;
    return;
  }

  listEl.innerHTML = state.notificationsList.map(item => {
    const isUnread = !state.readNotificationIds.has(item.id);
    return `
      <div class="p-3.5 hover:bg-surface-low transition-colors cursor-pointer flex items-start gap-3 relative ${isUnread ? 'bg-secondary/5 font-medium' : 'opacity-85'}" onclick="handleNotificationClick('${item.id}', ${item.cvId || 'null'}, '${item.type}')">
        <div class="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${item.iconBg || 'bg-surface-container text-secondary'} shadow-xs">
          <span class="material-symbols-outlined text-[18px]">${item.icon || 'notifications'}</span>
        </div>
        <div class="flex-1 min-w-0 text-left">
          <div class="flex items-center justify-between gap-1 mb-0.5">
            <span class="text-xs font-semibold text-text-primary truncate">${item.title}</span>
            <span class="text-[10px] text-text-muted shrink-0">${formatTimeAgo(item.timestamp)}</span>
          </div>
          <p class="text-[11px] text-text-secondary leading-tight line-clamp-2">${item.message}</p>
          <div class="flex items-center gap-2 mt-1.5">
            ${item.badge ? `<span class="px-1.5 py-0.5 rounded text-[10px] font-bold ${item.badgeClass || 'bg-surface-container text-text-secondary'}">${item.badge}</span>` : ''}
            <span class="text-[10px] text-secondary font-semibold hover:underline flex items-center gap-0.5">${item.actionLabel || 'Открыть'} &rarr;</span>
          </div>
        </div>
        ${isUnread ? `<span class="w-2 h-2 rounded-full bg-secondary shrink-0 mt-2" title="Не прочитано"></span>` : ''}
      </div>
    `;
  }).join('');
}

export function handleNotificationClick(id, cvId, type) {
  state.readNotificationIds.add(id);
  state.saveReadNotifications();
  renderNotificationsUI();

  const dropdown = document.getElementById('notifications-dropdown');
  if (dropdown) dropdown.classList.add('hidden');

  if (!cvId) return;

  if (type === 'ready') {
    if (window.openResultPage) window.openResultPage(cvId);
  } else {
    if (window.openValidationPage) window.openValidationPage(cvId);
  }
}

export function markAllNotificationsAsRead() {
  state.notificationsList.forEach(n => state.readNotificationIds.add(n.id));
  state.saveReadNotifications();
  renderNotificationsUI();
}

export function clearAllNotifications() {
  state.notificationsList.forEach(n => state.readNotificationIds.add(n.id));
  state.saveReadNotifications();
  state.notificationsList = state.notificationsList.filter(n => !state.readNotificationIds.has(n.id));
  renderNotificationsUI();
}

// Close notifications dropdown on outside click
document.addEventListener('click', (e) => {
  const wrapper = document.getElementById('notifications-wrapper');
  const dropdown = document.getElementById('notifications-dropdown');
  if (dropdown && !dropdown.classList.contains('hidden')) {
    if (wrapper && !wrapper.contains(e.target)) {
      dropdown.classList.add('hidden');
    }
  }
});
