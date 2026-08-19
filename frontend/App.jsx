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
  loadStoredCADState,
  saveStoredCADState,
  loadStoredDiabetesState,
  saveStoredDiabetesState,
  loadStoredReadmissionState,
  saveStoredReadmissionState,
  loadStoredSubsidyTier,
  saveStoredSubsidyTier
} from './services/storage';

// Readmission
import PatientForm from './features/readmission/components/PatientForm';
import ReadmissionResults from './features/readmission/components/ReadmissionResults';
import { predictReadmission } from './features/readmission/services/api';

// Diabetes
import DiabetesPage from './features/diabetes/pages/DiabetesPage';
import DiabetesResults from './features/diabetes/components/DiabetesResults';
import { predictRisk as predictDiabetesRisk } from './features/diabetes/services/api';
import { saveAssessment as saveDiabetesAssessment, saveModuleAssessment } from './features/diabetes/services/historyApi';

// Auth
import { useAuth } from './context/AuthContext';
import LoginPage from './features/auth/pages/LoginPage';
import RegisterPage from './features/auth/pages/RegisterPage';

// AI Insights Workspace
import AIWorkspacePage from './pages/AIWorkspacePage';

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  // CAD State
  const [assessmentState, setAssessmentState] = useState(() => loadStoredCADState());
  const [cadLoading, setCadLoading] = useState(false);

  // Readmission State
  const [readmissionState, setReadmissionState] = useState(() => loadStoredReadmissionState());
  const [readmissionLoading, setReadmissionLoading] = useState(false);

  // Diabetes State
  const [diabetesState, setDiabetesState] = useState(() => loadStoredDiabetesState());
  const [diabetesLoading, setDiabetesLoading] = useState(false);

  // Subsidy Tier State
  const [subsidyTier, setSubsidyTier] = useState(() => loadStoredSubsidyTier());

  const readmissionForm = readmissionState?.form ?? null;
  const readmissionPrediction = readmissionState?.prediction ?? null;

  const diabetesForm = diabetesState?.form ?? null;
  const diabetesPrediction = diabetesState?.prediction ?? null;

  useEffect(() => {
    saveStoredCADState(assessmentState);
  }, [assessmentState]);

  useEffect(() => {
    saveStoredReadmissionState(readmissionState);
  }, [readmissionState]);

  useEffect(() => {
    saveStoredDiabetesState(diabetesState);
  }, [diabetesState]);

  useEffect(() => {
    saveStoredSubsidyTier(subsidyTier);
  }, [subsidyTier]);

  // CAD Handlers
  async function handleSubmitCAD(values) {
    setCadLoading(true);
    try {
      const formValues = structuredClone(values);
      const response = await submitAssessment(values);
      const newState = {
        ...response,
        assessmentForm: formValues,
        sessionId: null
      };
      setAssessmentState(newState);
      saveStoredCADState(newState);
      if (user) {
        saveModuleAssessment('cad', formValues, response?.prediction ?? response ?? {})
          .catch((e) => console.warn('[history] CAD save failed:', e.message));
      }
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
      const formValues = structuredClone(values);
      const result = await predictReadmission(values);
      const newState = {
        form: formValues,
        prediction: result
      };
      setReadmissionState(newState);
      saveStoredReadmissionState(newState);
      if (user) {
        saveModuleAssessment('readmission', formValues, result ?? {})
          .catch((e) => console.warn('[history] Readmission save failed:', e.message));
      }
      if (formValues.chas_tier) {
        setSubsidyTier(formValues.chas_tier);
        saveStoredSubsidyTier(formValues.chas_tier);
      }
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
      const formValues = structuredClone(values);
      const result = await predictDiabetesRisk(values);
      const newState = {
        form: formValues,
        prediction: result
      };
      setDiabetesState(newState);
      saveStoredDiabetesState(newState);
      if (user) {
        saveDiabetesAssessment(formValues)
          .catch((e) => console.warn('[history] Diabetes save failed:', e.message));
      }
      navigate('/diabetes/results');
    } catch (error) {
      alert(error.message || 'Failed to calculate diabetes risk.');
    } finally {
      setDiabetesLoading(false);
    }
  }

  const cadCompleted = Boolean(assessmentState?.prediction);
  const readmissionCompleted = Boolean(readmissionPrediction);
  const diabetesCompleted = Boolean(diabetesPrediction);

  if (location.pathname === '/login') {
    return <LoginPage />;
  }
  if (location.pathname === '/register') {
    return <RegisterPage />;
  }

  return (
    <AppShell
      cadCompleted={cadCompleted}
      readmissionCompleted={readmissionCompleted}
      diabetesCompleted={diabetesCompleted}
      user={user}
      onLogout={() => {
        logout();
        navigate('/');
      }}
    >
      <Routes>
        {/* Dashboard (Home) */}
        <Route
          path="/"
          element={
            <LandingPage
              onStartCADAssessment={() => navigate('/cad/assessment')}
              onStartReadmissionAssessment={() => navigate('/readmission/assessment')}
              onStartDiabetesAssessment={() => navigate('/diabetes/assessment')}
            />
          }
        />
        <Route path="/home" element={<Navigate to="/" replace />} />

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
              onOpenChat={() => navigate('/ai-insights')}
            />
          }
        />
        <Route
          path="/cad/chat"
          element={<Navigate to="/ai-insights" replace />}
        />

        {/* Readmission Routes */}
        <Route
          path="/readmission/assessment"
          element={
            <PatientForm
              onSubmit={handleSubmitReadmission}
              loading={readmissionLoading}
              initialValues={readmissionForm}
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
              initialValues={diabetesForm}
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
              onOpenChat={() => navigate('/ai-insights')}
            />
          }
        />
        <Route path="/diabetes/dashboard" element={<Navigate to="/" replace />} />

        {/* AI Workspace Route */}
        <Route
          path="/ai-insights"
          element={
            <AIWorkspacePage
              assessmentState={assessmentState}
              diabetesPrediction={diabetesPrediction}
              diabetesForm={diabetesForm}
              readmissionPrediction={readmissionPrediction}
              readmissionForm={readmissionForm}
              subsidyTier={subsidyTier}
              onUpdateSubsidyTier={(tier) => {
                setSubsidyTier(tier);
                saveStoredSubsidyTier(tier);
              }}
              onNavigateToCAD={() => navigate('/cad/assessment')}
              onNavigateToDiabetes={() => navigate('/diabetes/assessment')}
              onNavigateToReadmission={() => navigate('/readmission/assessment')}
            />
          }
        />

        {/* Fallback redirect */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}
