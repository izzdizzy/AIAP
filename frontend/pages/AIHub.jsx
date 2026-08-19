import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import WidgetRenderer from '../components/widgets/WidgetRenderer';
import { sendGenAIQuery } from '../services/genaiApi';
import { loadStoredAIMessages, saveStoredAIMessages } from '../services/storage';

export default function AIHub({
  assessmentState,
  diabetesPrediction,
  readmissionPrediction,
  readmissionForm,
  subsidyTier,
  onNavigateToCAD,
  onNavigateToDiabetes,
  onNavigateToReadmission
}) {
  const [activeTab, setActiveTab] = useState('cad_coach'); // 'cad_coach', 'diabetes_explainer', 'care_navigator'

  // Subsidy tier is auto-populated from readmission form's CHAS tier; not user-editable
  const activeSubsidy = readmissionForm?.chas_tier || 'Not provided';

  const defaultMessages = {
    cad_coach: [
      {
        role: 'assistant',
        content: "Hello! I'm your **CAD Specialist & Lifestyle Coach**. I can help you understand how your cholesterol, blood pressure, and activity levels affect your cardiovascular health, and recommend heart-healthy dietary changes.",
        widget: {
          type: 'COPYABLE_DOCTOR_QUESTIONS',
          data: {
            title: 'Cardiovascular Health Questions for Your Doctor',
            questions: [
              'What dietary changes will help lower my cholesterol?',
              'How frequently should I monitor my blood pressure at home?',
              'What exercise intensity is safe for my heart?'
            ]
          }
        }
      }
    ],
    diabetes_explainer: [
      {
        role: 'assistant',
        content: "Welcome! I'm your **Diabetes Specialist & Results Explainer**. I translate machine learning feature contributions into plain-language insights so you can target your risk factors effectively.",
        widget: diabetesPrediction?.top_factors ? {
          type: 'SHAP_FACTOR_CARD',
          data: {
            overall_risk: diabetesPrediction.risk_label || 'Assessed Risk',
            probability: String(diabetesPrediction.risk_probability || ''),
            factors: diabetesPrediction.top_factors
          }
        } : null
      }
    ],
    care_navigator: [
      {
        role: 'assistant',
        content: "Greetings! I'm your **Care Navigator & Triage Assistant**. I evaluate your symptoms and subsidy tier to guide you to the right healthcare facility in Singapore.",
        widget: {
          type: 'GOOGLE_MAPS_ACTION',
          data: {
            facility_type: 'Polyclinic',
            subsidy_tier: activeSubsidy,
            label: `Locate Nearest Subsidized Polyclinics (${activeSubsidy})`
          }
        }
      }
    ]
  };

  const [messages, setMessages] = useState(() => {
    const saved = loadStoredAIMessages();
    return saved || defaultMessages;
  });

  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    saveStoredAIMessages(messages);
  }, [messages]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeTab, loading]);

  const activeMessages = messages[activeTab] || [];

  const tabConfig = {
    cad_coach: {
      id: 'cad_coach',
      label: '🫀 Lifestyle Coach',
      title: 'Lifestyle Coach',
      color: '#3b82f6',
      quickChips: [
        'Suggest a low-sodium meal plan',
        'What exercises are safe for me?'
      ]
    },
    diabetes_explainer: {
      id: 'diabetes_explainer',
      label: '🥗 Results Explainer',
      title: 'Results Explainer',
      color: '#10b981',
      quickChips: [
        'Explain my heart Results factors',
        'Why is my score 75.8%?'
      ]
    },
    care_navigator: {
      id: 'care_navigator',
      label: '🏥 Care Navigator',
      title: 'Care Navigator & Triage Assistant',
      color: '#f59e0b',
      quickChips: [
        'Where should I go for care?',
        'Questions for my doctor'
      ]
    }
  };

  const currentTab = tabConfig[activeTab];

  // Calculate loaded data status badges
  const isCadLoaded = Boolean(assessmentState?.prediction);
  const isDiabetesLoaded = Boolean(diabetesPrediction);
  const isReadmissionLoaded = Boolean(readmissionPrediction);

  function handleSubsidyChange(e) {
    const newTier = e.target.value;
    if (onUpdateSubsidyTier) {
      onUpdateSubsidyTier(newTier);
    }
  }

  function handleClearTabHistory() {
    if (window.confirm(`Clear chat history for ${currentTab.title}?`)) {
      setMessages(prev => ({
        ...prev,
        [activeTab]: defaultMessages[activeTab] || []
      }));
    }
  }

  function handleUpdateWidgetData(msgIdx, newWidgetData) {
    setMessages(prev => {
      const currentList = [...(prev[activeTab] || [])];
      if (currentList[msgIdx]) {
        currentList[msgIdx] = {
          ...currentList[msgIdx],
          widget: {
            ...currentList[msgIdx].widget,
            data: newWidgetData
          }
        };
      }
      return {
        ...prev,
        [activeTab]: currentList
      };
    });
  }

  // Construct patient context
  function getUnifiedPayload() {
    return {
      demographics: {
        age: assessmentState?.assessmentForm?.age || readmissionForm?.age,
        gender: assessmentState?.assessmentForm?.gender || readmissionForm?.gender,
        subsidy_tier: activeSubsidy
      },
      form_metrics: {
        blood_pressure: assessmentState?.assessmentForm?.bp || (assessmentState?.assessmentForm?.trestbps ? `${assessmentState.assessmentForm.trestbps}` : null),
        cholesterol: assessmentState?.assessmentForm?.cholesterol || assessmentState?.assessmentForm?.chol,
        bmi: assessmentState?.assessmentForm?.bmi,
        glucose: assessmentState?.assessmentForm?.glucose,
        active_symptoms: readmissionForm?.symptoms || []
      },
      ml_scores: {
        cad_risk_level: assessmentState?.prediction?.risk_level,
        cad_probability: assessmentState?.prediction?.probability,
        diabetes_risk_level: diabetesPrediction?.risk_label || diabetesPrediction?.risk_band,
        diabetes_probability: diabetesPrediction?.risk_probability,
        readmission_risk_level: readmissionPrediction?.urgency_level,
        readmission_severity_score: readmissionPrediction?.clinical_severity_score
      },
      shap_factors: diabetesPrediction?.top_factors || []
    };
  }

  async function handleSend(promptText) {
    const query = promptText || inputQuery;
    if (!query.trim() || loading) return;

    const userMsg = { role: 'user', content: query };
    setMessages(prev => ({
      ...prev,
      [activeTab]: [...prev[activeTab], userMsg]
    }));

    if (!promptText) setInputQuery('');
    setLoading(true);

    try {
      const rawInput = getUnifiedPayload();
      const res = await sendGenAIQuery({
        userQuery: query,
        assistantType: activeTab,
        rawInput,
        history: activeMessages
      });

      const assistantMsg = {
        role: 'assistant',
        content: res.message || 'Thank you for your inquiry.',
        widget: res.widget || null
      };

      setMessages(prev => ({
        ...prev,
        [activeTab]: [...prev[activeTab], assistantMsg]
      }));
    } catch (err) {
      console.error("AI Query Error:", err);
      const errorMsg = {
        role: 'assistant',
        content: `I encountered an issue processing your request: ${err.message || 'Server connection error'}.`,
        widget: null
      };
      setMessages(prev => ({
        ...prev,
        [activeTab]: [...prev[activeTab], errorMsg]
      }));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '16px', fontFamily: 'inherit' }}>
      {/* 1. Top Tab Bar */}
      <div style={{
        display: 'flex',
        gap: '10px',
        marginBottom: '16px',
        borderBottom: '2px solid var(--border, #334155)',
        paddingBottom: '10px'
      }}>
        {Object.keys(tabConfig).map(key => {
          const tab = tabConfig[key];
          const isActive = activeTab === key;

          return (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              style={{
                flex: 1,
                padding: '12px 16px',
                borderRadius: '10px',
                border: isActive ? `2px solid ${tab.color}` : '1px solid var(--border, #334155)',
                background: isActive ? `${tab.color}22` : 'var(--surface-muted, #1e293b)',
                color: isActive ? '#ffffff' : 'var(--text-muted, #94a3b8)',
                fontWeight: isActive ? '700' : '600',
                fontSize: '0.95rem',
                cursor: 'pointer',
                textAlign: 'center',
                transition: 'all 0.2s ease',
                boxShadow: isActive ? `0 4px 12px ${tab.color}33` : 'none'
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Floating Context Badge Status Bar */}
      <div style={{
        padding: '10px 16px',
        borderRadius: '10px',
        background: 'var(--surface-muted, #0f172a)',
        border: '1px solid var(--border, #334155)',
        marginBottom: '16px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '8px',
        fontSize: '0.85rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <span style={{ fontWeight: '700', color: 'var(--text-muted, #94a3b8)' }}>Clinical Data Status:</span>
          
          <span style={{
            padding: '2px 8px',
            borderRadius: '12px',
            background: isCadLoaded ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.12)',
            color: isCadLoaded ? '#34d399' : '#f87171',
            border: `1px solid ${isCadLoaded ? '#10b981' : '#ef4444'}`,
            fontSize: '0.78rem',
            fontWeight: '600'
          }}>
            {isCadLoaded ? '✓ CAD Data Loaded' : '✗ CAD Pending'}
          </span>

          <span style={{
            padding: '2px 8px',
            borderRadius: '12px',
            background: isDiabetesLoaded ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.12)',
            color: isDiabetesLoaded ? '#34d399' : '#f87171',
            border: `1px solid ${isDiabetesLoaded ? '#10b981' : '#ef4444'}`,
            fontSize: '0.78rem',
            fontWeight: '600'
          }}>
            {isDiabetesLoaded ? '✓ Diabetes Data Loaded' : '✗ Diabetes Pending'}
          </span>

          <span style={{
            padding: '2px 8px',
            borderRadius: '12px',
            background: isReadmissionLoaded ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.12)',
            color: isReadmissionLoaded ? '#34d399' : '#f87171',
            border: `1px solid ${isReadmissionLoaded ? '#10b981' : '#ef4444'}`,
            fontSize: '0.78rem',
            fontWeight: '600'
          }}>
            {isReadmissionLoaded ? '✓ Readmission Data Loaded' : '✗ Readmission Pending'}
          </span>
        </div>

        <div style={{ fontSize: '0.78rem', opacity: 0.8, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span>Subsidy Tier:</span>
          <span
            style={{
              padding: '4px 10px',
              borderRadius: '6px',
              background: 'var(--surface-muted, #334155)',
              color: 'var(--text-muted, #94a3b8)',
              border: '1px solid var(--border, #475569)',
              fontSize: '0.8rem',
              fontWeight: '600',
              cursor: 'help'
            }}
            title="CHAS tier is set from your Readmission assessment"
          >
            {activeSubsidy || 'Not provided'}
          </span>

          <button
            onClick={handleClearTabHistory}
            title="Reset conversation history for this tab"
            style={{
              padding: '4px 8px',
              borderRadius: '6px',
              background: 'rgba(239, 68, 68, 0.12)',
              color: '#f87171',
              border: '1px solid #ef4444',
              fontSize: '0.75rem',
              fontWeight: '600',
              cursor: 'pointer',
              marginLeft: '6px'
            }}
          >
            🗑️ Clear Chat
          </button>
        </div>
      </div>

      {/* Main Chat Container */}
      <div style={{
        borderRadius: '12px',
        border: '1px solid var(--border, #334155)',
        background: 'var(--surface, #0f172a)',
        display: 'flex',
        flexDirection: 'column',
        height: '520px',
        overflow: 'hidden'
      }}>
        {/* Chat Stream Messages */}
        <div style={{
          flex: 1,
          padding: '20px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px'
        }}>
          {activeMessages.map((msg, idx) => {
            const isAssistant = msg.role === 'assistant';

            return (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: isAssistant ? 'flex-start' : 'flex-end'
                }}
              >
                <div style={{
                  fontSize: '0.75rem',
                  fontWeight: '600',
                  color: 'var(--text-muted, #94a3b8)',
                  marginBottom: '4px'
                }}>
                  {isAssistant ? currentTab.title : 'You'}
                </div>

                <div style={{
                  maxWidth: '82%',
                  padding: '12px 16px',
                  borderRadius: isAssistant ? '4px 16px 16px 16px' : '16px 16px 4px 16px',
                  background: isAssistant ? 'var(--surface-muted, #1e293b)' : currentTab.color,
                  color: isAssistant ? 'var(--text, #f8fafc)' : '#ffffff',
                  fontSize: '0.9rem',
                  lineHeight: 1.5
                }}>
                  <ReactMarkdown
                    components={{
                      ul: ({ node, ...props }) => <ul style={{ margin: '8px 0', paddingLeft: '20px', listStyleType: 'disc' }} {...props} />,
                      ol: ({ node, ...props }) => <ol style={{ margin: '8px 0', paddingLeft: '20px', listStyleType: 'decimal' }} {...props} />,
                      li: ({ node, ...props }) => <li style={{ marginBottom: '4px' }} {...props} />,
                      p: ({ node, ...props }) => <p style={{ margin: '6px 0', lineHeight: '1.5' }} {...props} />
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                  
                  {/* Rich-Media Component Renderer */}
                  {isAssistant && msg.widget && (
                    <WidgetRenderer
                      widget={msg.widget}
                      onUpdateWidgetData={(newWidgetData) => handleUpdateWidgetData(idx, newWidgetData)}
                    />
                  )}
                </div>
              </div>
            );
          })}

          {loading && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#94a3b8', fontSize: '0.85rem' }}>
              <span style={{ animation: 'spin 1s infinite linear' }}>⏳</span>
              <span>{currentTab.title} is preparing your response...</span>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* 2. Domain-Specific Quick-Action Chips */}
        <div style={{
          padding: '8px 16px',
          borderTop: '1px solid var(--border, #334155)',
          background: 'rgba(255, 255, 255, 0.02)',
          display: 'flex',
          gap: '8px',
          overflowX: 'auto'
        }}>
          {currentTab.quickChips.map((chip, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(chip)}
              disabled={loading}
              style={{
                padding: '6px 14px',
                borderRadius: '16px',
                fontSize: '0.8rem',
                fontWeight: '600',
                border: `1px solid ${currentTab.color}`,
                background: 'var(--surface-muted, #1e293b)',
                color: 'var(--text, #f8fafc)',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                transition: 'all 0.15s ease'
              }}
              onMouseOver={(e) => e.currentTarget.style.background = `${currentTab.color}33`}
              onMouseOut={(e) => e.currentTarget.style.background = 'var(--surface-muted, #1e293b)'}
            >
              💡 {chip}
            </button>
          ))}
        </div>

        {/* Text Input Bar */}
        <div style={{
          padding: '12px 16px',
          borderTop: '1px solid var(--border, #334155)',
          display: 'flex',
          gap: '10px',
          alignItems: 'center'
        }}>
          <input
            type="text"
            placeholder={`Ask ${currentTab.title}...`}
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            disabled={loading}
            style={{
              flex: 1,
              padding: '10px 14px',
              borderRadius: '8px',
              border: '1px solid var(--border, #334155)',
              background: 'var(--surface-muted, #1e293b)',
              color: 'var(--text, #f8fafc)',
              fontSize: '0.9rem',
              outline: 'none'
            }}
          />
          <button
            onClick={() => handleSend()}
            disabled={loading || !inputQuery.trim()}
            style={{
              padding: '10px 18px',
              borderRadius: '8px',
              background: currentTab.color,
              color: 'white',
              fontWeight: '700',
              border: 'none',
              cursor: loading || !inputQuery.trim() ? 'not-allowed' : 'pointer',
              opacity: loading || !inputQuery.trim() ? 0.6 : 1,
              transition: 'opacity 0.2s ease'
            }}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
