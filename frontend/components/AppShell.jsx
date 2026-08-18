import { useLocation, useNavigate } from 'react-router-dom';
import ThemeToggle from '../theme/ThemeToggle';
import Disclaimer from './Disclaimer';

export default function AppShell({
  children,
  cadCompleted = false,
  readmissionCompleted = false,
  diabetesCompleted = false
}) {
  const location = useLocation();
  const navigate = useNavigate();
  const currentPath = location.pathname;

  let moduleInfo = { title: 'Clinical Health Assessment Hub', eyebrow: 'Patient Health Assessment' };

  if (currentPath.startsWith('/cad/assessment')) {
    moduleInfo = { title: 'Coronary Artery Disease Risk Assessment', eyebrow: 'Cardiovascular Module' };
  } else if (currentPath.startsWith('/cad/results')) {
    moduleInfo = { title: 'CAD Screening Results & Recommendations', eyebrow: 'Cardiovascular Module' };
  } else if (currentPath.startsWith('/cad/chat')) {
    moduleInfo = { title: 'AI Lifestyle Assistant', eyebrow: 'Cardiovascular Module' };
  } else if (currentPath.startsWith('/readmission/assessment')) {
    moduleInfo = { title: '30-Day Hospital Readmission Monitor', eyebrow: 'Inpatient Care Module' };
  } else if (currentPath.startsWith('/readmission/results')) {
    moduleInfo = { title: 'Hospital Readmission Risk Findings', eyebrow: 'Inpatient Care Module' };
  } else if (currentPath.startsWith('/diabetes/assessment')) {
    moduleInfo = { title: 'Diabetes Chronic Risk Classifier', eyebrow: 'Endocrine Module' };
  } else if (currentPath.startsWith('/diabetes/results')) {
    moduleInfo = { title: 'Diabetes Assessment Findings', eyebrow: 'Endocrine Module' };
  } else if (currentPath.startsWith('/ai-insights')) {
    moduleInfo = { title: 'Unified AI Insights & Care Navigation Workspace', eyebrow: 'GenAI Multi-Assistant Hub' };
  }

  const isCadActive = currentPath.startsWith('/cad');
  const isReadmissionActive = currentPath.startsWith('/readmission');
  const isDiabetesActive = currentPath.startsWith('/diabetes');
  const isAIActive = currentPath.startsWith('/ai-insights');

  function handleCadClick() {
    if (cadCompleted && !currentPath.startsWith('/cad')) {
      navigate('/cad/results');
    } else {
      navigate('/cad/assessment');
    }
  }

  function handleReadmissionClick() {
    if (readmissionCompleted && !currentPath.startsWith('/readmission')) {
      navigate('/readmission/results');
    } else {
      navigate('/readmission/assessment');
    }
  }

  function handleDiabetesClick() {
    if (diabetesCompleted && !currentPath.startsWith('/diabetes')) {
      navigate('/diabetes/results');
    } else {
      navigate('/diabetes/assessment');
    }
  }

  return (
    <div className="app-shell">
      <header className="app-header" style={{
        padding: '12px 20px',
        gap: '12px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'stretch',
        width: '100%',
        boxSizing: 'border-box'
      }}>
        {/* Top Tier: Branding (Left) & Utility Actions (Right) */}
        <div style={{
          display: 'flex',
          justify: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
          width: '100%'
        }}>
          {/* Left branding area */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ position: 'relative' }}>
              <div style={{
                width: '34px',
                height: '34px',
                borderRadius: '8px',
                background: 'var(--accent)',
                display: 'grid',
                placeItems: 'center',
                color: 'white',
                fontWeight: '700',
                fontSize: '16px'
              }}>
                +
              </div>
              <span
                title="Service Online"
                style={{
                  position: 'absolute',
                  bottom: '-2px',
                  right: '-2px',
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: '#16a34a',
                  border: '2px solid var(--surface, #0f172a)'
                }}
              />
            </div>
            <div>
              <p className="eyebrow" style={{ margin: 0, fontSize: '0.75rem' }}>{moduleInfo.eyebrow}</p>
              <h1 className="app-title" style={{ fontSize: '1.15rem', margin: 0, lineHeight: 1.2 }}>{moduleInfo.title}</h1>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '999px',
              background: 'var(--surface-muted)',
              border: '1px solid var(--border)',
              fontSize: '0.8rem',
              color: 'var(--text-muted)'
            }}>
              <span style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: 'var(--risk-low-text)'
              }} />
              <span>Service Online</span>
            </div>
            <ThemeToggle />
            <button
              type="button"
              onClick={() => navigate('/')}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                borderRadius: '8px',
                background: 'var(--surface-muted, rgba(255,255,255,0.05))',
                color: 'var(--text, #f8fafc)',
                border: '1px solid var(--border)',
                fontSize: '0.82rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
              title="Dashboard"
            >
              <span>🏠</span>
              <span>Dashboard</span>
            </button>
          </div>
        </div>

        {/* Bottom Tier: Segmented Module Navigation Tabs */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          borderTop: '1px solid var(--border)',
          paddingTop: '8px',
          width: '100%',
          justifyContent: 'flex-start',
          overflowX: 'auto'
        }}>
          <button
            type="button"
            onClick={handleCadClick}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '8px',
              fontSize: '0.85rem',
              fontWeight: isCadActive ? 600 : 500,
              background: isCadActive ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
              color: isCadActive ? 'var(--text, #ffffff)' : 'var(--text-muted, #94a3b8)',
              border: isCadActive ? '1px solid var(--accent, #38bdf8)' : '1px solid transparent',
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: cadCompleted ? '#16a34a' : '#f59e0b'
              }}
              title={cadCompleted ? 'Complete' : 'Pending'}
            />
            <span>CAD</span>
          </button>

          <button
            type="button"
            onClick={handleReadmissionClick}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '8px',
              fontSize: '0.85rem',
              fontWeight: isReadmissionActive ? 600 : 500,
              background: isReadmissionActive ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
              color: isReadmissionActive ? 'var(--text, #ffffff)' : 'var(--text-muted, #94a3b8)',
              border: isReadmissionActive ? '1px solid var(--accent, #38bdf8)' : '1px solid transparent',
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: readmissionCompleted ? '#16a34a' : '#f59e0b'
              }}
              title={readmissionCompleted ? 'Complete' : 'Pending'}
            />
            <span>Readmission</span>
          </button>

          <button
            type="button"
            onClick={handleDiabetesClick}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '8px',
              fontSize: '0.85rem',
              fontWeight: isDiabetesActive ? 600 : 500,
              background: isDiabetesActive ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
              color: isDiabetesActive ? 'var(--text, #ffffff)' : 'var(--text-muted, #94a3b8)',
              border: isDiabetesActive ? '1px solid var(--accent, #38bdf8)' : '1px solid transparent',
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: diabetesCompleted ? '#16a34a' : '#f59e0b'
              }}
              title={diabetesCompleted ? 'Complete' : 'Pending'}
            />
            <span>Diabetes</span>
          </button>

          <button
            type="button"
            onClick={() => navigate('/ai-insights')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '8px',
              fontSize: '0.85rem',
              fontWeight: isAIActive ? 700 : 600,
              background: isAIActive ? 'rgba(16, 185, 129, 0.25)' : 'rgba(16, 185, 129, 0.12)',
              color: isAIActive ? '#34d399' : '#10b981',
              border: '1px solid #10b981',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
              marginLeft: 'auto'
            }}
          >
            <span>✨</span>
            <span>AI Insights Workspace</span>
          </button>

          <div style={{ width: '1px', height: '18px', background: 'var(--border)', margin: '0 4px' }} />
        </div>
      </header>
      <main className="app-main">
        <Disclaimer />
        {children}
      </main>
    </div>
  );
}
