import React from 'react';
import { Link } from 'react-router-dom';

const MODIFIABLE_KEYS = new Set([
  // Diabetes
  'BMI', 'HighBP', 'HighChol', 'PhysActivity', 'Smoker', 'Fruits', 'Veggies', 'GenHlth', 'HvyAlcoholConsump',
  // CAD
  'trestbps', 'chol', 'fbs', 'thalach', 'exang', 'oldpeak',
  // Readmission
  'num_medications', 'medication_count', 'total_medications', 'num_lab_procedures', 'high_lab_utilization',
  'chas_tier', 'number_outpatient', 'on_insulin', 'insulin_complexity', 'oral_medications'
]);

const FACTOR_LABELS = {
  // Diabetes
  GenHlth: 'General Health Self-Assessment',
  HighBP: 'High Blood Pressure Status',
  BMI: 'Body Mass Index (BMI)',
  HighChol: 'High Cholesterol Level',
  Age: 'Patient Age Decade',
  DiffWalk: 'Difficulty Walking / Mobility',
  PhysActivity: 'Physical Activity Level',
  Smoker: 'Smoking History',
  HeartDiseaseorAttack: 'Heart Condition / Prior Attack',
  Fruits: 'Daily Fruit Consumption',
  Veggies: 'Daily Vegetable Consumption',
  HvyAlcoholConsump: 'Heavy Alcohol Consumption',
  Sex: 'Biological Sex',
  Stroke: 'Prior Stroke History',
  MentHlth: 'Mental Health Assessment',
  PhysHlth: 'Physical Health Assessment',

  // CAD
  trestbps: 'Resting Blood Pressure',
  chol: 'Serum Cholesterol',
  fbs: 'Fasting Blood Sugar',
  thalach: 'Max Heart Rate Achieved',
  exang: 'Exercise Induced Angina',
  oldpeak: 'ST Depression (Oldpeak)',
  age: 'Patient Age',
  sex: 'Biological Sex',
  cp: 'Chest Pain Type',
  restecg: 'Resting ECG Findings',
  slope: 'ST Segment Slope',
  ca: 'Major Vessels Count',
  thal: 'Thalassemia Perfusion Status',

  // Readmission
  inpatient_ratio: 'Inpatient Stay Ratio',
  time_in_hospital: 'Hospital Stay Duration',
  number_inpatient: 'Inpatient Visits Count',
  number_emergency: 'Emergency Room Visits',
  number_outpatient: 'Outpatient Visits Count',
  comorbidity_count: 'Comorbidities Count',
  number_diagnoses: 'Number of Diagnoses',
  num_lab_procedures: 'Lab Procedures Count',
  num_medications: 'Medication Count & Regimen',
  medication_count: 'Medication Count & Regimen',
  prior_admissions: 'Prior Hospital Admissions',
  total_prior_admissions: 'Total Prior Admissions',
  chas_tier: 'CHAS Healthcare Subsidy Tier'
};

const FACTOR_GUIDANCE = {
  // Diabetes
  GenHlth: 'Improving overall health through sleep, diet, and activity lowers risk contribution.',
  HighBP: 'Blood pressure can often be optimized through diet, exercise, and prescribed medication.',
  BMI: 'Gradual weight management directly reduces metabolic risk burden.',
  HighChol: 'Cholesterol responds well to dietary adjustments and lipid-lowering treatments.',
  PhysActivity: 'Regular activity — even brisk daily walking — actively lowers risk.',
  Smoker: 'Quitting smoking improves insulin sensitivity and overall vascular health.',
  Fruits: 'Daily fruit intake supports better glycemic control and nutrition.',
  Veggies: 'Vegetables help manage weight, blood sugar, and metabolic health.',
  HvyAlcoholConsump: 'Reducing alcohol intake supports liver function and metabolic health.',
  Age: 'Age is a non-modifiable baseline factor — making lifestyle factors even more key.',
  Sex: 'Biological sex influences baseline metabolic and hormonal risk profiles.',
  DiffWalk: 'Mobility limitations can be supported with low-impact physical therapy.',
  HeartDiseaseorAttack: 'Existing cardiovascular conditions raise baseline metabolic risk.',
  Stroke: 'Prior stroke history requires close ongoing clinical coordination.',

  // CAD
  trestbps: 'Optimal blood pressure management reduces strain on coronary arteries.',
  chol: 'Dietary adjustments and statin therapy help prevent arterial plaque accumulation.',
  fbs: 'Maintaining target fasting glucose prevents vascular endothelial damage.',
  thalach: 'Aerobic exercise conditioning improves cardiac reserve and peak heart rate.',
  exang: 'Angina symptoms respond to targeted anti-ischemic medication and rehab.',
  oldpeak: 'ST depression reflects ischemic stress during cardiac workload.',
  age: 'Cardiovascular risk naturally increases over time — managing modifiable factors helps.',
  sex: 'Biological sex plays a baseline role in coronary disease prevalence.',
  cp: 'Symptom characteristics reflect underlying cardiac ischemic patterns.',
  restecg: 'Baseline ECG findings show structural or electrical heart variations.',
  slope: 'ST segment slope reflects myocardial blood flow response during stress.',
  ca: 'Number of involved major vessels indicates coronary anatomical burden.',
  thal: 'Perfusion imaging shows fixed vs reversible myocardial blood flow.',

  // Readmission
  num_medications: 'Medication reconciliation and adherence prevent post-discharge events.',
  medication_count: 'Medication reconciliation and adherence prevent post-discharge events.',
  num_lab_procedures: 'Outpatient monitoring labs allow timely medical adjustments post-discharge.',
  chas_tier: 'Healthcare subsidy support ensures uninterrupted medication access.',
  number_outpatient: 'Regular outpatient appointments reduce acute hospital readmissions.',
  time_in_hospital: 'Hospital stay duration reflects acute illness severity during admission.',
  prior_admissions: 'Prior admission history indicates chronic illness recurrence risk.',
  total_prior_admissions: 'Prior admission history indicates chronic illness recurrence risk.',
  number_inpatient: 'Inpatient visit frequency highlights chronic disease complexity.',
  number_emergency: 'Emergency visits reflect acute symptom exacerbations.',
  comorbidity_count: 'Managing multiple chronic conditions prevents acute decompensation.',
  number_diagnoses: 'Multiple diagnoses require coordinated multidisciplinary follow-up.'
};

function formatFeatureLabel(key) {
  if (!key) return 'Factor';
  if (FACTOR_LABELS[key]) return FACTOR_LABELS[key];
  return String(key)
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/\b\w/g, char => char.toUpperCase());
}

function isModifiableFactor(key) {
  if (MODIFIABLE_KEYS.has(key)) return true;
  const l = String(key || '').toLowerCase();
  return (
    l.includes('bmi') ||
    l.includes('bp') ||
    l.includes('chol') ||
    l.includes('smok') ||
    l.includes('phys') ||
    l.includes('med') ||
    l.includes('fruit') ||
    l.includes('veggie') ||
    l.includes('diet') ||
    l.includes('alcohol') ||
    l.includes('fbs') ||
    l.includes('glucose') ||
    l.includes('lab') ||
    l.includes('outpatient') ||
    l.includes('angina') ||
    l.includes('oldpeak') ||
    l.includes('insulin')
  );
}

function normalizeFactors(factors) {
  return (factors || []).map((f, idx) => {
    let key = `factor_${idx}`;
    let rawLabel = '';
    let val = 0;

    if (typeof f === 'string') {
      key = f;
      rawLabel = f;
      val = 0.1;
    } else if (typeof f === 'object' && f !== null) {
      key = f.feature || f.key || f.label || f.name || `factor_${idx}`;
      rawLabel = f.label || f.feature || f.name || key;

      if (typeof f.impact === 'number') val = f.impact;
      else if (typeof f.shap_value === 'number') val = f.shap_value;
      else if (typeof f.value === 'number') val = f.value;
      else if (typeof f.importance === 'number') val = f.importance;
    }

    const label = FACTOR_LABELS[key] || FACTOR_LABELS[rawLabel] || formatFeatureLabel(rawLabel || key);
    const modifiable = isModifiableFactor(key) || isModifiableFactor(rawLabel);
    const guidance = FACTOR_GUIDANCE[key] || FACTOR_GUIDANCE[rawLabel] || (
      modifiable
        ? 'Lifestyle adjustments and clinical follow-up help manage this factor.'
        : 'Baseline clinical parameter evaluated by the risk model.'
    );

    return {
      key,
      label,
      impact: val,
      modifiable,
      guidance
    };
  });
}

function FactorRow({ factor, maxAbs }) {
  const isPositive = factor.impact >= 0;
  const absVal = Math.abs(factor.impact);
  const widthPct = maxAbs > 0 ? Math.max(6, (absVal / maxAbs) * 100) : 6;
  const formattedImpact = absVal < 0.001 && absVal !== 0 ? absVal.toExponential(2) : absVal.toFixed(3);

  return (
    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 py-3.5 urc-divider border-b last:border-0">
      {/* Left Column: Description Details (58% width) */}
      <div className="w-full md:w-[58%] flex-shrink-0">
        <div className="text-sm font-semibold urc-text-bright">{factor.label}</div>
        <div className="text-xs urc-text-muted mt-0.5 leading-relaxed">{factor.guidance}</div>
      </div>

      {/* Right Column: Progress Bar + Impact Value (42% width) */}
      <div className="w-full md:w-[40%] flex items-center justify-end gap-3">
        <div className="w-full max-w-[240px] urc-track h-2 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${isPositive ? 'bg-rose-500' : 'bg-teal-500'
              }`}
            style={{ width: `${widthPct}%` }}
          />
        </div>

        {/* Value Tag with Directional Indicator */}
        <span
          className={`text-xs font-bold whitespace-nowrap min-w-[70px] text-right ${isPositive ? 'urc-tag-pos' : 'urc-tag-neg'
            }`}
        >
          {isPositive ? `▲ +${formattedImpact}` : `▼ -${formattedImpact}`}
        </span>
      </div>
    </div>
  );
}

/**
 * Reusable Unified Results Card Component
 * Standardized across CAD, Hospital Readmission, and Diabetes screening modules.
 */
export default function UnifiedResultsCard({
  title = 'Assessment Findings',
  probLabel = 'Risk Probability',
  probValue = '0.0%',
  riskBadgeLabel = 'Standard Risk',
  riskLevel = 'Low',
  factors = [],
  onOpenChat,
  onEditAssessment,
  onBackToOverview,
  disableChat = false,
  emptyMessage = 'No assessment prediction found. Please complete the assessment form first.',
  isMissingPrediction = false,
  user = null
}) {
  const styleBlock = (
    <style>{`
      .unified-results-wrapper, .unified-results-wrapper * { box-sizing: border-box; }

      /* Default / Dark Theme Styles */
      .unified-results-wrapper .urc-card {
        background-color: #151c2e !important;
        border: 1px solid #2e3a50 !important;
        color: #f8fafc !important;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.35) !important;
      }
      .unified-results-wrapper .urc-text-white { color: #ffffff !important; }
      .unified-results-wrapper .urc-text-bright { color: #f8fafc !important; }
      .unified-results-wrapper .urc-text-muted { color: #94a3b8 !important; }
      .unified-results-wrapper .urc-btn-secondary {
        background-color: rgba(30, 41, 59, 0.8) !important;
        border: 1px solid rgba(51, 65, 85, 0.8) !important;
        color: #f1f5f9 !important;
      }
      .unified-results-wrapper .urc-btn-secondary:hover {
        background-color: rgba(51, 65, 85, 0.8) !important;
        color: #ffffff !important;
      }
      .unified-results-wrapper .urc-track { background-color: rgba(30, 41, 59, 0.8) !important; }
      .unified-results-wrapper .urc-divider { border-color: rgba(51, 65, 85, 0.6) !important; }
      .unified-results-wrapper .urc-tag-pos { color: #f43f5e !important; }
      .unified-results-wrapper .urc-tag-neg { color: #2dd4bf !important; }

      .unified-results-wrapper .urc-badge-high {
        background-color: rgba(244, 63, 94, 0.2) !important;
        color: #fda4af !important;
        border: 1px solid rgba(244, 63, 94, 0.4) !important;
      }
      .unified-results-wrapper .urc-badge-mod {
        background-color: rgba(245, 158, 11, 0.2) !important;
        color: #fde047 !important;
        border: 1px solid rgba(245, 158, 11, 0.4) !important;
      }
      .unified-results-wrapper .urc-badge-low {
        background-color: rgba(16, 185, 129, 0.2) !important;
        color: #6ee7b7 !important;
        border: 1px solid rgba(16, 185, 129, 0.4) !important;
      }

      /* Light Theme Overrides */
      [data-theme='light'] .unified-results-wrapper .urc-card {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        color: #0f172a !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06) !important;
      }
      [data-theme='light'] .unified-results-wrapper .urc-text-white { color: #ffffff !important; }
      [data-theme='light'] .unified-results-wrapper .urc-text-bright { color: #0f172a !important; }
      [data-theme='light'] .unified-results-wrapper .urc-text-muted { color: #64748b !important; }
      [data-theme='light'] .unified-results-wrapper .urc-btn-secondary {
        background-color: #f1f5f9 !important;
        border: 1px solid #cbd5e1 !important;
        color: #334155 !important;
      }
      [data-theme='light'] .unified-results-wrapper .urc-btn-secondary:hover {
        background-color: #e2e8f0 !important;
        color: #0f172a !important;
      }
      [data-theme='light'] .unified-results-wrapper .urc-track { background-color: #e2e8f0 !important; }
      [data-theme='light'] .unified-results-wrapper .urc-divider { border-color: #e2e8f0 !important; }
      [data-theme='light'] .unified-results-wrapper .urc-tag-pos { color: #e11d48 !important; }
      [data-theme='light'] .unified-results-wrapper .urc-tag-neg { color: #0d9488 !important; }

      [data-theme='light'] .unified-results-wrapper .urc-badge-high {
        background-color: #ffe4e6 !important;
        color: #be123c !important;
        border: 1px solid #fca5a5 !important;
      }
      [data-theme='light'] .unified-results-wrapper .urc-badge-mod {
        background-color: #fef3c7 !important;
        color: #92400e !important;
        border: 1px solid #fcd34d !important;
      }
      [data-theme='light'] .unified-results-wrapper .urc-badge-low {
        background-color: #d1fae5 !important;
        color: #065f46 !important;
        border: 1px solid #6ee7b7 !important;
      }
    `}</style>
  );

  if (isMissingPrediction) {
    return (
      <div className="unified-results-wrapper w-full max-w-4xl mx-auto my-6 px-4">
        {styleBlock}
        <h2 className="text-xl font-bold urc-text-bright mb-4">{title}</h2>
        <div className="urc-card rounded-2xl p-8 text-center shadow-xl">
          <p className="urc-text-muted mb-6 text-base">{emptyMessage}</p>
          {onEditAssessment && (
            <button
              type="button"
              onClick={onEditAssessment}
              className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm px-6 py-2.5 rounded-lg transition-all shadow-md"
            >
              Start Assessment
            </button>
          )}
        </div>
      </div>
    );
  }

  const normalized = normalizeFactors(factors);
  const maxAbs = Math.max(...normalized.map(f => Math.abs(f.impact)), 0.01);

  const modifiableFactors = normalized.filter(f => f.modifiable);
  const fixedFactors = normalized.filter(f => !f.modifiable);

  // Risk Badge Styling
  const levelText = String(riskLevel || riskBadgeLabel || '').toLowerCase();
  let badgeClass = 'urc-badge-low';
  if (levelText.includes('high')) {
    badgeClass = 'urc-badge-high';
  } else if (levelText.includes('mod')) {
    badgeClass = 'urc-badge-mod';
  }

  return (
    <div className="unified-results-wrapper w-full max-w-4xl mx-auto my-6 px-4 space-y-6">
      {styleBlock}

      {/* 1. Unified Action Toolbar Component */}
      <div className="urc-card rounded-xl p-4 shadow-lg flex flex-wrap items-center justify-between gap-3">
        {/* Primary Fancy AI Button */}
        {onOpenChat && (
          <button
            type="button"
            onClick={onOpenChat}
            disabled={disableChat}
            className="inline-flex items-center gap-2 bg-gradient-to-r from-violet-600 via-indigo-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 urc-text-white font-semibold text-sm px-5 py-2.5 rounded-lg shadow-lg shadow-indigo-500/25 transition-all duration-200 cursor-pointer disabled:opacity-50 border-0"
          >
            <span>✨</span> Ask AI Assistant
          </button>
        )}

        {/* Secondary Navigation Buttons */}
        <div className="flex items-center gap-2 flex-wrap">
          {onEditAssessment && (
            <button
              type="button"
              onClick={onEditAssessment}
              className="inline-flex items-center gap-1.5 urc-btn-secondary font-medium text-sm px-4 py-2 rounded-lg transition-all duration-200"
            >
              + New Assessment
            </button>
          )}

          {onBackToOverview && (
            <button
              type="button"
              onClick={onBackToOverview}
              className="inline-flex items-center gap-1.5 urc-btn-secondary font-medium text-sm px-4 py-2 rounded-lg transition-all duration-200"
            >
              ← Return to Module Overview
            </button>
          )}
        </div>
      </div>

      {/* 2. Standardized Hero Metric Card */}
      <div className="urc-card rounded-2xl p-6 sm:p-8 shadow-xl">
        <p className="text-xs font-bold urc-text-muted tracking-wider uppercase mb-2">
          {title}
        </p>

        <div className="flex items-baseline gap-4 flex-wrap mt-2 mb-3">
          <span className="text-5xl font-extrabold urc-text-bright tracking-tight">
            {probValue}
          </span>
          <span className={`text-sm font-semibold px-3.5 py-1.5 rounded-full inline-flex items-center gap-1.5 ${badgeClass}`}>
            {riskBadgeLabel}
          </span>
        </div>

        <p className="urc-text-muted text-sm max-w-xl leading-relaxed mt-3">
          This is the model's estimated probability based on your input metrics. It is a clinical screening aid, not a definitive diagnosis — please discuss these findings with a qualified healthcare professional.
        </p>
      </div>

      {/* Guest save prompt if unauthenticated */}
      {!user && (
        <div className="urc-card rounded-xl p-4 flex items-center justify-between flex-wrap gap-3 text-sm urc-text-muted">
          <span>Create a free account to save this result and track your risk over time.</span>
          <Link to="/register" className="text-teal-600 dark:text-teal-400 hover:underline font-semibold inline-flex items-center gap-1">
            Create account →
          </Link>
        </div>
      )}

      {/* 3. Combined SHAP Risk Factor Card Architecture */}
      <div className="urc-card rounded-2xl p-6 sm:p-8 shadow-xl">
        <h3 className="text-base font-bold urc-text-bright mb-6">
          Contributing Risk Factors (SHAP Feature Importance)
        </h3>

        {normalized.length === 0 ? (
          <p className="urc-text-muted text-sm">No feature impact factors calculated yet.</p>
        ) : (
          <div className="space-y-6">
            {/* WITHIN YOUR CONTROL Section */}
            {modifiableFactors.length > 0 && (
              <div>
                <div className="text-xs font-bold urc-text-muted tracking-wider uppercase mb-2 flex items-center gap-2">
                  <span>WITHIN YOUR CONTROL</span>
                </div>
                <div className="border-b urc-divider pb-2">
                  {modifiableFactors.map((f, i) => (
                    <FactorRow key={f.key || i} factor={f} maxAbs={maxAbs} />
                  ))}
                </div>
              </div>
            )}

            {/* FIXED FACTORS Section */}
            {fixedFactors.length > 0 && (
              <div>
                <div className="text-xs font-bold urc-text-muted tracking-wider uppercase mb-2 flex items-center gap-2">
                  <span>FIXED FACTORS</span>
                </div>
                <div>
                  {fixedFactors.map((f, i) => (
                    <FactorRow key={f.key || i} factor={f} maxAbs={maxAbs} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

