import { loadStoredCADState, saveStoredCADState } from '../../../services/storage';

export function loadStoredAssessmentState() {
  return loadStoredCADState();
}

export function saveStoredAssessmentState(state) {
  saveStoredCADState(state);
}