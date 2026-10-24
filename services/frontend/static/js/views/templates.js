// Templates & Customization View Controller
import { state, API_BASE } from '../state.js';
import { api } from '../api.js';

export async function loadTemplatesData() {
  try {
    // 1. Load Fields
    const fData = await api.getFieldsConfig();
    state.currentFieldsConfig = fData.fields || [];
    renderFieldsList();

    // 2. Load Templates
    const tData = await api.getTemplates();
    state.currentTemplatesList = tData.templates || [];
    const act = state.currentTemplatesList.find(t => t.is_active);
    if (act) {
      state.activeTemplateId = act.id;
      window.currentActiveTemplateId = act.id;
    }
    renderTemplatesList();
  } catch (err) {
    console.error('Ошибка загрузки данных шаблонов:', err);
  }
}

export function renderFieldsList() {
  const container = document.getElementById('fields-list-container');
  if (!container) return;

  const categories = [
    { id: 'personal', name: 'Личные данные и статус', icon: 'account_circle' },
    { id: 'competencies', name: 'Квалификация и ключевые компетенции', icon: 'psychology' },
    { id: 'experience', name: 'Опыт работы и проекты', icon: 'work' },
    { id: 'education', name: 'Образование и курсы', icon: 'school' }
  ];

  container.innerHTML = categories.map(cat => {
    const catFields = state.currentFieldsConfig.filter(f => f.category === cat.id);
    if (catFields.length === 0) return '';

    return `
      <div class="p-3.5 rounded-xl bg-surface-low border border-surface-container flex flex-col gap-2.5">
        <div class="flex items-center gap-2 text-xs font-bold text-primary">
          <span class="material-symbols-outlined text-secondary text-[18px]">${cat.icon}</span>
          <span>${cat.name}</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
          ${catFields.map(f => `
            <label class="p-2.5 rounded-lg bg-white border border-outline-variant hover:border-secondary/40 flex items-start gap-2.5 cursor-pointer transition-colors select-none">
              <input type="checkbox" data-key="${f.key}" ${f.enabled ? 'checked' : ''} onchange="onFieldCheckboxChange('${f.key}', this.checked)" class="mt-0.5 w-4 h-4 rounded text-secondary focus:ring-secondary cursor-pointer">
              <div class="flex-1 flex flex-col gap-0.5">
                <div class="flex items-center justify-between gap-1">
                  <span class="font-bold text-xs text-primary">${f.name}</span>
                  <button type="button" onclick="event.preventDefault(); copyTag('${f.tag}', this)" title="Скопировать тег" class="px-1.5 py-0.2 rounded bg-surface-low hover:bg-surface-container border border-outline-variant text-[10px] font-mono text-secondary flex items-center gap-0.5 transition-colors">
                    <span>${f.tag}</span>
                    <span class="material-symbols-outlined text-[12px]">content_copy</span>
                  </button>
                </div>
                <p class="text-[11px] text-text-muted leading-tight">${f.description}</p>
              </div>
            </label>
          `).join('')}
        </div>
      </div>
    `;
  }).join('');

  updateFieldsCounter();
}

export function onFieldCheckboxChange(key, isChecked) {
  const f = state.currentFieldsConfig.find(item => item.key === key);
  if (f) f.enabled = isChecked;
  updateFieldsCounter();
}

export function updateFieldsCounter() {
  const total = state.currentFieldsConfig.length;
  const active = state.currentFieldsConfig.filter(f => f.enabled).length;
  const el = document.getElementById('fields-selected-counter');
  if (el) el.textContent = `${active} из ${total} полей активно`;
}

export function applyPreset(name) {
  if (name === 'all') {
    state.currentFieldsConfig.forEach(f => f.enabled = true);
  } else if (name === 'express') {
    const allowed = ['fio', 'vacancy', 'total_year_work', 'pitch', 'skills_and_tools', 'projects', 'project_role', 'project_period', 'project_skills'];
    state.currentFieldsConfig.forEach(f => f.enabled = allowed.includes(f.key));
  } else if (name === 'tech') {
    const allowed = ['fio', 'vacancy', 'pitch', 'skills_and_tools', 'project_backround', 'projects', 'project_role', 'project_period', 'project_tasks', 'project_achievements', 'project_skills', 'languages'];
    state.currentFieldsConfig.forEach(f => f.enabled = allowed.includes(f.key));
  }
  renderFieldsList();
}

export function toggleAllFields(enable) {
  state.currentFieldsConfig.forEach(f => f.enabled = enable);
  renderFieldsList();
}

export async function saveAndApplyFields(silent = false) {
  const payload = {};
  state.currentFieldsConfig.forEach(f => {
    payload[f.key] = !!f.enabled;
  });

  try {
    await api.saveFieldsConfig(payload);
    localStorage.setItem('hrcv_fields_config', JSON.stringify(payload));
    if (silent) {
      alert('Конфигурация полей успешно сохранена!');
    } else {
      if (window.openTemplateInstructionModal) window.openTemplateInstructionModal();
    }
  } catch (err) {
    console.error('Ошибка сохранения полей:', err);
    if (!silent && window.openTemplateInstructionModal) window.openTemplateInstructionModal();
  }
}

export function renderTemplatesList() {
  const container = document.getElementById('templates-list-container');
  if (!container) return;

  const countBadge = document.getElementById('templates-count-badge');
  if (countBadge) countBadge.textContent = `${state.currentTemplatesList.length} макетов`;

  container.innerHTML = state.currentTemplatesList.map(t => {
    const isActive = t.is_active;
    const sizeKb = Math.round(t.size_bytes / 1024);

    return `
      <div class="p-3.5 rounded-xl border ${isActive ? 'bg-secondary/5 border-secondary shadow-xs' : 'bg-surface-low border-outline-variant'} flex items-start justify-between gap-3 transition-colors">
        <div class="flex items-start gap-3">
          <div class="w-9 h-9 rounded-xl ${isActive ? 'bg-secondary text-white' : 'bg-surface-container text-secondary'} flex items-center justify-center shrink-0">
            <span class="material-symbols-outlined text-[20px]">article</span>
          </div>
          <div class="flex flex-col">
            <div class="flex items-center gap-2">
              <span class="font-bold text-xs text-primary">${t.name}</span>
              ${isActive ? '<span class="px-2 py-0.2 rounded-full bg-emeraldBg text-emeraldText text-[10px] font-bold">Активен</span>' : ''}
              ${t.is_system ? '<span class="px-1.5 py-0.2 rounded bg-surface-container text-text-muted text-[10px]">Системный</span>' : ''}
            </div>
            <p class="text-[11px] text-text-muted mt-0.5">${t.description}</p>
            <div class="flex items-center gap-2 text-[10px] text-text-secondary mt-1">
              <span>${t.filename}</span>
              <span>•</span>
              <span>${sizeKb} KB</span>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-1.5 shrink-0">
          ${!isActive ? `
            <button onclick="setActiveTemplate('${t.id}')" title="Сделать активным по умолчанию" class="px-2.5 py-1 rounded-lg bg-white hover:bg-secondary hover:text-white border border-outline-variant text-xs font-semibold text-text-primary transition-colors">
              Выбрать
            </button>
          ` : ''}
          <button onclick="downloadTemplate('${t.id}')" title="Скачать файл шаблона" class="p-1 rounded-lg bg-white hover:bg-surface-container border border-outline-variant text-secondary transition-colors">
            <span class="material-symbols-outlined text-[18px]">download</span>
          </button>
          ${!t.is_system ? `
            <button onclick="deleteTemplate('${t.id}', '${t.name}')" title="Удалить макет" class="p-1 rounded-lg bg-white hover:bg-rose-50 border border-outline-variant text-roseText transition-colors">
              <span class="material-symbols-outlined text-[18px]">delete</span>
            </button>
          ` : ''}
        </div>
      </div>
    `;
  }).join('');
}

export async function setActiveTemplate(id) {
  try {
    await api.setActiveTemplate(id);
    state.activeTemplateId = id;
    window.currentActiveTemplateId = id;
    state.currentTemplatesList.forEach(t => t.is_active = (t.id === id));
    renderTemplatesList();
  } catch (e) {
    console.error('Ошибка смены шаблона:', e);
  }
}

export async function downloadTemplate(id) {
  window.open(`${API_BASE}/api/v1/templates/${id}/download`, '_blank');
}

export async function deleteTemplate(id, name) {
  if (!confirm(`Удалить пользовательский шаблон "${name}"?`)) return;
  try {
    await api.deleteTemplate(id);
    loadTemplatesData();
  } catch (e) {
    console.error('Ошибка удаления шаблона:', e);
  }
}

export function handleTemplateFileSelect(event) {
  const file = event.target.files[0];
  if (!file) return;
  if (!file.name.toLowerCase().endsWith('.docx')) {
    alert('Пожалуйста, выберите файл с расширением .docx');
    event.target.value = '';
    return;
  }
  state.selectedTemplateUploadFile = file;
  document.getElementById('tpl-file-label').textContent = `${file.name} (${Math.round(file.size / 1024)} KB)`;
  const nameInput = document.getElementById('upload-tpl-name');
  if (!nameInput.value.trim()) {
    nameInput.value = file.name.replace(/\.docx$/i, '');
  }
}

export async function handleTemplateUpload(e) {
  if (e) e.preventDefault();
  if (!state.selectedTemplateUploadFile) {
    alert('Пожалуйста, выберите файл .docx для загрузки');
    return;
  }

  const name = document.getElementById('upload-tpl-name').value.trim();
  const desc = document.getElementById('upload-tpl-desc').value.trim();
  const makeActive = document.getElementById('upload-tpl-make-active').checked;
  const btn = document.getElementById('btn-upload-tpl');

  btn.disabled = true;
  btn.innerHTML = `<span class="material-symbols-outlined text-[16px] animate-spin">sync</span><span>Загрузка шаблона...</span>`;

  try {
    await api.uploadTemplate(state.selectedTemplateUploadFile, name, desc, makeActive);
    alert('Шаблон успешно добавлен в библиотеку!');
    state.selectedTemplateUploadFile = null;
    document.getElementById('upload-tpl-file').value = '';
    document.getElementById('tpl-file-label').textContent = 'Выберите файл .docx или перетащите сюда';
    document.getElementById('upload-tpl-name').value = '';
    document.getElementById('upload-tpl-desc').value = '';

    loadTemplatesData();
  } catch (err) {
    alert('Ошибка: ' + err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span class="material-symbols-outlined text-[16px]">add_circle</span><span>Добавить шаблон в библиотеку</span>`;
  }
}
