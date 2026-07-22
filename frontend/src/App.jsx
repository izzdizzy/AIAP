import React, { useState } from 'react';
import PatientForm from './components/PatientForm';
import RiskDashboard from './components/RiskDashboard';
import ChatInterface from './components/ChatInterface';
import { predictPatient, uploadPatientFile, sendChatMessage } from './services/api';

function App() {
  const [activeTab, setActiveTab] = useState('assessment');
  const [loading, setLoading] = useState(false);
  const [patientData, setPatientData] = useState({ form: null, prediction: null });
  const [error, setError] = useState(null);

  const handleFormSubmit = async (formData, file) => {
    setLoading(true);
    setError(null);

    try {
      let predictionData;

      if (file) {
        const uploadResponse = await uploadPatientFile(file);
        predictionData = uploadResponse.prediction || uploadResponse;
      } else {
        predictionData = await predictPatient(formData);
      }

      setPatientData({ form: formData, prediction: predictionData });
      setActiveTab('navigation');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to process patient data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async (context, query) => {
    setLoading(true);
    try {
      const response = await sendChatMessage(context, query);
      return response;
    } catch (err) {
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-blue-700 text-white shadow-md">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">IT3100 PR2 - Healthcare Risk Assessment</h1>
          <p className="text-sm text-blue-200 mt-1">ML-Powered Clinical Decision Support</p>
        </div>
      </header>

      <div className="container mx-auto px-4 py-6">
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
          <p className="text-sm text-yellow-800">
            <strong>Medical Disclaimer:</strong> This tool is for educational and demonstration purposes only. 
            It does not provide medical advice, diagnosis, or treatment. Always consult qualified healthcare professionals.
          </p>
        </div>

        <div className="flex border-b border-gray-200 mb-6">
          <button
            onClick={() => setActiveTab('assessment')}
            className={`px-6 py-3 font-medium ${
              activeTab === 'assessment'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Risk Assessment
          </button>
          <button
            onClick={() => setActiveTab('navigation')}
            className={`px-6 py-3 font-medium ${
              activeTab === 'navigation'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Care Navigation
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            {activeTab === 'assessment' && (
              <div className="bg-white p-6 rounded-lg shadow">
                <h2 className="text-xl font-semibold text-gray-800 mb-4">Patient Input</h2>
                <PatientForm onSubmit={handleFormSubmit} loading={loading} />
              </div>
            )}

            {activeTab === 'navigation' && patientData.prediction && (
              <div className="bg-white p-6 rounded-lg shadow">
                <h2 className="text-xl font-semibold text-gray-800 mb-4">Patient Summary</h2>
                <div className="space-y-2 text-sm">
                  <p><span className="font-medium">Severity Score:</span> {patientData.prediction.severity_score}/100</p>
                  <p><span className="font-medium">Urgency:</span> {patientData.prediction.urgency_level}</p>
                  {patientData.form && (
                    <>
                      <p><span className="font-medium">Age:</span> {patientData.form.age || 'N/A'}</p>
                      <p><span className="font-medium">CHAS Tier:</span> {patientData.form.chas_tier}</p>
                      <p><span className="font-medium">Symptoms:</span> {patientData.form.symptoms?.join(', ') || 'None'}</p>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="lg:col-span-2">
            {activeTab === 'assessment' && patientData.prediction && (
              <div>
                <h2 className="text-xl font-semibold text-gray-800 mb-4">Risk Analysis Results</h2>
                <RiskDashboard prediction={patientData.prediction} />
              </div>
            )}

            {activeTab === 'assessment' && !patientData.prediction && (
              <div className="bg-white p-12 rounded-lg shadow text-center">
                <p className="text-gray-500">Enter patient data to see risk assessment results.</p>
              </div>
            )}

            {activeTab === 'navigation' && (
              <div>
                <h2 className="text-xl font-semibold text-gray-800 mb-4">AI Care Navigation</h2>
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
