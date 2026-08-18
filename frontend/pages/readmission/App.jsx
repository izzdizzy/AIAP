import React, { useState } from 'react';
import PatientForm from '../../components/readmission/PatientForm';
import RiskDashboard from '../../components/readmission/RiskDashboard';
import ChatInterface from '../../components/readmission/ChatInterface';
import { predictReadmission, uploadReadmissionPatientFile, sendReadmissionChatMessage } from '../../services/readmission/api';
import '../../styles/readmission.css';

function App() {
  const [activeTab, setActiveTab] = useState('assessment');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [patientData, setPatientData] = useState({ form: null, prediction: null });
  const [error, setError] = useState(null);

  const handleFormSubmit = async (formData, file) => {
    setLoading(true);
    setError(null);

    try {
      let predictionData;

      if (file) {
        setUploading(true);
        const uploadResponse = await uploadReadmissionPatientFile(file);

        // Check for upload error - don't throw, just handle gracefully
        if (!uploadResponse?.success) {
          throw new Error(uploadResponse?.error || 'Failed to parse file');
        }

        // Safe access to patient_data with defaults
        const uploadedData = uploadResponse?.patient_data || {};

        // Map uploaded patient data to prediction request format with strict optional chaining
        const patientInput = {
          age: uploadedData?.age_numeric ?? undefined,
          prior_admissions: uploadedData?.total_prior_admissions ?? uploadedData?.number_inpatient ?? undefined,
          comorbidity_count: uploadedData?.comorbidity_count ?? undefined,
          medication_count: uploadedData?.total_medications ?? uploadedData?.num_medications ?? undefined,
          time_in_hospital: uploadedData?.time_in_hospital ?? undefined,
          number_diagnoses: uploadedData?.number_diagnoses ?? undefined,
          number_outpatient: uploadedData?.number_outpatient ?? undefined,
          number_emergency: uploadedData?.number_emergency ?? undefined,
          number_inpatient: uploadedData?.number_inpatient ?? undefined,
          admission_type_id: uploadedData?.admission_type_id ?? undefined,
          discharge_disposition_id: uploadedData?.discharge_disposition_id ?? undefined,
          admission_source_id: uploadedData?.admission_source_id ?? undefined,
          num_lab_procedures: uploadedData?.num_lab_procedures ?? undefined,
          num_procedures: uploadedData?.num_procedures ?? undefined,
          diabetes_diag_count: uploadedData?.diabetes_diag_count ?? undefined,
          metformin_encoded: uploadedData?.metformin_encoded ?? undefined,
          insulin_encoded: uploadedData?.insulin_encoded ?? undefined,
          on_insulin: uploadedData?.on_insulin ?? undefined,
        };

        // Clean undefined values
        Object.keys(patientInput).forEach(key => {
          if (patientInput[key] === undefined || patientInput[key] === null) {
            delete patientInput[key];
          }
        });

        // Get prediction using parsed data
        predictionData = await predictReadmission(patientInput);
        setPatientData({ form: { ...formData, ...uploadedData }, prediction: predictionData });
      } else {
        predictionData = await predictReadmission(formData);
        setPatientData({ form: formData, prediction: predictionData });
      }

      // Keep user on Risk Assessment tab to view clinical severity score and SHAP analysis
      // Do NOT auto-switch to navigation tab - let user explore results first
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to process patient data. Please try again.');
    } finally {
      setLoading(false);
      setUploading(false);
    }
  };

  const handleSendMessage = async (context, query) => {
    setLoading(true);
    try {
      // Build context object matching ChatRequest schema with strict optional chaining
      // Ensure symptoms array is correctly extracted from form data
      const symptomsArray = Array.isArray(patientData?.form?.symptoms)
        ? patientData.form.symptoms
        : (Array.isArray(patientData?.form?.symptoms_list)
          ? patientData.form.symptoms_list
          : []);

      const chatContext = {
        clinical_severity_score: patientData?.prediction?.clinical_severity_score ?? 0,
        symptoms: symptomsArray,
        chas_tier: patientData?.form?.chas_tier ?? null
      };

      const response = await sendReadmissionChatMessage(chatContext, query);
      return response;
    } catch (err) {
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-stack">
      <div>
        <div className="alert-banner alert-banner--info" style={{ marginBottom: '16px' }}>
          <span><strong>Medical Disclaimer:</strong> This tool is for educational and decision support purposes only. It does not provide medical diagnosis or treatment. Always consult qualified healthcare professionals.</span>
        </div>

        <div className="flex border-b border-gray-700 mb-6">
          <button
            onClick={() => setActiveTab('assessment')}
            className={`px-6 py-3 font-medium ${activeTab === 'assessment'
              ? 'border-b-2 border-blue-500 text-blue-400'
              : 'text-gray-400 hover:text-gray-200'
              }`}
          >
            Risk Assessment
          </button>
          <button
            onClick={() => setActiveTab('navigation')}
            className={`px-6 py-3 font-medium ${activeTab === 'navigation'
              ? 'border-b-2 border-blue-500 text-blue-400'
              : 'text-gray-400 hover:text-gray-200'
              }`}
          >
            Care Navigation
          </button>
        </div>

        {error && (
          <div className="alert-banner alert-banner--danger" role="alert">
            {error}
          </div>
        )}

        {/* Removed top-level loading banner - typing indicator now appears inside chat stream */}

        {uploading && (
          <div className="bg-blue-900/30 border border-blue-700 text-blue-300 px-4 py-3 rounded mb-6">
            Uploading and parsing file...
          </div>
        )}

        {activeTab === 'assessment' && (
          <PatientForm
            onSubmit={handleFormSubmit}
            loading={loading || uploading}
            prediction={patientData?.prediction}
            onResetPrediction={() => setPatientData(prev => ({ ...prev, prediction: null }))}
          />
        )}

        {activeTab === 'navigation' && (
          <div className="assessment-layout">
            <div className="assessment-main">
              <div className="section-card">
                <h2>AI Care Navigation</h2>
                <p style={{ color: 'var(--text-muted)', marginBottom: '16px' }}>
                  Post-discharge care guidance and interactive clinical follow-up assistant.
                </p>
                <div style={{ height: '500px' }}>
                  <ChatInterface
                    patientData={patientData}
                    onSendMessage={handleSendMessage}
                    loading={loading}
                  />
                </div>
              </div>
            </div>

            {patientData?.prediction && (
              <div className="section-card" style={{ padding: '20px' }}>
                <h3>Patient Case Summary</h3>
                <div style={{ display: 'grid', gap: '8px', fontSize: '0.88rem', marginTop: '12px', color: 'var(--text)' }}>
                  <p><strong>Severity Score:</strong> {patientData.prediction?.clinical_severity_score ?? 'N/A'}/100</p>
                  <p><strong>Urgency Level:</strong> {patientData.prediction?.urgency_level ?? 'N/A'}</p>
                  <p><strong>Risk Category:</strong> {patientData.prediction?.risk_category ?? 'N/A'}</p>
                  {patientData?.form && (
                    <>
                      <p><strong>Age Group:</strong> {patientData.form.age || patientData.form.age_numeric || 'N/A'}</p>
                      <p><strong>CHAS Tier:</strong> {patientData.form.chas_tier || 'N/A'}</p>
                      <p><strong>Active Symptoms:</strong> {Array.isArray(patientData.form.symptoms) && patientData.form.symptoms.length > 0 ? patientData.form.symptoms.join(', ') : 'None logged'}</p>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
