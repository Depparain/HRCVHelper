// Modals and Dialogs Component Controller
import { state, API_BASE } from '../state.js';
import { api } from '../api.js';
import { addSessionNotification } from '../notifications.js';
import { hideAllViews, showDashboard } from '../views/auth.js';
import { loadCVs } from '../views/dashboard.js';
import { downloadTemplate } from '../views/templates.js';

// --- Rework Modal ---

export function openReworkModal() {
  if (!state.activeCvId) return;
  const fio = state.activeCvJson?.fio || 'Кандидат';
  const vac = state.activeCvJson?.vacancy || '';
  document.getElementById('rework-candidate-subtitle').textContent = `Резюме #${state.activeCvId}: ${fio} ${vac ? '• ' + vac : ''}`;
  document.getElementById('rework-comment-input').value = '';
  document.getElementById('modal-rework').classList.remove('hidden');
}

export function closeReworkModal() {
  document.getElementById('modal-rework').classList.add('hidden');
}

export function appendReworkChip(text) {
  const input = document.getElementById('rework-comment-input');
  if (input.value.trim()) {
    input.value = input.value.trim() + ' ' + text;
  } else {
    input.value = text;
  }
  input.focus();
}

export async function submitReworkWithComment() {
  if (!state.activeCvId) return;
  const comment = document.getElementById('rework-comment-input').value.trim();
  const btn = document.getElementById('btn-submit-rework');
  const origHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<span class="material-symbols-outlined text-[16px] animate-spin">sync</span><span>Запуск пересоздания...</span>`;

  try {
    await api.reworkCV(state.activeCvId, comment);

    closeReworkModal();
    addSessionNotification({
      type: 'rework',
      cvId: state.activeCvId,
      title: 'Возврат на доработку',
      message: comment ? `Резюме #${state.activeCvId}: «${comment}»` : `Резюме #${state.activeCvId} отправлено на повторный парсинг Gemma-3`,
      badge: 'Доработка'
    });
    alert(`Резюме #${state.activeCvId} успешно возвращено на доработку.\nСтатус: «Обработка резюме». Запущен повторный парсинг Gemma-3.`);
    showDashboard();
    await loadCVs();
  } catch (err) {
    alert('Ошибка: ' + err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = origHtml;
  }
}

// --- Result Download View / Modal ---

export async function downloadCV(cvId = null, filename = null) {
  const targetId = cvId || state.activeCvId;
  if (!targetId) return;

  const targetFilename = filename || document.getElementById('res-doc-filename')?.textContent || `resume_${targetId}.docx`;
  const token = state.currentToken || localStorage.getItem('hrcv_token') || '';
  const tokenParam = token ? `?token=${encodeURIComponent(token)}` : '';
  const fallbackUrl = `${API_BASE}/api/v1/cv/${targetId}/download${tokenParam}`;

  if (!token) {
    alert('Требуется авторизация. Пожалуйста, выполните вход в систему.');
    return;
  }

  try {
    const resp = await fetch(`${API_BASE}/api/v1/cv/${targetId}/download`, {
      headers: {
        'Authorization': `Bearer ${token}`
      },
    });

    if (resp.status === 401) {
      alert('Сессия авторизации истекла. Пожалуйста, выполните повторный вход.');
      return;
    }

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || 'Ошибка скачивания файла');
    }

    const blob = await resp.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = targetFilename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => window.URL.revokeObjectURL(blobUrl), 1000);
  } catch (err) {
    console.warn('Blob download failed, using direct URL:', err);
    if (token) {
      window.location.href = fallbackUrl;
    } else {
      alert('Не удалось скачать файл: ' + (err.message || 'Ошибка'));
    }
  }
}

export async function openResultPage(cvId, record) {
  state.activeCvId = cvId;
  hideAllViews();
  document.getElementById('main-header').classList.remove('hidden');
  document.getElementById('view-result').classList.remove('hidden');

  let data = record?.data || state.activeCvJson;
  if (!data || !data.fio) {
    try {
      const fullRecord = await api.getCV(cvId);
      data = fullRecord.jsonb || {};
      state.activeCvJson = data;
    } catch (e) {
      console.warn('Не удалось загрузить данные резюме:', e);
    }
  }

  const fio = data?.fio || 'Кандидат';
  const vac = data?.vacancy || 'Специалист';
  const cleanFio = fio.replace(/[^а-яА-Яa-zA-Z0-9_-]/g, '_');
  const cleanVac = vac.replace(/[^а-яА-Яa-zA-Z0-9_-]/g, '_');
  const filename = `Резюме_${cleanFio}_${cleanVac}.docx`;

  document.getElementById('res-doc-filename').textContent = filename;
  const downloadBtn = document.getElementById('res-download-btn');
  if (downloadBtn) {
    downloadBtn.onclick = (e) => {
      e.preventDefault();
      downloadCV(cvId, filename);
    };
  }
}

export function copyDownloadUrl() {
  const token = state.currentToken || localStorage.getItem('hrcv_token') || '';
  const tokenParam = token ? `?token=${encodeURIComponent(token)}` : '';
  const url = `${API_BASE}/api/v1/cv/${state.activeCvId}/download${tokenParam}`;
  navigator.clipboard.writeText(url);
  const textEl = document.getElementById('copy-link-text');
  textEl.textContent = 'Скопировано!';
  setTimeout(() => { textEl.textContent = 'Копировать ссылку'; }, 3000);
}

// --- Template Instruction Modal ---

export function openTemplateInstructionModal() {
  const modal = document.getElementById('modal-template-instruction');
  if (!modal) return;

  const activeFields = state.currentFieldsConfig.filter(f => f.enabled);
  document.getElementById('instruction-modal-subtitle').textContent =
    `Список тегов и правила верстки под выбранные вами ${activeFields.length} полей`;

  const grid = document.getElementById('instruction-tags-grid');
  grid.innerHTML = activeFields.map(f => `
    <div class="p-3 rounded-xl bg-surface-low border border-outline-variant flex items-center justify-between gap-2">
      <div class="flex flex-col">
        <span class="font-bold text-primary text-xs">${f.name}</span>
        <span class="text-[10px] font-mono text-secondary">${f.tag}</span>
      </div>
      <button onclick="copyTag('${f.tag}', this)" class="px-2.5 py-1 rounded-lg bg-white hover:bg-surface-container border border-outline-variant text-[11px] font-semibold text-text-primary flex items-center gap-1 transition-colors">
        <span class="material-symbols-outlined text-[14px]">content_copy</span>
        <span>Копировать</span>
      </button>
    </div>
  `).join('');

  const hasProjects = activeFields.some(f => f.key === 'projects' || f.key.startsWith('project_'));
  const loopBlock = document.getElementById('instruction-project-loop-container');
  if (loopBlock) {
    if (hasProjects) {
      loopBlock.classList.remove('hidden');
    } else {
      loopBlock.classList.add('hidden');
    }
  }

  modal.classList.remove('hidden');
}

export function closeTemplateInstructionModal() {
  const modal = document.getElementById('modal-template-instruction');
  if (modal) modal.classList.add('hidden');
}

export function copyTag(text, btn) {
  navigator.clipboard.writeText(text);
  if (btn) {
    const orig = btn.innerHTML;
    btn.innerHTML = `<span class="material-symbols-outlined text-[14px] text-emeraldText">check</span><span class="text-emeraldText font-bold">Скопировано!</span>`;
    setTimeout(() => { btn.innerHTML = orig; }, 1500);
  }
}

export function copyAllActiveTags() {
  const activeFields = state.currentFieldsConfig.filter(f => f.enabled);
  const text = activeFields.map(f => `${f.name}: ${f.tag}`).join('\n');
  navigator.clipboard.writeText(text);
  alert(`Скопировано ${activeFields.length} тегов в буфер обмена!`);
}

export function copyProjectLoopCode() {
  const code = document.getElementById('code-project-loop').textContent.trim();
  navigator.clipboard.writeText(code);
  alert('Код цикла проектов скопирован в буфер обмена!');
}

export function downloadActiveOrBaseTemplate() {
  const id = state.activeTemplateId || 'default';
  downloadTemplate(id);
}
