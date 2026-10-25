// State management for HRCVHelper

export const API_BASE = window.location.origin.includes(':8501') ? 'http://localhost:8000' : window.location.origin;

export const state = {
  currentToken: localStorage.getItem('hrcv_token') || null,
  currentUser: JSON.parse(localStorage.getItem('hrcv_user') || 'null'),
  cvList: [],
  currentTab: 'ALL',
  selectedUploadFile: null,
  activeCvId: null,
  activeCvJson: null,
  adminInterval: null,
  adminAutoRefresh: true,
  adminLogsList: [],
  dashboardPollInterval: null,
  notificationsList: [],
  readNotificationIds: new Set(JSON.parse(localStorage.getItem('hrcv_read_notifications') || '[]')),
  currentFieldsConfig: [],
  currentTemplatesList: [],
  activeTemplateId: 'default',
  selectedTemplateUploadFile: null,

  setToken(token) {
    this.currentToken = token;
    if (token) {
      localStorage.setItem('hrcv_token', token);
    } else {
      localStorage.removeItem('hrcv_token');
    }
  },

  setUser(user) {
    this.currentUser = user;
    if (user) {
      localStorage.setItem('hrcv_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('hrcv_user');
    }
  },

  saveReadNotifications() {
    localStorage.setItem('hrcv_read_notifications', JSON.stringify(Array.from(this.readNotificationIds)));
  },

  getAuthHeaders(extraHeaders = {}) {
    const headers = { ...extraHeaders };
    const token = this.currentToken || localStorage.getItem('hrcv_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }
};

// Mirroring on window for backward compatibility
window.HRCV_STATE = state;
