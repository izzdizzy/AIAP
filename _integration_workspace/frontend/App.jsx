import { useEffect, useState } from 'react';
import AppShell from './components/AppShell';
import AssessmentPage from './pages/AssessmentPage';
import HomePage from './pages/HomePage';
import ResultsPage from './pages/ResultsPage';
import ChatPage from './pages/ChatbotPage';
import ReadmissionAssessmentPage from './pages/readmission/ReadmissionAssessmentPage';
import { submitAssessment } from './services/predictionService';
import {
  loadStoredAssessmentState,
  saveStoredAssessmentState
} from './utils/storage';

function getRouteFromHash() {
  const hash = window.location.hash.replace('#', '');
  return ['assessment', 'results', 'chat', 'readmission'].includes(hash)
    ? hash
    : 'home';
}

export default function App() {
  const [route, setRoute] = useState(() => (typeof window === 'undefined' ? 'home' : getRouteFromHash()));
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
    window.location.hash = nextRoute === 'home' ? '' : nextRoute;
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

  // Clear assessmnet if restarted
  function handleRestart() {
    setAssessmentState(null);
    navigate('home');
  }

  function handleEditAssessment() {
    navigate('assessment');
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

  // Navigation pages & loading
  return (
    <AppShell
      currentRoute={route}
      onNavigate={navigate}
      hasPrediction={hasPrediction}
    >
      {route === 'home' && (
        <HomePage
          onStartAssessment={() => navigate('assessment')}
        />
      )}

      {route === 'assessment' && (
        <AssessmentPage
          onSubmitAssessment={handleSubmitAssessment}
          loading={loading}
          onCancel={() => navigate('home')}
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
        <HomePage
          onStartAssessment={() => navigate('assessment')}
        />
      )}

      {route === 'chat' && (!hasAssessment || !hasPrediction) && (
        <HomePage
          onStartAssessment={() => navigate('assessment')}
        />
      )}

      {route === 'readmission' && (
        <ReadmissionAssessmentPage />
      )}
    </AppShell>
  );
}
