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
        
        if (!uploadResponse.success) {
          throw new Error(uploadResponse.error || 'Failed to parse file');
        }
        
        // Map uploaded patient data to prediction request format
        const patientInput = {
          age: uploadResponse.patient_data?.age_numeric,
          prior_admissions: uploadResponse.patient_data?.total_prior_admissions || uploadResponse.patient_data?.number_inpatient,
          comorbidity_count: uploadResponse.patient_data?.comorbidity_count,
          medication_count: uploadResponse.patient_data?.total_medications || uploadResponse.patient_data?.num_medications,
          time_in_hospital: uploadResponse.patient_data?.time_in_hospital,
          number_diagnoses: uploadResponse.patient_data?.number_diagnoses,
          number_outpatient: uploadResponse.patient_data?.number_outpatient,
          number_emergency: uploadResponse.patient_data?.number_emergency,
          number_inpatient: uploadResponse.patient_data?.number_inpatient,
          admission_type_id: uploadResponse.patient_data?.admission_type_id,
          discharge_disposition_id: uploadResponse.patient_data?.discharge_disposition_id,
          admission_source_id: uploadResponse.patient_data?.admission_source_id,
          num_lab_procedures: uploadResponse.patient_data?.num_lab_procedures,
          num_procedures: uploadResponse.patient_data?.num_procedures,
          diabetes_diag_count: uploadResponse.patient_data?.diabetes_diag_count,
          metformin_encoded: uploadResponse.patient_data?.metformin_encoded,
          insulin_encoded: uploadResponse.patient_data?.insulin_encoded,
          on_insulin: uploadResponse.patient_data?.on_insulin,
        };
        
        // Clean undefined values
        Object.keys(patientInput).forEach(key => {
          if (patientInput[key] === undefined || patientInput[key] === null) {
            delete patientInput[key];
          }
        });
        
        // Get prediction using parsed data
        predictionData = await predictPatient(patientInput);
        setPatientData({ form: { ...formData, ...uploadResponse.patient_data }, prediction: predictionData });
      } else {
        predictionData = await predictPatient(formData);
        setPatientData({ form: formData, prediction: predictionData });
      }

      setActiveTab('navigation');
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to process patient data. Please try again.');
    } finally {
      setLoading(false);
      setUploading(false);
    }
  };

  const handleSendMessage = async (context, query) => {
    setLoading(true);
    try {
      // Build context object matching ChatRequest schema
      const chatContext = {
        clinical_severity_score: patientData.prediction?.clinical_severity_score || 0,
        symptoms: patientData.form?.symptoms_list || patientData.form?.symptoms || [],
        chas_tier: patientData.form?.chas_tier || null
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
          <h1 className="text-2xl font-bold">IT3100 PR2 - Healthcare Risk Assessment</h1>
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

        <div className="flex border-b border-gray-700 mb-6">
          <button
            onClick={() => setActiveTab('assessment')}
            className={`px-6 py-3 font-medium ${
              activeTab === 'assessment'
                ? 'border-b-2 border-blue-500 text-blue-400'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            Risk Assessment
          </button>
          <button
            onClick={() => setActiveTab('navigation')}
            className={`px-6 py-3 font-medium ${
              activeTab === 'navigation'
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

        {loading && !uploading && (
          <div className="bg-blue-900/30 border border-blue-700 text-blue-300 px-4 py-3 rounded mb-6">
            Processing prediction...
          </div>
        )}

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

            {activeTab === 'navigation' && patientData.prediction && (
              <div className="bg-gray-800 p-6 rounded-lg shadow-lg border border-gray-700">
                <h2 className="text-xl font-semibold text-gray-100 mb-4">Patient Summary</h2>
                <div className="space-y-2 text-sm text-gray-300">
                  <p><span className="font-medium">Severity Score:</span> {patientData.prediction.clinical_severity_score}/100</p>
                  <p><span className="font-medium">Urgency:</span> {patientData.prediction.urgency_level}</p>
                  <p><span className="font-medium">Risk Category:</span> {patientData.prediction.risk_category}</p>
                  {patientData.form && (
                    <>
                      <p><span className="font-medium">Age:</span> {patientData.form.age || patientData.form.age_numeric || 'N/A'}</p>
                      <p><span className="font-medium">CHAS Tier:</span> {patientData.form.chas_tier}</p>
                      <p><span className="font-medium">Symptoms:</span> {patientData.form.symptoms?.join(', ') || patientData.form.symptoms_list?.join(', ') || 'None'}</p>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="lg:col-span-2">
            {activeTab === 'assessment' && patientData.prediction && (
              <div>
                <h2 className="text-xl font-semibold text-gray-100 mb-4">Risk Analysis Results</h2>
                <RiskDashboard prediction={patientData.prediction} />
              </div>
            )}

            {activeTab === 'assessment' && !patientData.prediction && (
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
