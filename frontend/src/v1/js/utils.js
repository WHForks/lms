import { get as getCookie } from 'es-cookie';
import template from 'lodash-es/template';
import { renderComponent } from './react_app';

export function getLocalStorageKey(textarea) {
  return window.location.pathname.replace(/\//g, '_') + '_' + textarea.name;
}

export function csrfSafeMethod(method) {
  // These HTTP methods do not require CSRF protection
  return /^(GET|HEAD|OPTIONS|TRACE)$/.test(method);
}

export function getCSRFToken() {
  return getCookie(window.__CSC__.config.csrfCookieName);
}

export function getTemplate(id) {
  return template(document.getElementById(id)?.innerHTML??"");
}

export function createNotification(msg, theme = "default", options = {}) {
  const opts = { position: "bottom-right", ...options };

  if (typeof $.jGrowl === "function") {
    $.jGrowl(msg, { theme: theme, ...opts });
  } else {
    console.error("Notification:", theme, msg);
  }
}

export function showComponentError(error, msg = 'An error occurred while loading the component') {
  console.error(error);
  createNotification(msg, 'error');
}

// TODO: share with v2?
export function getSections() {
  if (document.body.hasAttribute('data-init-sections')) {
    let sections = document.body.getAttribute('data-init-sections');
    return sections.split(',');
  } else {
    return [];
  }
}

export function loadReactApplications() {
  let reactApps = document.querySelectorAll(".__react-app");
  if (reactApps.length > 0) {
    Array.from(reactApps).forEach(renderComponent);
  }
}

export function escapeHTML(data) {
  return data
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}
