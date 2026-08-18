const STORAGE_KEY = 'cad-risk-assessment-state';

export function loadStoredAssessmentState() {
  if (typeof window === 'undefined') {
    return null;
  }

  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function saveStoredAssessmentState(state) {
  if (typeof window === 'undefined') {
    return;
  }

  if (!state) {
    window.sessionStorage.removeItem(STORAGE_KEY);
    return;
  }

  window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}