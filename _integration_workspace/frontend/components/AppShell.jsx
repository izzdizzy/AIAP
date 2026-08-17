export default function AppShell({
  children,
  currentRoute,
  onNavigate,
  hasPrediction
}) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">CAD screening prototype</p>
          <h1 className="app-title">CAD Risk Check</h1>
        </div>
        <nav className="app-nav" aria-label="Primary">
          <button type="button" className={currentRoute === 'home' ? 'nav-link active' : 'nav-link'} onClick={() => onNavigate('home')}>
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
