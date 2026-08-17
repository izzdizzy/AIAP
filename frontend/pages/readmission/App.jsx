import React, { useState } from 'react';
import PatientForm from './components/PatientForm';
import RiskDashboard from './components/RiskDashboard';
import ChatInterface from './components/ChatInterface';
import { predictPatient, uploadPatientFile, sendChatMessage } from './services/api';

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
        const uploadResponse = await uploadPatientFile(file);

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
        predictionData = await predictPatient(patientInput);
        setPatientData({ form: { ...formData, ...uploadedData }, prediction: predictionData });
      } else {
        predictionData = await predictPatient(formData);
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

      const response = await sendChatMessage(chatContext, query);
      return response;
    } catch (err) {
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900">
      <header className="bg-gray-800 text-gray-100 shadow-md border-b border-gray-700">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">Healthcare Risk Assessment</h1>
          <p className="text-sm text-gray-400 mt-1">ML-Powered Clinical Decision Support</p>
        </div>
      </header>

      <div className="container mx-auto px-4 py-6">
        <div className="bg-yellow-900/30 border-l-4 border-yellow-500 p-4 mb-6">
          <p className="text-sm text-yellow-200">
            <strong>Medical Disclaimer:</strong> This tool is for educational and demonstration purposes only.
            It does not provide medical advice, diagnosis, or treatment. Always consult qualified healthcare professionals.
          </p>

        </div>
        <div className="mb-6">
          <button
            type="button"
            onClick={() => { window.location.hash = '/'; }}
            className="bg-gray-700 text-gray-200 px-4 py-2 rounded hover:bg-gray-600 transition"
          >
            Back to Home
          </button>
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
          <div className="bg-red-900/30 border border-red-700 text-red-300 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Removed top-level loading banner - typing indicator now appears inside chat stream */}

        {uploading && (
          <div className="bg-blue-900/30 border border-blue-700 text-blue-300 px-4 py-3 rounded mb-6">
            Uploading and parsing file...
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            {activeTab === 'assessment' && (
              <div className="bg-gray-800 p-6 rounded-lg shadow-lg border border-gray-700">
                <h2 className="text-xl font-semibold text-gray-100 mb-4">Patient Input</h2>
                <PatientForm onSubmit={handleFormSubmit} loading={loading || uploading} />
              </div>
            )}

            {activeTab === 'navigation' && patientData?.prediction && (
              <div className="bg-gray-800 p-6 rounded-lg shadow-lg border border-gray-700">
                <h2 className="text-xl font-semibold text-gray-100 mb-4">Patient Summary</h2>
                <div className="space-y-2 text-sm text-gray-300">
                  <p><span className="font-medium">Severity Score:</span> {patientData.prediction?.clinical_severity_score ?? 'N/A'}/100</p>
                  <p><span className="font-medium">Urgency:</span> {patientData.prediction?.urgency_level ?? 'N/A'}</p>
                  <p><span className="font-medium">Risk Category:</span> {patientData.prediction?.risk_category ?? 'N/A'}</p>
                  {patientData?.form && (
                    <>
                      <p><span className="font-medium">Age:</span> {patientData.form.age || patientData.form.age_numeric || 'N/A'}</p>
                      <p><span className="font-medium">CHAS Tier:</span> {patientData.form.chas_tier || 'N/A'}</p>
                      <p><span className="font-medium">Symptoms:</span> {Array.isArray(patientData.form.symptoms) ? patientData.form.symptoms.join(', ') : (Array.isArray(patientData.form.symptoms_list) ? patientData.form.symptoms_list.join(', ') : 'None')}</p>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="lg:col-span-2">
            {activeTab === 'assessment' && patientData?.prediction && (
              <div>
                <h2 className="text-xl font-semibold text-gray-100 mb-4">Risk Analysis Results</h2>
                <RiskDashboard prediction={patientData.prediction} />
              </div>
            )}

            {activeTab === 'assessment' && !patientData?.prediction && (
              <div className="bg-gray-800 p-12 rounded-lg shadow-lg border border-gray-700 text-center">
                <p className="text-gray-400">Enter patient data to see risk assessment results.</p>
              </div>
            )}

            {activeTab === 'navigation' && (
              <div>
                <h2 className="text-xl font-semibold text-gray-100 mb-4">AI Care Navigation</h2>
                <div className="h-96 lg:h-[500px]">
                  <ChatInterface
                    patientData={patientData}
                    onSendMessage={handleSendMessage}
                    loading={loading}
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
