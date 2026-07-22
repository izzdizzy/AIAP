import axios from 'axios';

const API_BASE = '/api';

/**
 * Send prediction request to FastAPI backend
 * @param {Object} data - Patient data matching PatientData Pydantic model
 * @returns {Promise<Object>} PredictionResponse with severity score, urgency level, and SHAP analysis
 */
export const predictPatient = async (data) => {
  const response = await axios.post(`${API_BASE}/predict`, data);
  return response.data;
};

/**
 * Upload CSV/Excel patient file for parsing
 * @param {File} file - Patient data file (CSV or Excel format)
 * @returns {Promise<Object>} UploadResponse with parsed patient_data
 */
export const uploadPatientFile = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await axios.post(`${API_BASE}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

/**
 * Send chat message to Gen AI service with patient context
 * @param {Object} context - Patient context including clinical_severity_score, symptoms, chas_tier
 * @param {string} query - User's question or message
 * @returns {Promise<Object>} ChatResponse with AI-generated healthcare advice and is_fallback flag
 */
export const sendChatMessage = async (context, query) => {
  // Build ChatRequest matching backend expectations
  // Ensure all required fields are explicitly included in the payload
  const requestBody = {
    clinical_severity_score: context.clinical_severity_score || 0,
    symptoms: Array.isArray(context.symptoms) ? context.symptoms : [],
    chas_tier: context.chas_tier || null,
    user_query: query
  };
  
  const response = await axios.post(`${API_BASE}/chat`, requestBody);
  return response.data;
};

/**
 * Get model metadata and performance metrics
 * @returns {Promise<Object>} ModelInfoResponse with ROC-AUC, recall, threshold info
 */
export const getModelInfo = async () => {
  const response = await axios.get(`${API_BASE}/model-info`);
  return response.data;
};
