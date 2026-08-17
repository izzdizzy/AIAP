/**
 * Diabetes Readmission Prediction Service
 * 
 * This module provides API client functions for the Diabetes Readmission module.
 * All endpoints are prefixed with /api/v1/diabetes to avoid conflicts with CAD endpoints.
 */

const API_BASE = '/api/v1/diabetes';

/**
 * Predict diabetes readmission risk for a patient
 * @param {Object} patientData - Patient clinical data
 * @returns {Promise<Object>} Prediction response with severity score and SHAP analysis
 */
export async function predictDiabetesReadmission(patientData) {
  try {
    const response = await fetch(`${API_BASE}/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(patientData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Prediction failed');
    }

    return await response.json();
  } catch (error) {
    console.error('[Diabetes API] Prediction error:', error);
    throw error;
  }
}

/**
 * Get AI care navigation advice for diabetes patient
 * @param {Object} chatContext - Context including severity score, symptoms, CHAS tier
 * @param {string} userQuery - User's question or message
 * @returns {Promise<Object>} Chat response with AI-generated advice
 */
export async function sendDiabetesChatMessage(chatContext, userQuery) {
  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ...chatContext,
        user_query: userQuery,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Chat request failed');
    }

    return await response.json();
  } catch (error) {
    console.error('[Diabetes API] Chat error:', error);
    throw error;
  }
}

/**
 * Upload patient data file (CSV or Excel)
 * @param {File} file - Patient data file
 * @returns {Promise<Object>} Upload response with parsed patient data
 */
export async function uploadDiabetesPatientFile(file) {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Upload failed');
    }

    return await response.json();
  } catch (error) {
    console.error('[Diabetes API] Upload error:', error);
    throw error;
  }
}

/**
 * Get model information and performance metrics
 * @returns {Promise<Object>} Model info response
 */
export async function getDiabetesModelInfo() {
  try {
    const response = await fetch(`${API_BASE}/model-info`, {
      method: 'GET',
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to retrieve model info');
    }

    return await response.json();
  } catch (error) {
    console.error('[Diabetes API] Model info error:', error);
    throw error;
  }
}

/**
 * Health check endpoint
 * @returns {Promise<Object>} Health status
 */
export async function checkDiabetesHealth() {
  try {
    const response = await fetch(`${API_BASE}/health`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error('Health check failed');
    }

    return await response.json();
  } catch (error) {
    console.error('[Diabetes API] Health check error:', error);
    throw error;
  }
}
