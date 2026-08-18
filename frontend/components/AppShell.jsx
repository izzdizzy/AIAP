import ThemeToggle from '../theme/ThemeToggle';

export default function AppShell({
  children,
  currentRoute,
  onNavigate,
  hasPrediction,
  onBackToLanding
}) {
  const moduleInfo = {
    assessment: { title: 'Coronary Artery Disease Risk', eyebrow: 'Cardiovascular Module' },
    results: { title: 'CAD Risk Results & Recommendations', eyebrow: 'Cardiovascular Module' },
    chat: { title: 'AI Lifestyle Assistant', eyebrow: 'Cardiovascular Module' },
    readmission: { title: '30-Day Hospital Readmission Monitor', eyebrow: 'Inpatient Care Module' },
    diabetes: { title: 'Diabetes Chronic Risk Classifier', eyebrow: 'Endocrine Module' }
  }[currentRoute] || { title: 'Clinical Health Assessment Hub', eyebrow: 'AI Clinical Platform' };

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
            <ThemeToggle />
            <button
              type="button"
              className="nav-link"
              onClick={() => onNavigate ? onNavigate('landing') : onBackToLanding?.()}
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
              className={['assessment', 'results', 'chat'].includes(currentRoute) ? 'nav-link active' : 'nav-link'}
              onClick={() => onNavigate('assessment')}
            >
              CAD Screening
            </button>
            <button
              type="button"
              className={currentRoute === 'readmission' ? 'nav-link active' : 'nav-link'}
              onClick={() => onNavigate('readmission')}
            >
              Hospital Readmission
            </button>
            <button
              type="button"
              className={currentRoute === 'diabetes' ? 'nav-link active' : 'nav-link'}
              onClick={() => onNavigate('diabetes')}
            >
              Diabetes Classifier
            </button>
          </div>

          {/* Sub-nav for CAD route if in CAD screening */}
          {['assessment', 'results', 'chat'].includes(currentRoute) && (
            <div style={{ display: 'flex', gap: '6px' }}>
              <button
                type="button"
                className={currentRoute === 'assessment' ? 'nav-link active' : 'nav-link'}
                onClick={() => onNavigate('assessment')}
                style={{ padding: '6px 12px', fontSize: '0.82rem' }}
              >
                Form
              </button>
              <button
                type="button"
                className={currentRoute === 'results' ? 'nav-link active' : 'nav-link'}
                onClick={() => onNavigate('results')}
                disabled={!hasPrediction}
                style={{ padding: '6px 12px', fontSize: '0.82rem' }}
              >
                Results
              </button>
              <button
                type="button"
                className={currentRoute === 'chat' ? 'nav-link active' : 'nav-link'}
                onClick={() => onNavigate('chat')}
                disabled={!hasPrediction}
                style={{ padding: '6px 12px', fontSize: '0.82rem' }}
              >
                Chat Assistant
              </button>
            </div>
          )}
        </div>
      </header>
      <main className="app-main">{children}</main>
    </div>
  );
}
