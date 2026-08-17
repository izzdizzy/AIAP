import React, { useState } from 'react';
import './tailwind-readmission.css';
import { predictReadmission, uploadReadmissionPatientFile, sendReadmissionChatMessage } from '../services/readmission/api';

/**
 * Hospital Readmission Assessment Page
 * 
 * This page provides the complete hospital readmission prediction workflow:
 * - Patient data input form
 * - File upload for CSV/Excel data
 * - Risk dashboard with Clinical Severity Score and SHAP analysis
 * - AI care navigation chat interface
 * 
 * Integration note: This is a self-contained page that can be added to the
 * main App.jsx routing structure without modifying existing CAD pages.
 */
export default function ReadmissionAssessmentPage({ onBackToLanding }) {
  const [activeTab, setActiveTab] = useState('assessment');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [patientData, setPatientData] = useState({ form: null, prediction: null });
  const [error, setError] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);

  // Handle back navigation with error handling
  const handleBackToMain = () => {
    if (onBackToLanding) {
      onBackToLanding();
    } else {
      // Fallback: directly modify hash if prop not provided
      window.location.hash = '';
    }
  };

  // Handle form submission for hospital readmission prediction
  const handleFormSubmit = async (formData, file) => {
    setLoading(true);
    setError(null);

    try {
      let predictionData;

      if (file) {
        // File upload path
        setUploading(true);
        const uploadResponse = await uploadReadmissionPatientFile(file);
        
        // Check for upload error
        if (!uploadResponse?.success) {
          throw new Error(uploadResponse?.error || 'Failed to parse file');
        }
        
        // Safe access to patient_data with defaults
        const uploadedData = uploadResponse?.patient_data || {};
        
        // Map uploaded patient data to prediction request format
        const patientInput = {
          age: uploadedData?.age ?? undefined,
          prior_admissions: uploadedData?.prior_admissions ?? uploadedData?.number_inpatient ?? undefined,
          comorbidity_count: uploadedData?.comorbidity_count ?? undefined,
          medication_count: uploadedData?.medication_count ?? uploadedData?.total_medications ?? undefined,
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
        // Direct form submission path
        predictionData = await predictReadmission(formData);
        setPatientData({ form: formData, prediction: predictionData });
      }

      // Keep user on Risk Assessment tab to view results
    } catch (err) {
      setError(err?.message || 'Failed to process patient data. Please try again.');
    } finally {
      setLoading(false);
      setUploading(false);
    }
  };

  // Handle chat message for care navigation
  const handleSendMessage = async (context, query) => {
    setChatLoading(true);
    try {
      // Build context object matching API schema
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
      
      // Add messages to chat history
      setChatMessages(prev => [
        ...prev,
        { role: 'user', content: query },
        { role: 'assistant', content: response.response }
      ]);
      
      return response;
    } catch (err) {
      console.error('[Hospital Readmission Page] Chat error:', err);
      throw err;
    } finally {
      setChatLoading(false);
    }
  };

  // Handle file upload
  const handleFileUpload = async (file) => {
    setUploading(true);
    setError(null);
    
    try {
      const uploadResponse = await uploadReadmissionPatientFile(file);
      
      if (!uploadResponse?.success) {
        throw new Error(uploadResponse?.error || 'Failed to parse file');
      }
      
      // Pre-fill form with uploaded data (implementation depends on PatientForm component)
      return uploadResponse.patient_data;
    } catch (err) {
      setError(err?.message || 'Failed to upload file');
      return null;
    } finally {
      setUploading(false);
    }
  };

  // Reset assessment
  const handleReset = () => {
    setPatientData({ form: null, prediction: null });
    setChatMessages([]);
    setError(null);
    setActiveTab('assessment');
  };

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header with Back to Main Menu button */}
      <header className="bg-gray-800 text-gray-100 shadow-md border-b border-gray-700">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={handleBackToMain}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.5rem 1rem',
                backgroundColor: '#374151',
                color: '#f3f4f6',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: '500'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#4b5563';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#374151';
              }}
            >
              <svg style={{ width: '16px', height: '16px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back to Main Menu
            </button>
          </div>
          <div>
            <h1 className="text-2xl font-bold">Hospital Readmission Prediction</h1>
            <p className="text-sm text-gray-400 mt-1">ML-Powered Clinical Decision Support for Hospital Readmission Risk</p>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-6">
        {/* Medical Disclaimer */}
        <div className="bg-yellow-900/30 border-l-4 border-yellow-500 p-4 mb-6">
          <p className="text-sm text-yellow-200">
            <strong>Medical Disclaimer:</strong> This tool is for educational and demonstration purposes only. 
            It does not provide medical advice, diagnosis, or treatment. Always consult qualified healthcare professionals.
          </p>
        </div>

        {/* Tab Navigation */}
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
            disabled={!patientData?.prediction}
            className={`px-6 py-3 font-medium ${
              !patientData?.prediction ? 'opacity-50 cursor-not-allowed' : ''
            } ${
              activeTab === 'navigation'
                ? 'border-b-2 border-blue-500 text-blue-400'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            Care Navigation
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-900/30 border border-red-700 text-red-300 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Loading States */}
        {uploading && (
          <div className="bg-blue-900/30 border border-blue-700 text-blue-300 px-4 py-3 rounded mb-6">
            Uploading and parsing file...
          </div>
        )}

        {chatLoading && (
          <div className="bg-blue-900/30 border border-blue-700 text-blue-300 px-4 py-3 rounded mb-6">
            AI assistant is typing...
          </div>
        )}

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Input/Summary */}
          <div className="lg:col-span-1">
            {activeTab === 'assessment' && (
              <div className="bg-gray-800 p-6 rounded-lg shadow-lg border border-gray-700">
                <h2 className="text-xl font-semibold text-gray-100 mb-4">Patient Input</h2>
                {/* Note: PatientForm component should be created/ported from conflicts/my_components/ */}
                <div className="text-gray-400 text-sm">
                  <p>Patient form component would be rendered here.</p>
                  <p className="mt-2">The form should collect:</p>
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>Age</li>
                    <li>Prior admissions count</li>
                    <li>Comorbidity count</li>
                    <li>Medication count</li>
                    <li>Hospital stay details</li>
                    <li>CHAS tier (for Singapore context)</li>
                    <li>Symptoms</li>
                  </ul>
                  <p className="mt-2 text-xs">
                    Form implementation pending - use conflicts/my_components/PatientForm.jsx as reference.
                  </p>
                </div>
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

          {/* Right Column - Results/Chat */}
          <div className="lg:col-span-2">
            {activeTab === 'assessment' && patientData?.prediction && (
              <div>
                <h2 className="text-xl font-semibold text-gray-100 mb-4">Risk Analysis Results</h2>
                <div className="bg-gray-800 p-6 rounded-lg shadow-lg border border-gray-700">
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="bg-gray-700 p-4 rounded">
                      <p className="text-gray-400 text-sm">Clinical Severity Score</p>
                      <p className="text-3xl font-bold text-blue-400">{patientData.prediction.clinical_severity_score}/100</p>
                    </div>
                    <div className="bg-gray-700 p-4 rounded">
                      <p className="text-gray-400 text-sm">Raw Probability</p>
                      <p className="text-3xl font-bold text-green-400">{(patientData.prediction.raw_probability * 100).toFixed(1)}%</p>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <p><span className="text-gray-400">Urgency Level:</span> <span className="text-white">{patientData.prediction.urgency_level}</span></p>
                    <p><span className="text-gray-400">Risk Category:</span> <span className="text-white">{patientData.prediction.risk_category}</span></p>
                    <p><span className="text-gray-400">Prediction:</span> <span className="text-white">{patientData.prediction.prediction_label}</span></p>
                  </div>

                  {patientData.prediction.shap_values && (
                    <div className="mt-4 pt-4 border-t border-gray-700">
                      <h3 className="text-lg font-semibold text-gray-100 mb-2">Top Contributing Factors</h3>
                      <ul className="space-y-1 text-sm text-gray-300">
                        {patientData.prediction.shap_values.slice(0, 5).map((factor, idx) => (
                          <li key={idx}>
                            <span className="text-blue-400">{factor.feature}:</span> {factor.shap_value > 0 ? '+' : ''}{factor.shap_value.toFixed(3)}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'assessment' && !patientData?.prediction && (
              <div className="bg-gray-800 p-12 rounded-lg shadow-lg border border-gray-700 text-center">
                <p className="text-gray-400">Enter patient data to see hospital readmission risk assessment results.</p>
              </div>
            )}

            {activeTab === 'navigation' && (
              <div>
                <h2 className="text-xl font-semibold text-gray-100 mb-4">AI Care Navigation</h2>
                <div className="h-96 lg:h-[500px] bg-gray-800 rounded-lg border border-gray-700 p-4">
                  {patientData?.prediction ? (
                    <div className="h-full flex flex-col">
                      {/* Chat Messages Area */}
                      <div className="flex-1 overflow-y-auto space-y-3 mb-4">
                        {chatMessages.length === 0 ? (
                          <p className="text-gray-400 text-sm text-center py-8">
                            Ask questions about your care plan, medications, or lifestyle recommendations.
                          </p>
                        ) : (
                          chatMessages.map((msg, idx) => (
                            <div
                              key={idx}
                              className={`p-3 rounded-lg max-w-[80%] ${
                                msg.role === 'user'
                                  ? 'bg-blue-600 ml-auto'
                                  : 'bg-gray-700'
                              }`}
                            >
                              <p className="text-sm text-white">{msg.content}</p>
                            </div>
                          ))
                        )}
                      </div>
                      
                      {/* Chat Input */}
                      <div className="flex gap-2">
                        <input
                          type="text"
                          placeholder="Type your question..."
                          className="flex-1 bg-gray-700 text-white px-4 py-2 rounded border border-gray-600 focus:outline-none focus:border-blue-500"
                          onKeyPress={(e) => {
                            if (e.key === 'Enter' && e.target.value.trim()) {
                              handleSendMessage({}, e.target.value.trim());
                              e.target.value = '';
                            }
                          }}
                        />
                        <button
                          onClick={(e) => {
                            const input = e.target.previousSibling;
                            if (input.value.trim()) {
                              handleSendMessage({}, input.value.trim());
                              input.value = '';
                            }
                          }}
                          disabled={chatLoading}
                          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
                        >
                          Send
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="h-full flex items-center justify-center text-gray-400">
                      <p>Complete risk assessment first to access care navigation.</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Reset Button */}
        {patientData?.prediction && (
          <div className="mt-6 text-center">
            <button
              onClick={handleReset}
              className="bg-gray-700 text-gray-300 px-6 py-2 rounded hover:bg-gray-600 transition"
            >
              Start New Assessment
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
