import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import AppShell from './components/AppShell';
import LandingPage from './pages/LandingPage';

// CAD
import AssessmentPage from './features/cad/pages/AssessmentPage';
import ResultsPage from './features/cad/pages/ResultsPage';
import ChatPage from './features/cad/pages/ChatbotPage';
import { submitAssessment } from './features/cad/services/predictionService';
import {
  loadStoredAssessmentState,
  saveStoredAssessmentState
} from './features/cad/utils/storage';

// Readmission
import PatientForm from './features/readmission/components/PatientForm';
import ReadmissionResults from './features/readmission/components/ReadmissionResults';
import { predictReadmission } from './features/readmission/services/api';

// Diabetes
import DiabetesPage from './features/diabetes/pages/DiabetesPage';
import DiabetesResults from './features/diabetes/components/DiabetesResults';
import { predictRisk as predictDiabetesRisk } from './features/diabetes/services/api';

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();

  // CAD State
  const [assessmentState, setAssessmentState] = useState(() => loadStoredAssessmentState());
  const [cadLoading, setCadLoading] = useState(false);

  // Readmission State
  const [readmissionPrediction, setReadmissionPrediction] = useState(null);
  const [readmissionLoading, setReadmissionLoading] = useState(false);

  // Diabetes State
  const [diabetesPrediction, setDiabetesPrediction] = useState(null);
  const [diabetesLoading, setDiabetesLoading] = useState(false);

  useEffect(() => {
    saveStoredAssessmentState(assessmentState);
  }, [assessmentState]);

  // CAD Handlers
  async function handleSubmitCAD(values) {
    setCadLoading(true);
    try {
      const formValues = structuredClone(values);
      const response = await submitAssessment(values);
      setAssessmentState({
        ...response,
        assessmentForm: formValues,
        sessionId: null,
        chatMessages: []
      });
      navigate('/cad/results');
    } catch (error) {
      alert(error.message || 'Failed to calculate CAD risk.');
    } finally {
      setCadLoading(false);
    }
  }

  // Readmission Handlers
  async function handleSubmitReadmission(values) {
    setReadmissionLoading(true);
    try {
      const result = await predictReadmission(values);
      setReadmissionPrediction(result);
      navigate('/readmission/results');
    } catch (error) {
      alert(error.message || 'Failed to calculate readmission risk.');
    } finally {
      setReadmissionLoading(false);
    }
  }

  // Diabetes Handlers
  async function handleSubmitDiabetes(values) {
    setDiabetesLoading(true);
    try {
      const result = await predictDiabetesRisk(values);
      setDiabetesPrediction(result);
      navigate('/diabetes/results');
    } catch (error) {
      alert(error.message || 'Failed to calculate diabetes risk.');
    } finally {
      setDiabetesLoading(false);
    }
  }

  const isLanding = location.pathname === '/' || location.pathname === '/home';

  if (isLanding) {
    return (
      <LandingPage
        onStartCADAssessment={() => navigate('/cad/assessment')}
        onStartReadmissionAssessment={() => navigate('/readmission/assessment')}
        onStartDiabetesAssessment={() => navigate('/diabetes/assessment')}
      />
    );
  }

  return (
    <AppShell>
      <Routes>
        {/* CAD Routes */}
        <Route
          path="/cad/assessment"
          element={
            <AssessmentPage
              onSubmitAssessment={handleSubmitCAD}
              loading={cadLoading}
              onCancel={() => navigate('/')}
              initialValues={assessmentState?.assessmentForm}
            />
          }
        />
        <Route
          path="/cad/results"
          element={
            <ResultsPage
              assessmentState={assessmentState}
              onRestart={() => {
                setAssessmentState(null);
                navigate('/');
              }}
              onEditAssessment={() => navigate('/cad/assessment')}
              onOpenChat={() => navigate('/cad/chat')}
            />
          }
        />
        <Route
          path="/cad/chat"
          element={
            <ChatPage
              assessmentState={assessmentState}
              setAssessmentState={setAssessmentState}
              chatMessages={assessmentState?.chatMessages ?? []}
              setChatMessages={(updater) => {
                setAssessmentState(prev => {
                  if (!prev) return prev;
                  const current = prev.chatMessages ?? [];
                  const next = typeof updater === 'function' ? updater(current) : updater;
                  return { ...prev, chatMessages: next };
                });
              }}
              onBack={() => navigate('/cad/results')}
            />
          }
        />

        {/* Readmission Routes */}
        <Route
          path="/readmission/assessment"
          element={
            <PatientForm
              onSubmit={handleSubmitReadmission}
              loading={readmissionLoading}
            />
          }
        />
        <Route
          path="/readmission/results"
          element={
            <ReadmissionResults
              prediction={readmissionPrediction}
              onResetPrediction={() => navigate('/readmission/assessment')}
              onBackToLanding={() => navigate('/')}
            />
          }
        />

        {/* Diabetes Routes */}
        <Route
          path="/diabetes/assessment"
          element={
            <DiabetesPage
              onSubmitAssessment={handleSubmitDiabetes}
              loading={diabetesLoading}
            />
          }
        />
        <Route
          path="/diabetes/results"
          element={
            <DiabetesResults
              prediction={diabetesPrediction}
              onResetPrediction={() => navigate('/diabetes/assessment')}
              onBackToLanding={() => navigate('/')}
              onOpenChat={() => navigate('/cad/chat')}
            />
          }
        />

        {/* Fallback redirect */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}
