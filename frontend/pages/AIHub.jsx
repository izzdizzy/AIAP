import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import WidgetRenderer from '../components/widgets/WidgetRenderer';
import { sendGenAIQuery } from '../services/genaiApi';
import { loadStoredAIMessages, saveStoredAIMessages } from '../services/storage';

export default function AIHub({
  assessmentState,
  diabetesPrediction,
  diabetesForm,
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

  // Extract model states
  const cadPred = assessmentState?.prediction?.backendPrediction || assessmentState?.prediction || {};
  const cadForm = assessmentState?.assessmentForm || assessmentState?.assessment || {};

  // Calculate loaded data status badges
  const isCadLoaded = Boolean(assessmentState?.prediction);
  const isDiabetesLoaded = Boolean(diabetesPrediction);
  const isReadmissionLoaded = Boolean(readmissionPrediction);

  // Feature Label & Value Translation Maps
  const CAD_LABELS = {
    chol: 'Serum Cholesterol',
    trestbps: 'Resting Blood Pressure',
    thalach: 'Max Heart Rate',
    oldpeak: 'ST Depression (Oldpeak)',
    cp: 'Chest Pain Type',
    ca: 'Major Vessels Count',
    exang: 'Exercise-Induced Angina',
    age: 'Age',
    sex: 'Biological Sex',
    fbs: 'Fasting Blood Sugar',
    restecg: 'Resting ECG',
    slope: 'ST Slope',
    thal: 'Thalassemia'
  };

  const CP_LABELS = { 1: 'Typical Angina (1)', 2: 'Atypical Angina (2)', 3: 'Non-anginal Pain (3)', 4: 'Asymptomatic (4)' };
  const RESTECG_LABELS = { 0: 'Normal (0)', 1: 'ST-T Abnormality (1)', 2: 'LV Hypertrophy (2)' };
  const SLOPE_LABELS = { 1: 'Upsloping (1)', 2: 'Flat (2)', 3: 'Downsloping (3)' };
  const THAL_LABELS = { 3: 'Normal (3)', 6: 'Fixed Defect (6)', 7: 'Reversible Defect (7)' };
  const GENHLTH_LABELS = { 1: 'Excellent (1)', 2: 'Very Good (2)', 3: 'Good (3)', 4: 'Fair (4)', 5: 'Poor (5)' };

  function getCadFactorValue(rawKey, item) {
    if (item.value != null && String(item.value).toLowerCase() !== 'observed') {
      return String(item.value);
    }
    const val = cadForm[rawKey];
    if (val == null) return null;
    if (rawKey === 'cp') return CP_LABELS[val] || `Type ${val}`;
    if (rawKey === 'chol') return `${val} mg/dL`;
    if (rawKey === 'trestbps') return `${val} mmHg`;
    if (rawKey === 'thalach') return `${val} bpm`;
    if (rawKey === 'fbs') return Number(val) === 1 ? 'Elevated (>120 mg/dL)' : 'Normal (<=120 mg/dL)';
    if (rawKey === 'exang') return Number(val) === 1 ? 'Yes' : 'No';
    if (rawKey === 'restecg') return RESTECG_LABELS[val] || String(val);
    if (rawKey === 'slope') return SLOPE_LABELS[val] || String(val);
    if (rawKey === 'thal') return THAL_LABELS[val] || String(val);
    if (rawKey === 'sex') return Number(val) === 1 ? 'Male' : 'Female';
    if (rawKey === 'ca') return `${val} vessels`;
    return String(val);
  }

  function getDiabetesFactorValue(rawKey, item) {
    if (item.value != null && String(item.value).toLowerCase() !== 'observed') {
      return String(item.value);
    }
    const val = diabetesForm?.[rawKey];
    if (val == null) return null;
    if (rawKey === 'GenHlth') return GENHLTH_LABELS[val] || String(val);
    if (rawKey === 'BMI') return `${val}`;
    if (rawKey === 'Age') return `Age Group ${val}`;
    if (['HighBP', 'HighChol', 'PhysActivity', 'DiffWalk', 'Smoker', 'HeartDiseaseorAttack', 'Fruits', 'Veggies'].includes(rawKey)) {
      return Number(val) === 1 || val === '1' ? 'Yes' : 'No';
    }
    return String(val);
  }

  function getReadmissionFactorValue(rawKey, item) {
    const rawVal = item.feature_value ?? item.value;
    if (rawVal != null && String(rawVal).toLowerCase() !== 'observed') {
      return String(rawVal);
    }
    const formVal = readmissionForm?.[rawKey];
    if (formVal == null) return null;
    if (Array.isArray(formVal)) return formVal.join(', ');
    return String(formVal);
  }

  function normalizeCadFactors(factors = []) {
    return factors.map((item, idx) => {
      const rawKey = item.feature || item.name || item.key || `Factor ${idx + 1}`;
      const name = CAD_LABELS[rawKey] ? `${CAD_LABELS[rawKey]} (CAD)` : (rawKey.includes('(CAD)') ? rawKey : `${rawKey} (CAD)`);
      let impact = item.impact ?? item.shap_value ?? item.importance ?? 0;
      if (typeof impact === 'number') {
        impact = impact >= 0 ? `+${impact.toFixed(3)}` : impact.toFixed(3);
      }
      const valStr = getCadFactorValue(rawKey, item);
      return {
        name,
        value: valStr,
        impact: String(impact),
        type: item.direction === 'negative' || (typeof item.impact === 'number' && item.impact < 0) ? 'protective_factor' : 'risk_driver'
      };
    });
  }

  function normalizeReadmissionFactors(factors = []) {
    return factors.map((item, idx) => {
      const label = item.feature_name || item.name || item.feature || `Factor ${idx + 1}`;
      const rawKey = item.feature || item.feature_name || label;
      const name = label.includes('(Readmission)') ? label : `${label} (Readmission)`;
      const rawImpact = item.shap_value ?? item.impact ?? item.importance ?? 0;
      const impactStr = typeof rawImpact === 'number'
        ? (rawImpact >= 0 ? `+${rawImpact.toFixed(3)}` : rawImpact.toFixed(3))
        : String(rawImpact);
      const valStr = getReadmissionFactorValue(rawKey, item);
      return {
        name,
        value: valStr,
        impact: impactStr,
        type: (typeof rawImpact === 'number' && rawImpact < 0) ? 'protective_factor' : 'risk_driver'
      };
    });
  }

  function normalizeDiabetesFactors(factors = []) {
    return factors.map((item, idx) => {
      if (typeof item === 'string') {
        const valStr = getDiabetesFactorValue(item, {});
        return { name: `${item} (Diabetes)`, value: valStr, impact: '+0.200', type: 'risk_driver' };
      }
      const rawKey = item.name || item.feature || `Factor ${idx + 1}`;
      const name = rawKey.includes('(Diabetes)') ? rawKey : `${rawKey} (Diabetes)`;
      const rawImpact = item.impact ?? item.shap_value ?? item.importance ?? 0;
      const impactStr = typeof rawImpact === 'number'
        ? (rawImpact >= 0 ? `+${rawImpact.toFixed(3)}` : rawImpact.toFixed(3))
        : String(rawImpact);
      const valStr = getDiabetesFactorValue(rawKey, item);
      return {
        name,
        value: valStr,
        impact: impactStr,
        type: item.type || ((typeof rawImpact === 'number' && rawImpact < 0) ? 'protective_factor' : 'risk_driver')
      };
    });
  }

  const cadFactorsList = cadPred.topFactors || cadPred.top_factors || [];
  const readmissionFactorsList = readmissionPrediction?.shap_values || readmissionPrediction?.top_positive_features || [];
  const diabetesFactorsList = diabetesPrediction?.top_factors || [];

  const combinedShapFactors = [
    ...normalizeDiabetesFactors(diabetesFactorsList),
    ...normalizeCadFactors(cadFactorsList),
    ...normalizeReadmissionFactors(readmissionFactorsList)
  ];

  // Synthesize multi-model overall risk label and probability badges
  function computeOverallRiskSummary() {
    const activeResults = [];
    const probs = [];

    if (isCadLoaded) {
      const lvl = cadPred.riskLevel || cadPred.risk_level || 'Assessed Risk';
      const pct = cadPred.riskPercent || (cadPred.riskProbability ? `${(cadPred.riskProbability * 100).toFixed(1)}%` : null);
      activeResults.push({ module: 'CAD', level: lvl, pct });
      if (pct) probs.push(`CAD: ${pct}`);
    }

    if (isDiabetesLoaded) {
      const lvl = diabetesPrediction?.risk_label || diabetesPrediction?.risk_band || 'Assessed Risk';
      const prob = diabetesPrediction?.risk_probability ? `${(diabetesPrediction.risk_probability * 100).toFixed(1)}%` : null;
      activeResults.push({ module: 'Diabetes', level: lvl, pct: prob });
      if (prob) probs.push(`Dia: ${prob}`);
    }

    if (isReadmissionLoaded) {
      const lvl = readmissionPrediction?.urgency_level || readmissionPrediction?.risk_category || 'Assessed Urgency';
      const score = readmissionPrediction?.clinical_severity_score ? `${readmissionPrediction.clinical_severity_score}/100` : null;
      activeResults.push({ module: 'Readm', level: lvl, pct: score });
      if (score) probs.push(`Readm: ${score}`);
    }

    if (activeResults.length === 0) {
      return { overallRiskLabel: 'Assessed Risk', overallProbLabel: '' };
    }

    if (activeResults.length === 1) {
      return {
        overallRiskLabel: `${activeResults[0].module}: ${activeResults[0].level}`,
        overallProbLabel: activeResults[0].pct || ''
      };
    }

    const hasHigh = activeResults.some(r => /high|immediate/i.test(r.level));
    const hasMod = activeResults.some(r => /mod|increased|surveillance/i.test(r.level));
    const overallRiskLabel = hasHigh ? 'High Risk' : (hasMod ? 'Moderate Risk' : 'Low Risk');
    const overallProbLabel = probs.join(' | ');

    return { overallRiskLabel, overallProbLabel };
  }

  const { overallRiskLabel, overallProbLabel } = computeOverallRiskSummary();

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
        content: "Welcome! I'm your **Clinical Results & SHAP Explainer**. I translate machine learning risk assessment scores and feature contributions (across CAD, Diabetes, and Hospital Readmission) into plain-language insights so you can target your risk factors effectively.",
        widget: combinedShapFactors.length > 0 ? {
          type: 'SHAP_FACTOR_CARD',
          data: {
            overall_risk: overallRiskLabel || 'Assessed Risk',
            probability: overallProbLabel || '',
            module_risks: {
              cad: isCadLoaded ? { risk: cadPred.riskLevel || 'Assessed Risk', prob: cadPred.riskPercent || (cadPred.riskProbability ? `${(cadPred.riskProbability * 100).toFixed(1)}%` : '') } : null,
              diabetes: isDiabetesLoaded ? { risk: diabetesPrediction?.risk_label || diabetesPrediction?.risk_band || 'Assessed Risk', prob: diabetesPrediction?.risk_probability ? `${(diabetesPrediction.risk_probability * 100).toFixed(1)}%` : '' } : null,
              readmission: isReadmissionLoaded ? { risk: readmissionPrediction?.urgency_level || 'Assessed Urgency', prob: readmissionPrediction?.clinical_severity_score ? `Score: ${readmissionPrediction.clinical_severity_score}/100` : '' } : null
            },
            factors: combinedShapFactors
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
        'Explain my risk factors',
        'Summarize my overall results'
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
    const cadRiskLevel = cadPred.riskLevel || cadPred.risk_level || (isCadLoaded ? 'Assessed Risk' : null);
    const cadProb = cadPred.riskPercent || (cadPred.riskProbability ? `${(cadPred.riskProbability * 100).toFixed(1)}%` : null) || (cadPred.probability ? `${(cadPred.probability * 100).toFixed(1)}%` : null);

    return {
      demographics: {
        age: cadForm.age || (diabetesForm?.Age ? String(diabetesForm.Age) : null) || readmissionForm?.age,
        gender: cadForm.gender || (cadForm.sex !== undefined ? String(cadForm.sex) : null) || (diabetesForm?.Sex !== undefined ? String(diabetesForm.Sex) : null) || readmissionForm?.gender,
        subsidy_tier: activeSubsidy
      },
      form_metrics: {
        blood_pressure: cadForm.bp || (cadForm.trestbps ? `${cadForm.trestbps} mmHg` : null),
        cholesterol: cadForm.cholesterol || (cadForm.chol ? `${cadForm.chol} mg/dL` : null),
        bmi: diabetesForm?.BMI || cadForm.bmi,
        glucose: diabetesForm?.glucose || cadForm.glucose || (cadForm.fbs === 1 || cadForm.fbs === '1' ? '> 120 mg/dL' : null),
        active_symptoms: readmissionForm?.symptoms || [],

        // Full Raw Modules
        cad_form: cadForm,
        diabetes_form: diabetesForm || {},
        readmission_form: readmissionForm || {}
      },
      ml_scores: {
        cad_risk_level: cadRiskLevel,
        cad_probability: cadProb,
        diabetes_risk_level: diabetesPrediction?.risk_label || diabetesPrediction?.risk_band,
        diabetes_probability: diabetesPrediction?.risk_probability,
        readmission_risk_level: readmissionPrediction?.urgency_level || readmissionPrediction?.risk_category,
        readmission_severity_score: readmissionPrediction?.clinical_severity_score
      },
      shap_factors: combinedShapFactors
    };
  }

  async function handleSend(promptText, targetTabOverride = null) {
    const targetTabKey = targetTabOverride || activeTab;
    const query = promptText || inputQuery;
    if (!query.trim() || loading) return;

    const userMsg = { role: 'user', content: query };
    const tabHistory = messages[targetTabKey] || [];

    setMessages(prev => ({
      ...prev,
      [targetTabKey]: [...(prev[targetTabKey] || []), userMsg]
    }));

    if (!promptText && !targetTabOverride) setInputQuery('');
    setLoading(true);

    try {
      const rawInput = getUnifiedPayload();
      const res = await sendGenAIQuery({
        userQuery: query,
        assistantType: targetTabKey,
        rawInput,
        history: tabHistory
      });

      const assistantMsg = {
        role: 'assistant',
        content: res.message || 'Thank you for your inquiry.',
        widget: res.widget || null
      };

      setMessages(prev => ({
        ...prev,
        [targetTabKey]: [...(prev[targetTabKey] || []), assistantMsg]
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
        [targetTabKey]: [...(prev[targetTabKey] || []), errorMsg]
      }));
    } finally {
      setLoading(false);
    }
  }

  function handleCrossTabNavigate(targetTab, promptText) {
    if (!tabConfig[targetTab]) return;
    setActiveTab(targetTab);
    if (promptText) {
      setTimeout(() => {
        handleSend(promptText, targetTab);
      }, 50);
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
                      onNavigateTab={(targetTab, promptText) => handleCrossTabNavigate(targetTab, promptText)}
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
