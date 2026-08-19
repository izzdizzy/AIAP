/**
 * Diabetes Risk Classifier API Service
 * 
 * Communicates with the FastAPI backend at /diabetes endpoints.
 */

const API_BASE = 'http://localhost:8000/diabetes';

/**
 * Check if the diabetes model service is healthy and loaded.
 * @returns {Promise<{status: string, model_loaded: boolean}>}
 */
export async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE}/health`);
    if (!response.ok) {
      throw new Error('Diabetes service health check failed');
    }
    return await response.json();
  } catch (error) {
    console.error('Diabetes health check error:', error);
    return { status: 'error', model_loaded: false, error: error.message };
  }
}

/**
 * Predict diabetes risk from a health profile.
 * @param {Object} profile - Health profile data
 * @returns {Promise<{risk_label: string, risk_probability: number, risk_band: string, top_factors: string[]}>}
 */
export async function predictRisk(profile) {
  try {
    const response = await fetch(`${API_BASE}/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(profile),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Prediction failed');
    }
    
    const result = await response.json();
    
    // Persist Diabetes risk score to localStorage for cross-module state sharing
    if (typeof window !== 'undefined' && window.localStorage) {
      const diabetesRiskScore = Math.round((result.risk_probability || 0) * 100);
      window.localStorage.setItem('diabetes_risk_score', String(diabetesRiskScore));
    }
    
    return result;
  } catch (error) {
    console.error('Diabetes prediction error:', error);
    throw error;
  }
}

/**
 * Get diabetes risk prediction with AI-generated explanation.
 * @param {Object} profile - Health profile data
 * @returns {Promise<{prediction: Object, explanation: string}>}
 */
export async function explainRisk(profile) {
  try {
    const response = await fetch(`${API_BASE}/explain`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ profile }),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Explanation failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Diabetes explanation error:', error);
    throw error;
  }
}
