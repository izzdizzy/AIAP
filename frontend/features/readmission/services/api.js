/**
 * Hospital Readmission Prediction Service
 * 
 * This module provides API client functions for the Hospital Readmission module.
 * Points directly to the mounted FastAPI sub-app on port 8000.
 */

const API_BASE = 'http://localhost:8000/readmission/api';

/**
 * Predict hospital readmission risk for a patient
 * @param {Object} patientData - Patient clinical data
 * @returns {Promise<Object>} Prediction response with severity score and SHAP analysis
 */
export async function predictReadmission(patientData) {
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
    console.error('[Hospital API] Prediction error:', error);
    throw error;
  }
}

/**
 * Get AI care navigation advice for hospital readmission patient
 * @param {Object} chatContext - Context including severity score, symptoms, CHAS tier
 * @param {string} userQuery - User's question or message
 * @returns {Promise<Object>} Chat response with AI-generated advice
 */
export async function sendReadmissionChatMessage(chatContext, userQuery) {
  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ...chatContext,
        user_query: userQuery,
        history: chatContext?.history || [],
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Chat request failed');
    }

    return await response.json();
  } catch (error) {
    console.error('[Hospital API] Chat error:', error);
    throw error;
  }
}

/**
 * Upload patient data file (CSV or Excel)
 * @param {File} file - Patient data file
 * @returns {Promise<Object>} Upload response with parsed patient data
 */
export async function uploadReadmissionPatientFile(file) {
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
    console.error('[Hospital API] Upload error:', error);
    throw error;
  }
}

/**
 * Get model information and performance metrics
 * @returns {Promise<Object>} Model info response
 */
export async function getReadmissionModelInfo() {
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
    console.error('[Hospital API] Model info error:', error);
    throw error;
  }
}

/**
 * Health check endpoint
 * Note: The health endpoint is mounted directly at /readmission/health, not under /readmission/api
 * @returns {Promise<Object>} Health status
 */
export async function checkReadmissionHealth() {
  try {
    const response = await fetch('http://localhost:8000/readmission/health', {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error('Health check failed');
    }

    return await response.json();
  } catch (error) {
    console.error('[Hospital API] Health check error:', error);
    throw error;
  }
}