import { buildAssessmentPayload } from '../utils/payload';
import { getLifestyleAdvice, getRiskLevel } from '../utils/risk';

const DEFAULT_API_BASE_URL = 'http://localhost:8000';

function normalizeApiResponse(data) {
  return {
    // Keep the original backend response for the chatbot
    backendPrediction: data,

    // Frontend-friendly fields
    prediction: data.prediction,
    rawProbability: data.raw_probability,
    riskProbability: data.risk_probability,
    riskPercent: `${data.risk_percent.toFixed(1)}%`,
    riskLevel: data.risk_level,
    topFactors: data.top_factors ?? [],
    lifestyleAdvice:
      data.lifestyle_advice ?? getLifestyleAdvice(data.risk_level),
    medicalDisclaimer: data.medical_disclaimer ?? ''
  };
}

export async function submitAssessment(values) {
  const payload = buildAssessmentPayload(values);
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL;

  try {
    const response = await fetch(`${apiBaseUrl}/api/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`Prediction request failed with status ${response.status}`);
    }

    const data = await response.json();
    const prediction = normalizeApiResponse(data);

    // Persist CAD risk score to localStorage for cross-module state sharing
    if (typeof window !== 'undefined' && window.localStorage) {
      const cadRiskScore = Math.round(data.risk_percent || (data.risk_probability * 100) || 0);
      window.localStorage.setItem('cad_risk_score', String(cadRiskScore));
    }

    return {
        assessment: payload,
        prediction
    };
  } catch (error) {
    throw new Error(
        'Unable to connect to the prediction service. Please try again.'
    );
}
}
