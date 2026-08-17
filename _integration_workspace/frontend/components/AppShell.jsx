export default function AppShell({
  children,
  currentRoute,
  onNavigate,
  hasPrediction,
  onBackToLanding
}) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="flex items-center gap-4">
          {/* Back to Main Menu button - only show when not on landing page */}
          {currentRoute !== 'landing' && onBackToLanding && (
            <button
              type="button"
              onClick={onBackToLanding}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.5rem 1rem',
                backgroundColor: '#374151',
                color: '#f3f4f6',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: '500'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#4b5563';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#374151';
              }}
            >
              <svg style={{ width: '16px', height: '16px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back to Main Menu
            </button>
          )}
          <div>
            <p className="eyebrow">CAD screening prototype</p>
            <h1 className="app-title">CAD Risk Check</h1>
          </div>
        </div>
        <nav className="app-nav" aria-label="Primary">
          <button type="button" className={currentRoute === 'landing' ? 'nav-link active' : 'nav-link'} onClick={() => onNavigate('landing')}>
            Home
          </button>
          <button type="button" className={currentRoute === 'assessment' ? 'nav-link active' : 'nav-link'} onClick={() => onNavigate('assessment')}>
            Assessment
          </button>
          <button
            type="button"
            className={currentRoute === 'results' ? 'nav-link active' : 'nav-link'}
            onClick={() => onNavigate('results')}
            disabled={!hasPrediction}
          >
            Results
          </button>
          <button
            type="button"
            className={currentRoute === 'chat' ? 'nav-link active' : 'nav-link'}
            onClick={() => onNavigate('chat')}
            disabled={!hasPrediction}
          >
            Lifestyle Chatbot
          </button>
        </nav>
      </header>
      <main className="app-main">{children}</main>
    </div>
  );
}
