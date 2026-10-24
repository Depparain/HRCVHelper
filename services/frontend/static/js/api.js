// API Client for HRCVHelper Backend Gateway
import { API_BASE, state } from './state.js';

export const api = {
  // --- Auth ---
  async login(login, password) {
    const resp = await fetch(`${API_BASE}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ login, password }),
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || 'Неверный логин или пароль');
    }
    return await resp.json();
  },

  // --- CV Operations ---
  async getCVs(hrId = null) {
    const query = hrId ? `?hr_id=${encodeURIComponent(hrId)}` : '';
    const resp = await fetch(`${API_BASE}/api/v1/cv${query}`, {
      headers: state.getAuthHeaders(),
    });
    if (!resp.ok) throw new Error(`Ошибка загрузки списка резюме (${resp.status})`);
    return await resp.json();
  },

  async getCV(cvId) {
    const resp = await fetch(`${API_BASE}/api/v1/cv/${cvId}`, {
      headers: state.getAuthHeaders(),
    });
    if (!resp.ok) throw new Error(`Резюме #${cvId} не найдено`);
    return await resp.json();
  },

  async uploadCV(file, hrId) {
    const formData = new FormData();
    formData.append('file', file);
    if (hrId) formData.append('hr_id', hrId);

    const resp = await fetch(`${API_BASE}/api/v1/cv/upload`, {
      method: 'POST',
      headers: state.getAuthHeaders(),
      body: formData,
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || 'Ошибка при обработке файла');
    }
    return await resp.json();
  },

  async reworkCV(cvId, comment) {
    const resp = await fetch(`${API_BASE}/api/v1/cv/${cvId}/rework`, {
      method: 'PUT',
      headers: state.getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ comment }),
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || 'Не удалось отправить резюме на доработку');
    }
    return await resp.json();
  },

  async saveDraft(cvId, cvJson) {
    const resp = await fetch(`${API_BASE}/api/v1/cv/${cvId}/draft`, {
      method: 'PUT',
      headers: state.getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(cvJson),
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || 'Не удалось сохранить черновик');
    }
    return await resp.json();
  },

  async validateCV(cvId, cvJson, templateId = null) {
    const query = templateId ? `?template_id=${encodeURIComponent(templateId)}` : '';
    const resp = await fetch(`${API_BASE}/api/v1/cv/${cvId}/validate${query}`, {
      method: 'PUT',
      headers: state.getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(cvJson),
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || 'Ошибка сохранения и генерации DOCX');
    }
    return await resp.json();
  },

  // --- Admin Operations ---
  async getAdminHealth() {
    return await fetch(`${API_BASE}/api/v1/admin/health`, {
      headers: state.getAuthHeaders(),
    });
  },

  async getAdminLogs(limit = 100) {
    return await fetch(`${API_BASE}/api/v1/admin/logs?limit=${limit}`, {
      headers: state.getAuthHeaders(),
    });
  },

  // --- Templates & Fields Operations ---
  async getFieldsConfig() {
    const resp = await fetch(`${API_BASE}/api/v1/templates/fields`, {
      headers: state.getAuthHeaders(),
    });
    if (!resp.ok) throw new Error('Ошибка получения конфигурации полей');
    return await resp.json();
  },

  async saveFieldsConfig(payload) {
    const resp = await fetch(`${API_BASE}/api/v1/templates/fields`, {
      method: 'POST',
      headers: state.getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(payload),
    });
    if (!resp.ok) throw new Error('Ошибка сохранения конфигурации полей');
    return await resp.json();
  },

  async getTemplates() {
    const resp = await fetch(`${API_BASE}/api/v1/templates`, {
      headers: state.getAuthHeaders(),
    });
    if (!resp.ok) throw new Error('Ошибка загрузки шаблонов');
    return await resp.json();
  },

  async uploadTemplate(file, name, desc, makeActive) {
    const formData = new FormData();
    formData.append('file', file);
    if (name) formData.append('name', name);
    if (desc) formData.append('description', desc);
    formData.append('make_active', makeActive);

    const resp = await fetch(`${API_BASE}/api/v1/templates/upload`, {
      method: 'POST',
      headers: state.getAuthHeaders(),
      body: formData,
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || 'Ошибка загрузки шаблона');
    }
    return await resp.json();
  },

  async setActiveTemplate(templateId) {
    const resp = await fetch(`${API_BASE}/api/v1/templates/${templateId}/set-default`, {
      method: 'POST',
      headers: state.getAuthHeaders(),
    });
    if (!resp.ok) throw new Error('Ошибка назначения активного шаблона');
    return await resp.json();
  },

  async deleteTemplate(templateId) {
    const resp = await fetch(`${API_BASE}/api/v1/templates/${templateId}`, {
      method: 'DELETE',
      headers: state.getAuthHeaders(),
    });
    if (!resp.ok) throw new Error('Ошибка удаления шаблона');
    return await resp.json();
  },
};
