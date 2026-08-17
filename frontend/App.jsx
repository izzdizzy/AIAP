import { useEffect, useState } from 'react';
import AppShell from './components/AppShell';
import AssessmentPage from './pages/AssessmentPage';
import LandingPage from './pages/LandingPage';
import ResultsPage from './pages/ResultsPage';
import ChatPage from './pages/ChatbotPage';
import ReadmissionApp from './pages/readmission/App.jsx';
import DiabetesPage from './pages/diabetes/DiabetesPage.jsx';
import { submitAssessment } from './services/predictionService';
import {
  loadStoredAssessmentState,
  saveStoredAssessmentState
} from './utils/storage';

function getRouteFromHash() {
  const hash = window.location.hash.replace('#', '');
  return ['assessment', 'results', 'chat', 'readmission', 'diabetes'].includes(hash)
    ? hash
    : 'landing';
}

export default function App() {
  const [route, setRoute] = useState(() => (typeof window === 'undefined' ? 'landing' : getRouteFromHash()));
  const [assessmentState, setAssessmentState] = useState(() =>
    loadStoredAssessmentState()
  );

  const chatMessages = assessmentState?.chatMessages ?? [];
  const [loading, setLoading] = useState(false);

  // Verify if user has done an assessment, blocks access to Results & Chatbot otherwise.
  const hasAssessment = Boolean(assessmentState?.assessment);
  const hasPrediction = Boolean(assessmentState?.prediction);

  useEffect(() => {
    const handleHashChange = () => setRoute(getRouteFromHash());
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  useEffect(() => {
    saveStoredAssessmentState(assessmentState);
  }, [assessmentState]);

  function navigate(nextRoute) {
    window.location.hash = nextRoute === 'landing' ? '' : nextRoute;
    setRoute(nextRoute);
  }

  // Submit assessment
  async function handleSubmitAssessment(values) {
    setLoading(true);
    try {
      const formValues = structuredClone(values);
      const response = await submitAssessment(values);

      setAssessmentState({
        ...response,
        assessmentForm: formValues,
        sessionId: null,
        chatMessages: []
      });

      navigate('results');
    } catch (error) {
      alert(error.message);
    } finally {
      setLoading(false);
    }
  }

  // Clear assessment if restarted
  function handleRestart() {
    setAssessmentState(null);
    navigate('landing');
  }

  function handleEditAssessment() {
    navigate('assessment');
  }

  // Navigate to CAD Assessment from Landing Page
  function handleStartCADAssessment() {
    navigate('assessment');
  }

  // Navigate to Readmission Assessment from Landing Page
  function handleStartReadmissionAssessment() {
    navigate('readmission');
  }

  // Navigate to Diabetes Risk Classifier from Landing Page
  function handleStartDiabetesAssessment() {
    navigate('diabetes');
  }

  // Navigate back to Landing Page
  function handleBackToLanding() {
    navigate('landing');
  }

  function setChatMessages(messagesOrUpdater) {
    setAssessmentState(previous => {
      if (!previous) {
        return previous;
      }

      const currentMessages = previous.chatMessages ?? [];

      const nextMessages =
        typeof messagesOrUpdater === 'function'
          ? messagesOrUpdater(currentMessages)
          : messagesOrUpdater;

      return {
        ...previous,
        chatMessages: nextMessages
      };
    });
  }

  // Render standalone pages (no AppShell wrapper)
  if (route === 'landing') {
    return (
      <LandingPage
        onStartCADAssessment={handleStartCADAssessment}
        onStartReadmissionAssessment={handleStartReadmissionAssessment}
        onStartDiabetesAssessment={handleStartDiabetesAssessment}
      />
    );
  }

  if (route === 'readmission') {
    return (
      <ReadmissionApp onBackToLanding={handleBackToLanding} />
    );
  }

  if (route === 'diabetes') {
    return (
      <DiabetesPage onBackToLanding={handleBackToLanding} />
    );
  }

  // CAD routes wrapped in AppShell
  return (
    <AppShell
      currentRoute={route}
      onNavigate={navigate}
      hasPrediction={hasPrediction}
      onBackToLanding={handleBackToLanding}
    >
      {route === 'assessment' && (
        <AssessmentPage
          onSubmitAssessment={handleSubmitAssessment}
          loading={loading}
          onCancel={handleBackToLanding}
          initialValues={assessmentState?.assessmentForm}
        />
      )}

      {route === 'results' && hasPrediction && (
        <ResultsPage
          assessmentState={assessmentState}
          onRestart={handleRestart}
          onEditAssessment={handleEditAssessment}
          onOpenChat={() => navigate('chat')}
        />
      )}

      {route === 'chat' && hasAssessment && hasPrediction && (
        <ChatPage
          assessmentState={assessmentState}
          setAssessmentState={setAssessmentState}
          chatMessages={chatMessages}
          setChatMessages={setChatMessages}
          onBack={() => navigate('results')}
        />
      )}

      {route === 'results' && !hasPrediction && (
        <LandingPage
          onStartCADAssessment={handleStartCADAssessment}
          onStartReadmissionAssessment={handleStartReadmissionAssessment}
        />
      )}

      {route === 'chat' && (!hasAssessment || !hasPrediction) && (
        <LandingPage
          onStartCADAssessment={handleStartCADAssessment}
          onStartReadmissionAssessment={handleStartReadmissionAssessment}
        />
      )}
    </AppShell>
  );
}
