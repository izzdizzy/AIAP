import { useLocation, useNavigate } from 'react-router-dom';
import ThemeToggle from '../theme/ThemeToggle';
import Disclaimer from './Disclaimer';

export default function AppShell({
  children,
  hasPrediction = false
}) {
  const location = useLocation();
  const navigate = useNavigate();
  const currentPath = location.pathname;

  let moduleInfo = { title: 'Clinical Health Assessment Hub', eyebrow: 'AI Clinical Platform' };

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
  }

  const isCadActive = currentPath.startsWith('/cad');
  const isReadmissionActive = currentPath.startsWith('/readmission');
  const isDiabetesActive = currentPath.startsWith('/diabetes');

  return (
    <div className="app-shell">
      <header className="app-header" style={{ flexDirection: 'column', gap: '16px', alignItems: 'stretch' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '38px',
              height: '38px',
              borderRadius: '10px',
              background: 'var(--accent)',
              display: 'grid',
              placeItems: 'center',
              color: 'white',
              fontWeight: '700',
              fontSize: '18px'
            }}>
              +
            </div>
            <div>
              <p className="eyebrow" style={{ margin: 0 }}>{moduleInfo.eyebrow}</p>
              <h1 className="app-title" style={{ fontSize: '1.4rem', margin: 0 }}>{moduleInfo.title}</h1>
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
              className="nav-link"
              onClick={() => navigate('/')}
            >
              ← Hub Home
            </button>
          </div>
        </div>

        {/* Module Switcher Tabs */}
        <div style={{
          display: 'flex',
          justify: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '8px',
          borderTop: '1px solid var(--border)',
          paddingTop: '12px'
        }}>
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            <button
              type="button"
              className={isCadActive ? 'nav-link active' : 'nav-link'}
              onClick={() => navigate('/cad/assessment')}
            >
              CAD Screening
            </button>
            <button
              type="button"
              className={isReadmissionActive ? 'nav-link active' : 'nav-link'}
              onClick={() => navigate('/readmission/assessment')}
            >
              Hospital Readmission
            </button>
            <button
              type="button"
              className={isDiabetesActive ? 'nav-link active' : 'nav-link'}
              onClick={() => navigate('/diabetes/assessment')}
            >
              Diabetes Classifier
            </button>
          </div>
        </div>
      </header>
      <main className="app-main">
        <Disclaimer />
        {children}
      </main>
    </div>
  );
}
