/**
 * Storage utility for persisting clinical form states, predictions, and AI chat messages across page refreshes.
 */

const CAD_KEY = 'cad-risk-assessment-state';
const DIABETES_KEY = 'diabetes-risk-assessment-state';
const READMISSION_KEY = 'readmission-risk-assessment-state';
const AI_MESSAGES_KEY = 'ai-workspace-chat-messages';
const SUBSIDY_TIER_KEY = 'patient-subsidy-tier';

export function loadStoredCADState() {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(CAD_KEY) || window.sessionStorage.getItem(CAD_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function saveStoredCADState(state) {
  if (typeof window === 'undefined') return;
  try {
    if (!state) {
      window.localStorage.removeItem(CAD_KEY);
      window.sessionStorage.removeItem(CAD_KEY);
    } else {
      window.localStorage.setItem(CAD_KEY, JSON.stringify(state));
    }
  } catch (e) {
    console.error('Failed to save CAD state:', e);
  }
}

export function loadStoredDiabetesState() {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(DIABETES_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function saveStoredDiabetesState(state) {
  if (typeof window === 'undefined') return;
  try {
    if (!state) {
      window.localStorage.removeItem(DIABETES_KEY);
    } else {
      window.localStorage.setItem(DIABETES_KEY, JSON.stringify(state));
    }
  } catch (e) {
    console.error('Failed to save Diabetes state:', e);
  }
}

export function loadStoredReadmissionState() {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(READMISSION_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function saveStoredReadmissionState(state) {
  if (typeof window === 'undefined') return;
  try {
    if (!state) {
      window.localStorage.removeItem(READMISSION_KEY);
    } else {
      window.localStorage.setItem(READMISSION_KEY, JSON.stringify(state));
    }
  } catch (e) {
    console.error('Failed to save Readmission state:', e);
  }
}

export function loadStoredAIMessages() {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(AI_MESSAGES_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function saveStoredAIMessages(messages) {
  if (typeof window === 'undefined') return;
  try {
    if (!messages) {
      window.localStorage.removeItem(AI_MESSAGES_KEY);
    } else {
      window.localStorage.setItem(AI_MESSAGES_KEY, JSON.stringify(messages));
    }
  } catch (e) {
    console.error('Failed to save AI messages:', e);
  }
}

export function loadStoredSubsidyTier() {
  if (typeof window === 'undefined') return 'CHAS Green';
  try {
    return window.localStorage.getItem(SUBSIDY_TIER_KEY) || 'CHAS Green';
  } catch {
    return 'CHAS Green';
  }
}

export function saveStoredSubsidyTier(tier) {
  if (typeof window === 'undefined') return;
  try {
    if (tier) {
      window.localStorage.setItem(SUBSIDY_TIER_KEY, tier);
    }
  } catch (e) {
    console.error('Failed to save subsidy tier:', e);
  }
}
