// Dashboard & CV Registry View Controller
import { state } from '../state.js';
import { api } from '../api.js';
import { updateNotificationsFromCVs, addSessionNotification } from '../notifications.js';

export async function loadCVs(silent = false) {
  try {
    const hrId = state.currentUser ? state.currentUser.hr_id : '';
    const list = await api.getCVs(hrId);
    state.cvList = list || [];
    updateMetrics();
    renderCVTable();
    updateNotificationsFromCVs(state.cvList);

    const inProgress = state.cvList.filter(c => c.status === 'Загружено' || c.status.includes('Обработ') || c.status.includes('Конверт'));
    const banner = document.getElementById('processing-banner');
    if (banner) {
      if (inProgress.length > 0) {
        banner.classList.remove('hidden');
        document.getElementById('processing-filename').textContent = inProgress[0].jsonb?.fio || 'Резюме.pdf';
      } else {
        banner.classList.add('hidden');
      }
    }
  } catch (e) {
    if (!silent) console.error('Ошибка загрузки списка резюме:', e);
  }
}

export function updateMetrics() {
  const total = state.cvList.length;
  const pending = state.cvList.filter(c => c.status === 'Ожидает проверки HR').length;
  const ready = state.cvList.filter(c => c.status === 'Готово').length;
  const loaded = state.cvList.filter(c => c.status === 'Загружено' || c.status.includes('Обработ') || c.status.includes('Конверт')).length;
  const err = state.cvList.filter(c => c.status.includes('Ошибк')).length;

  document.getElementById('metric-total').textContent = total;
  document.getElementById('metric-pending').textContent = pending;
  document.getElementById('metric-llm').textContent = total;
  document.getElementById('metric-ready').textContent = ready;

  document.getElementById('tab-cnt-all').textContent = total;
  document.getElementById('tab-cnt-loaded').textContent = loaded;
  document.getElementById('tab-cnt-pending').textContent = pending;
  document.getElementById('tab-cnt-ready').textContent = ready;
  document.getElementById('tab-cnt-error').textContent = err;
}

export function setTab(tab) {
  state.currentTab = tab;
  document.querySelectorAll('.tab-btn').forEach(btn => {
    if (btn.getAttribute('data-tab') === tab) {
      btn.className = 'tab-btn px-3.5 py-1.5 rounded-lg bg-primary text-white text-xs font-semibold flex items-center gap-1.5';
    } else {
      btn.className = 'tab-btn px-3.5 py-1.5 rounded-lg text-text-secondary hover:bg-surface-low text-xs font-medium flex items-center gap-1.5';
    }
  });
  renderCVTable();
}

export function renderCVTable() {
  const tbody = document.getElementById('cv-table-body');
  if (!tbody) return;

  const search = (document.getElementById('cv-search')?.value || '').toLowerCase();
  const roleFilter = document.getElementById('cv-role-filter')?.value || 'all';
  const sort = document.getElementById('cv-sort')?.value || 'newest';

  let items = state.cvList.filter(c => {
    if (state.currentTab === 'Загружено' && !(c.status === 'Загружено' || c.status.includes('Обработ') || c.status.includes('Конверт'))) return false;
    if (state.currentTab === 'Ожидает проверки HR' && c.status !== 'Ожидает проверки HR') return false;
    if (state.currentTab === 'Готово' && c.status !== 'Готово') return false;
    if (state.currentTab === 'Ошибка' && !c.status.includes('Ошибк')) return false;

    const fio = (c.jsonb?.fio || '').toLowerCase();
    const vac = (c.jsonb?.vacancy || '').toLowerCase();
    if (search && !fio.includes(search) && !vac.includes(search)) return false;

    if (roleFilter === 'lead' && !vac.includes('lead') && !vac.includes('руковод')) return false;
    if (roleFilter === 'senior' && !vac.includes('senior') && !vac.includes('старш')) return false;
    if (roleFilter === 'analyst' && !vac.includes('аналитик') && !vac.includes('analyst')) return false;
    if (roleFilter === 'ds' && !vac.includes('data') && !vac.includes('ml') && !vac.includes('ai')) return false;

    return true;
  });

  if (sort === 'oldest') {
    items = [...items].reverse();
  }

  if (items.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="py-12 text-center text-text-muted">
          <span class="material-symbols-outlined text-[36px] text-outline mb-1">inbox</span>
          <p class="font-medium text-xs">Нет резюме по выбранным критериям</p>
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = items.map(c => {
    const fio = c.jsonb?.fio || 'Новый кандидат';
    const vac = c.jsonb?.vacancy || 'Вакансия не указана';
    const exp = c.jsonb?.total_year_work || '';
    const initials = fio.split(' ').map(s => s[0]).slice(0, 2).join('') || 'CV';

    let badgeBg = 'bg-blue-50 text-secondary border-blue-200';
    let badgeDot = 'bg-secondary animate-pulse';
    let isProcessing = false;

    if (c.status === 'Готово') {
      badgeBg = 'bg-emeraldBg text-emeraldText border-emeraldBorder';
      badgeDot = 'bg-emeraldAccent';
    } else if (c.status === 'Ожидает проверки HR') {
      badgeBg = 'bg-amberBg text-amberText border-amberBorder font-bold';
      badgeDot = 'bg-amberAccent';
    } else if (c.status.includes('Ошибк')) {
      badgeBg = 'bg-roseBg text-roseText border-roseBorder';
      badgeDot = 'bg-roseText';
    } else {
      isProcessing = true;
    }

    let actionBtn = '';
    if (c.status === 'Ожидает проверки HR') {
      actionBtn = `
        <button onclick="openValidationPage(${c.cv_id})" class="px-3 py-1.5 rounded-lg bg-amberAccent hover:bg-amber-600 text-white font-bold text-xs flex items-center gap-1 shadow-xs transition-colors">
          <span class="material-symbols-outlined text-[15px]">rate_review</span>
          <span>Валидация</span>
        </button>
      `;
    } else if (c.status === 'Готово') {
      actionBtn = `
        <button onclick="downloadCV(${c.cv_id})" class="px-3 py-1.5 rounded-lg bg-emeraldText hover:bg-emerald-700 text-white font-bold text-xs flex items-center gap-1 shadow-xs transition-colors" title="Скачать документ .docx">
          <span class="material-symbols-outlined text-[15px]">download</span>
          <span>.docx</span>
        </button>
      `;
    } else if (isProcessing) {
      actionBtn = `
        <span class="inline-flex items-center gap-1 text-[11px] font-semibold text-secondary">
          <span class="material-symbols-outlined text-[14px] animate-spin">sync</span>
          <span>Обработка...</span>
        </span>
      `;
    } else {
      actionBtn = `
        <button onclick="openValidationPage(${c.cv_id})" class="px-2.5 py-1.5 rounded-lg border border-outline-variant hover:bg-surface-low text-text-primary text-xs font-semibold">
          Детали
        </button>
      `;
    }

    return `
      <tr class="hover:bg-surface-low/50 transition-colors">
        <td class="px-4 py-3 font-mono text-[11px] text-text-muted">#${c.cv_id}</td>
        <td class="px-4 py-3">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full bg-surface-container text-secondary flex items-center justify-center font-bold text-xs">
              ${initials}
            </div>
            <div class="flex flex-col">
              <span class="font-bold text-primary ${!isProcessing ? 'hover:text-secondary cursor-pointer' : ''}" onclick="${!isProcessing ? (c.status === 'Готово' ? `openResultPage(${c.cv_id})` : `openValidationPage(${c.cv_id})`) : ''}">${fio}</span>
              <span class="text-[11px] text-text-muted">${vac}${exp ? ' • ' + exp : ''}</span>
            </div>
          </div>
        </td>
        <td class="px-4 py-3">
          <div class="flex items-center gap-1.5">
            <span class="px-1.5 py-0.5 rounded bg-surface-low font-bold text-secondary text-[10px]">PDF</span>
            <span class="text-text-primary text-xs truncate max-w-[120px]">Резюме.pdf</span>
          </div>
        </td>
        <td class="px-4 py-3">
          <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border text-[11px] ${badgeBg}">
            <span class="w-1.5 h-1.5 rounded-full ${badgeDot}"></span>
            ${c.status}
          </span>
        </td>
        <td class="px-4 py-3 text-text-muted text-[11px]">Сегодня</td>
        <td class="px-4 py-3 text-right">
          <div class="inline-flex items-center justify-end gap-1.5">
            ${actionBtn}
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

export function openUploadModal() {
  state.selectedUploadFile = null;
  document.getElementById('file-upload-input').value = '';
  document.getElementById('upload-file-status').classList.add('hidden');
  document.getElementById('btn-start-upload').disabled = true;
  document.getElementById('modal-upload').classList.remove('hidden');
}

export function closeUploadModal() {
  document.getElementById('modal-upload').classList.add('hidden');
}

export function handleFileSelect(event) {
  if (event.target.files && event.target.files.length > 0) {
    state.selectedUploadFile = event.target.files[0];
    document.getElementById('upload-filename').textContent = state.selectedUploadFile.name;
    document.getElementById('upload-filesize').textContent = (state.selectedUploadFile.size / (1024 * 1024)).toFixed(1) + ' MB';
    document.getElementById('upload-file-status').classList.remove('hidden');
    document.getElementById('btn-start-upload').disabled = false;
  }
}

export function clearSelectedFile() {
  state.selectedUploadFile = null;
  document.getElementById('file-upload-input').value = '';
  document.getElementById('upload-file-status').classList.add('hidden');
  document.getElementById('btn-start-upload').disabled = true;
}

export async function startFileUpload() {
  if (!state.selectedUploadFile) return;

  const fileToUpload = state.selectedUploadFile;
  const fileName = fileToUpload.name;

  closeUploadModal();

  const banner = document.getElementById('processing-banner');
  if (banner) {
    banner.classList.remove('hidden');
    document.getElementById('processing-filename').textContent = fileName;
  }

  addSessionNotification({
    type: 'upload',
    title: 'Файл передан в пайплайн',
    message: `${fileName} загружается и обрабатывается нейросетью`,
    badge: 'Загрузка'
  });

  try {
    setTimeout(loadCVs, 500);

    const hrId = state.currentUser ? state.currentUser.hr_id : '1';
    const newCv = await api.uploadCV(fileToUpload, hrId);

    addSessionNotification({
      type: 'pending',
      cvId: newCv.cv_id,
      title: 'Резюме распознано',
      message: `${newCv.data?.fio || fileName} готово к проверке HR`,
      badge: 'Новое'
    });
    await loadCVs();
  } catch (err) {
    console.error('Ошибка фоновой загрузки:', err);
    alert('Ошибка при обработке резюме ' + fileName + ': ' + err.message);
  } finally {
    loadCVs();
  }
}
