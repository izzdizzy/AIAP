import apiClient from '../../../services/apiClient';

export function saveAssessment(profile) {
  return apiClient('/diabetes/history', {
    method: 'POST',
    body: JSON.stringify({ profile })
  });
}

export function getHistory() {
  return apiClient('/diabetes/history');
}

export function deleteAssessment(id) {
  return apiClient(`/diabetes/history/${id}`, { method: 'DELETE' });
}

// Generic history for modules without their own history endpoint (cad, readmission).

export function saveModuleAssessment(module, payload, result) {
  return apiClient(`/history/${module}`, {
    method: 'POST',
    body: JSON.stringify({ payload, result })
  });
}

export function getModuleHistory(module) {
  return apiClient(`/history/${module}`);
}

export function deleteModuleAssessment(module, id) {
  return apiClient(`/history/${module}/${id}`, { method: 'DELETE' });
}
