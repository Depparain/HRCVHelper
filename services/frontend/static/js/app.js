// HRCVHelper Main Application Entry Point
import { state, API_BASE } from './state.js';
import { api } from './api.js';
import * as notifications from './notifications.js';
import * as auth from './views/auth.js';
import * as dashboard from './views/dashboard.js';
import * as validation from './views/validation.js';
import * as admin from './views/admin.js';
import * as templates from './views/templates.js';
import * as modals from './components/modals.js';

// Expose state and API globally
window.API_BASE = API_BASE;
window.state = state;
window.api = api;

// Expose all view and component functions to window for inline HTML onclick handlers
const exposedMethods = {
  // Notifications
  toggleNotificationsMenu: notifications.toggleNotificationsMenu,
  formatTimeAgo: notifications.formatTimeAgo,
  updateNotificationsFromCVs: notifications.updateNotificationsFromCVs,
  addSessionNotification: notifications.addSessionNotification,
  renderNotificationsUI: notifications.renderNotificationsUI,
  handleNotificationClick: notifications.handleNotificationClick,
  markAllNotificationsAsRead: notifications.markAllNotificationsAsRead,
  clearAllNotifications: notifications.clearAllNotifications,

  // Auth & Nav
  togglePassVisibility: auth.togglePassVisibility,
  handleLogin: auth.handleLogin,
  logout: auth.logout,
  hideAllViews: auth.hideAllViews,
  showLogin: auth.showLogin,
  showDashboard: auth.showDashboard,
  showTemplates: auth.showTemplates,
  showAdmin: auth.showAdmin,
  updateNavActive: auth.updateNavActive,

  // Dashboard
  loadCVs: dashboard.loadCVs,
  updateMetrics: dashboard.updateMetrics,
  setTab: dashboard.setTab,
  renderCVTable: dashboard.renderCVTable,
  openUploadModal: dashboard.openUploadModal,
  closeUploadModal: dashboard.closeUploadModal,
  handleFileSelect: dashboard.handleFileSelect,
  clearSelectedFile: dashboard.clearSelectedFile,
  startFileUpload: dashboard.startFileUpload,

  // Validation
  openValidationPage: validation.openValidationPage,
  renderSkills: validation.renderSkills,
  addSkillItem: validation.addSkillItem,
  removeSkillItem: validation.removeSkillItem,
  renderEducation: validation.renderEducation,
  addEducationItem: validation.addEducationItem,
  renderProjects: validation.renderProjects,
  toggleProjectAccordion: validation.toggleProjectAccordion,
  addProjectItem: validation.addProjectItem,
  addProjectTask: validation.addProjectTask,
  addProjectAchievement: validation.addProjectAchievement,
  syncActiveJsonFromInputs: validation.syncActiveJsonFromInputs,
  renderRawJsonViewer: validation.renderRawJsonViewer,
  toggleRawJson: validation.toggleRawJson,
  copyRawJson: validation.copyRawJson,
  saveDraftNotification: validation.saveDraftNotification,
  submitValidation: validation.submitValidation,

  // Admin
  loadAdminData: admin.loadAdminData,
  renderAdminHealthCards: admin.renderAdminHealthCards,
  renderAdminLogs: admin.renderAdminLogs,
  toggleAdminAutoRefresh: admin.toggleAdminAutoRefresh,
  copyAdminLogs: admin.copyAdminLogs,

  // Templates
  loadTemplatesData: templates.loadTemplatesData,
  renderFieldsList: templates.renderFieldsList,
  onFieldCheckboxChange: templates.onFieldCheckboxChange,
  updateFieldsCounter: templates.updateFieldsCounter,
  applyPreset: templates.applyPreset,
  toggleAllFields: templates.toggleAllFields,
  saveAndApplyFields: templates.saveAndApplyFields,
  renderTemplatesList: templates.renderTemplatesList,
  setActiveTemplate: templates.setActiveTemplate,
  downloadTemplate: templates.downloadTemplate,
  deleteTemplate: templates.deleteTemplate,
  handleTemplateFileSelect: templates.handleTemplateFileSelect,
  handleTemplateUpload: templates.handleTemplateUpload,

  // Modals
  openReworkModal: modals.openReworkModal,
  closeReworkModal: modals.closeReworkModal,
  appendReworkChip: modals.appendReworkChip,
  submitReworkWithComment: modals.submitReworkWithComment,
  openResultPage: modals.openResultPage,
  copyDownloadUrl: modals.copyDownloadUrl,
  openTemplateInstructionModal: modals.openTemplateInstructionModal,
  closeTemplateInstructionModal: modals.closeTemplateInstructionModal,
  copyTag: modals.copyTag,
  copyAllActiveTags: modals.copyAllActiveTags,
  copyProjectLoopCode: modals.copyProjectLoopCode,
  downloadActiveOrBaseTemplate: modals.downloadActiveOrBaseTemplate,
};

Object.assign(window, exposedMethods);

// Global properties for compatibility
Object.defineProperty(window, 'currentToken', {
  get: () => state.currentToken,
  set: (v) => state.setToken(v)
});
Object.defineProperty(window, 'currentUser', {
  get: () => state.currentUser,
  set: (v) => state.setUser(v)
});
Object.defineProperty(window, 'activeCvId', {
  get: () => state.activeCvId,
  set: (v) => { state.activeCvId = v; }
});
Object.defineProperty(window, 'activeCvJson', {
  get: () => state.activeCvJson,
  set: (v) => { state.activeCvJson = v; }
});

// Initial boot
window.addEventListener('DOMContentLoaded', () => {
  // Bind form submits
  const loginForm = document.getElementById('form-login');
  if (loginForm) {
    loginForm.addEventListener('submit', auth.handleLogin);
  }

  const tplForm = document.getElementById('form-upload-template');
  if (tplForm) {
    tplForm.addEventListener('submit', templates.handleTemplateUpload);
  }

  // Check auth and route to view
  if (state.currentToken && state.currentUser) {
    auth.showDashboard();
  } else {
    auth.showLogin();
  }
});
