// Validation View Controller (Human-in-the-Loop)
import { state } from '../state.js';
import { api } from '../api.js';
import { addSessionNotification } from '../notifications.js';
import { hideAllViews } from './auth.js';

export async function openValidationPage(cvId) {
  state.activeCvId = cvId;
  try {
    const data = await api.getCV(cvId);
    state.activeCvJson = data.jsonb || {};

    document.getElementById('val-breadcrumb-id').textContent = `Резюме #CV-${cvId}`;

    document.getElementById('val-fio').value = state.activeCvJson.fio || '';
    document.getElementById('val-vacancy').value = state.activeCvJson.vacancy || '';
    document.getElementById('val-total-year').value = state.activeCvJson.total_year_work || '';
    document.getElementById('val-background').value = state.activeCvJson.project_backround || '';
    document.getElementById('val-pitch').value = state.activeCvJson.pitch || '';
    document.getElementById('val-languages').value = state.activeCvJson.languages || '';
    document.getElementById('val-location').value = state.activeCvJson.citizenship_location || '';
    document.getElementById('val-employment').value = state.activeCvJson.employment || '';
    document.getElementById('val-status').value = state.activeCvJson.status || '';

    if (state.activeCvJson._rework_comment) {
      document.getElementById('val-rework-banner').classList.remove('hidden');
      document.getElementById('val-rework-text').textContent = 'Замечание к доработке: ' + state.activeCvJson._rework_comment;
    } else {
      document.getElementById('val-rework-banner').classList.add('hidden');
    }

    renderSkills();
    renderEducation();
    renderProjects();
    renderRawJsonViewer();

    hideAllViews();
    document.getElementById('main-header').classList.remove('hidden');
    document.getElementById('view-validation').classList.remove('hidden');
  } catch (e) {
    alert(e.message);
  }
}

export function renderSkills() {
  const cloud = document.getElementById('skills-cloud');
  const list = state.activeCvJson.skills_and_tools || [];
  document.getElementById('skills-badge').textContent = `${list.length} навыков`;

  cloud.innerHTML = list.map((s, idx) => `
    <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-surface-low border border-surface-container text-xs font-semibold text-text-primary">
      <span>${s}</span>
      <button onclick="removeSkillItem(${idx})" class="text-outline hover:text-roseText">
        <span class="material-symbols-outlined text-[14px]">close</span>
      </button>
    </span>
  `).join('');
}

export function addSkillItem() {
  const inp = document.getElementById('input-new-skill');
  const val = inp.value.trim();
  if (val) {
    if (!state.activeCvJson.skills_and_tools) state.activeCvJson.skills_and_tools = [];
    state.activeCvJson.skills_and_tools.push(val);
    inp.value = '';
    renderSkills();
    renderRawJsonViewer();
  }
}

export function removeSkillItem(idx) {
  state.activeCvJson.skills_and_tools.splice(idx, 1);
  renderSkills();
  renderRawJsonViewer();
}

export function renderEducation() {
  const container = document.getElementById('education-list');
  const list = state.activeCvJson.education || [];

  if (list.length === 0) {
    container.innerHTML = `<span class="text-xs text-text-muted">Данные об образовании отсутствуют</span>`;
    return;
  }

  container.innerHTML = list.map((edu, idx) => `
    <div class="p-3.5 rounded-xl bg-surface-low border border-surface-container flex items-start gap-3">
      <div class="w-8 h-8 rounded-lg bg-surface-container text-secondary flex items-center justify-center shrink-0">
        <span class="material-symbols-outlined text-[18px]">school</span>
      </div>
      <div class="flex-1 flex flex-col gap-1">
        <div class="flex items-center justify-between">
          <input type="text" value="${edu.institution || ''}" onchange="state.activeCvJson.education[${idx}].institution=this.value; renderRawJsonViewer();" class="bg-transparent font-bold text-xs text-primary outline-none" placeholder="Учебное заведение">
          <span class="px-2 py-0.5 rounded bg-white text-[10px] font-semibold text-text-secondary">${edu.type || 'Высшее'}</span>
        </div>
        <input type="text" value="${edu.speciality || ''}" onchange="state.activeCvJson.education[${idx}].speciality=this.value; renderRawJsonViewer();" class="bg-transparent text-xs text-text-secondary outline-none" placeholder="Специальность">
        <input type="text" value="${edu.year || ''}" onchange="state.activeCvJson.education[${idx}].year=this.value; renderRawJsonViewer();" class="bg-transparent text-[11px] text-text-muted outline-none" placeholder="Годы обучения">
      </div>
      <button onclick="state.activeCvJson.education.splice(${idx}, 1); renderEducation(); renderRawJsonViewer();" class="text-outline hover:text-roseText">
        <span class="material-symbols-outlined text-[16px]">delete</span>
      </button>
    </div>
  `).join('');
}

export function addEducationItem() {
  if (!state.activeCvJson.education) state.activeCvJson.education = [];
  state.activeCvJson.education.push({
    type: 'Высшее:',
    institution: 'ВУЗ / Университет',
    speciality: 'Специальность',
    year: '2018 - 2022'
  });
  renderEducation();
  renderRawJsonViewer();
}

export function renderProjects() {
  const container = document.getElementById('projects-accordion-list');
  const list = state.activeCvJson.projects || [];
  document.getElementById('projects-counter-text').textContent = `${list.length} проверенных карьерных позиций`;

  container.innerHTML = list.map((p, pIdx) => `
    <div class="rounded-xl border border-surface-container bg-surface-low overflow-hidden">
      <div class="p-3.5 flex items-center justify-between cursor-pointer hover:bg-surface-container/40 transition-colors" onclick="toggleProjectAccordion(${pIdx})">
        <div class="flex items-center gap-3">
          <span class="w-6 h-6 rounded-md bg-secondary text-white flex items-center justify-center font-bold text-xs">${pIdx + 1}</span>
          <div>
            <h5 class="text-xs font-bold text-primary">${p.place_time_raw || 'Проект'}</h5>
            <span class="text-[11px] text-text-muted">${p.role_in_project || ''} • ${p.period || ''}</span>
          </div>
        </div>
        <span class="material-symbols-outlined text-outline text-[18px]" id="proj-chevron-${pIdx}">expand_more</span>
      </div>
      <div id="proj-body-${pIdx}" class="p-4 border-t border-surface-container flex flex-col gap-3 bg-white">
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="text-[10px] font-bold text-text-secondary uppercase">Компания</label>
            <input type="text" value="${p.place_time_raw || ''}" onchange="state.activeCvJson.projects[${pIdx}].place_time_raw=this.value; renderRawJsonViewer();" class="w-full h-8 px-2.5 rounded-lg bg-surface-low border border-outline-variant text-xs">
          </div>
          <div>
            <label class="text-[10px] font-bold text-text-secondary uppercase">Роль</label>
            <input type="text" value="${p.role_in_project || ''}" onchange="state.activeCvJson.projects[${pIdx}].role_in_project=this.value; renderRawJsonViewer();" class="w-full h-8 px-2.5 rounded-lg bg-surface-low border border-outline-variant text-xs">
          </div>
        </div>
        <div>
          <label class="text-[10px] font-bold text-text-secondary uppercase">Период работы</label>
          <input type="text" value="${p.period || ''}" onchange="state.activeCvJson.projects[${pIdx}].period=this.value; renderRawJsonViewer();" class="w-full h-8 px-2.5 rounded-lg bg-surface-low border border-outline-variant text-xs">
        </div>

        <!-- Tasks -->
        <div>
          <div class="flex justify-between items-center text-[10px] font-bold text-text-secondary uppercase mb-1">
            <span>Задачи на проекте</span>
            <button onclick="addProjectTask(${pIdx})" class="text-secondary hover:underline">+ Добавить задачу</button>
          </div>
          <div class="flex flex-col gap-1.5" id="proj-tasks-${pIdx}">
            ${(p.task_on_project || []).map((t, tIdx) => `
              <div class="flex items-center gap-2 p-1.5 rounded-lg bg-surface-low border border-surface-container">
                <span class="material-symbols-outlined text-secondary text-[14px]">check</span>
                <input type="text" value="${t}" onchange="state.activeCvJson.projects[${pIdx}].task_on_project[${tIdx}]=this.value; renderRawJsonViewer();" class="flex-1 bg-transparent text-xs text-text-primary outline-none">
                <button onclick="state.activeCvJson.projects[${pIdx}].task_on_project.splice(${tIdx}, 1); renderProjects(); renderRawJsonViewer();" class="text-outline hover:text-roseText">
                  <span class="material-symbols-outlined text-[14px]">close</span>
                </button>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Achievements -->
        <div>
          <div class="flex justify-between items-center text-[10px] font-bold text-text-secondary uppercase mb-1">
            <span>Ключевые достижения</span>
            <button onclick="addProjectAchievement(${pIdx})" class="text-amberText hover:underline">+ Добавить достижение</button>
          </div>
          <div class="flex flex-col gap-1.5">
            ${(p.achievements_in_project || []).map((a, aIdx) => `
              <div class="flex items-center gap-2 p-1.5 rounded-lg bg-surface-low border border-surface-container">
                <span class="material-symbols-outlined text-amberAccent text-[14px]">emoji_events</span>
                <input type="text" value="${a}" onchange="state.activeCvJson.projects[${pIdx}].achievements_in_project[${aIdx}]=this.value; renderRawJsonViewer();" class="flex-1 bg-transparent text-xs text-text-primary outline-none">
                <button onclick="state.activeCvJson.projects[${pIdx}].achievements_in_project.splice(${aIdx}, 1); renderProjects(); renderRawJsonViewer();" class="text-outline hover:text-roseText">
                  <span class="material-symbols-outlined text-[14px]">close</span>
                </button>
              </div>
            `).join('')}
          </div>
        </div>

        <div class="flex justify-end pt-1">
          <button onclick="state.activeCvJson.projects.splice(${pIdx}, 1); renderProjects(); renderRawJsonViewer();" class="text-roseText hover:underline text-xs flex items-center gap-1">
            <span class="material-symbols-outlined text-[14px]">delete</span>
            <span>Удалить проект</span>
          </button>
        </div>
      </div>
    </div>
  `).join('');
}

export function toggleProjectAccordion(pIdx) {
  const body = document.getElementById(`proj-body-${pIdx}`);
  const icon = document.getElementById(`proj-chevron-${pIdx}`);
  if (body.classList.contains('hidden')) {
    body.classList.remove('hidden');
    icon.textContent = 'expand_less';
  } else {
    body.classList.add('hidden');
    icon.textContent = 'expand_more';
  }
}

export function addProjectItem() {
  if (!state.activeCvJson.projects) state.activeCvJson.projects = [];
  state.activeCvJson.projects.push({
    place_time_raw: 'Новый проект',
    period: '2023 - 2024',
    role_in_project: 'Специалист',
    task_on_project: ['Основная задача'],
    achievements_in_project: ['Достижение'],
    skills_tools_in_project: ''
  });
  renderProjects();
  renderRawJsonViewer();
}

export function addProjectTask(pIdx) {
  if (!state.activeCvJson.projects[pIdx].task_on_project) state.activeCvJson.projects[pIdx].task_on_project = [];
  state.activeCvJson.projects[pIdx].task_on_project.push('Новая задача');
  renderProjects();
  renderRawJsonViewer();
}

export function addProjectAchievement(pIdx) {
  if (!state.activeCvJson.projects[pIdx].achievements_in_project) state.activeCvJson.projects[pIdx].achievements_in_project = [];
  state.activeCvJson.projects[pIdx].achievements_in_project.push('Новое достижение');
  renderProjects();
  renderRawJsonViewer();
}

export function syncActiveJsonFromInputs() {
  state.activeCvJson.fio = document.getElementById('val-fio').value.trim();
  state.activeCvJson.vacancy = document.getElementById('val-vacancy').value.trim();
  state.activeCvJson.total_year_work = document.getElementById('val-total-year').value.trim();
  state.activeCvJson.project_backround = document.getElementById('val-background').value.trim();
  state.activeCvJson.pitch = document.getElementById('val-pitch').value.trim();
  state.activeCvJson.languages = document.getElementById('val-languages').value.trim();
  state.activeCvJson.citizenship_location = document.getElementById('val-location').value.trim();
  state.activeCvJson.employment = document.getElementById('val-employment').value.trim();
  state.activeCvJson.status = document.getElementById('val-status').value.trim();
}

export function renderRawJsonViewer() {
  syncActiveJsonFromInputs();
  document.getElementById('raw-json-viewer').textContent = JSON.stringify(state.activeCvJson, null, 2);
}

export function toggleRawJson() {
  const card = document.getElementById('card-raw-json');
  if (card.classList.contains('hidden')) {
    renderRawJsonViewer();
    card.classList.remove('hidden');
    card.scrollIntoView({ behavior: 'smooth' });
  } else {
    card.classList.add('hidden');
  }
}

export function copyRawJson() {
  syncActiveJsonFromInputs();
  navigator.clipboard.writeText(JSON.stringify(state.activeCvJson, null, 2));
  alert('JSON скопирован в буфер обмена');
}

export async function saveDraftNotification() {
  if (!state.activeCvId) return;
  syncActiveJsonFromInputs();
  const btn = document.getElementById('btn-save-draft');
  const origHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<span class="material-symbols-outlined text-[16px] animate-spin">sync</span><span>Сохранение...</span>`;

  try {
    await api.saveDraft(state.activeCvId, state.activeCvJson);
    alert(`Черновик резюме #${state.activeCvId} успешно сохранен в базе данных.`);
  } catch (err) {
    alert('Ошибка сохранения черновика: ' + err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = origHtml;
  }
}

export async function submitValidation() {
  syncActiveJsonFromInputs();
  const btn = document.getElementById('btn-validate-submit');
  btn.disabled = true;
  btn.innerHTML = `<span class="material-symbols-outlined text-[18px] animate-spin">sync</span><span>Генерация DOCX...</span>`;

  try {
    const tplParam = window.currentActiveTemplateId || state.activeTemplateId;
    const updated = await api.validateCV(state.activeCvId, state.activeCvJson, tplParam);

    addSessionNotification({
      type: 'ready',
      cvId: state.activeCvId,
      title: 'Резюме утверждено',
      message: `${state.activeCvJson?.fio || 'Кандидат'} — DOCX сформирован и готов к скачиванию`,
      badge: 'Готово'
    });
    if (window.openResultPage) {
      window.openResultPage(state.activeCvId, updated);
    }
  } catch (e) {
    alert(e.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<span class="material-symbols-outlined text-[18px]">bolt</span><span>Подтвердить и docx</span>`;
  }
}
