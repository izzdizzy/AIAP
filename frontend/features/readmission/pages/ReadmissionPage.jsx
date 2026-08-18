import React, { useState } from 'react';
import PatientForm from '../components/PatientForm';
import { predictReadmission } from '../services/api';

export default function ReadmissionApp({ onBackToLanding }) {
  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState(null);
  const [error, setError] = useState(null);

  async function handleSubmit(formData) {
    setLoading(true);
    setError(null);
    try {
      const result = await predictReadmission(formData);
      setPrediction(result);
    } catch (err) {
      setError(err.message || 'Failed to calculate readmission risk.');
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    setPrediction(null);
    setError(null);
  }

  return (
    <div className="page-stack">
      {error && (
        <div className="alert-banner alert-banner--danger" role="alert">
          <strong>Error:</strong> {error}
        </div>
      )}

      <PatientForm
        onSubmit={handleSubmit}
        loading={loading}
        prediction={prediction}
        onResetPrediction={handleReset}
      />
    </div>
  );
}
