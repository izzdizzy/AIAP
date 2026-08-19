import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import ThemeToggle from '../theme/ThemeToggle';
import Disclaimer from './Disclaimer';
import ChangePasswordModal from '../features/auth/components/ChangePasswordModal';

export default function AppShell({
  children,
  cadCompleted = false,
  readmissionCompleted = false,
  diabetesCompleted = false,
  user = null,
  onLogout = () => { }
}) {
  const location = useLocation();
  const navigate = useNavigate();
  const currentPath = location.pathname;
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const [changePasswordOpen, setChangePasswordOpen] = useState(false);

  // App name stays constant across every route.
  const moduleInfo = { title: 'General Healthcare Assessment Hub', eyebrow: 'Following Your Heart' };

  const isCadActive = currentPath.startsWith('/cad');
  const isReadmissionActive = currentPath.startsWith('/readmission');
  const isDiabetesActive = currentPath.startsWith('/diabetes');
  const isAIActive = currentPath.startsWith('/ai-insights');

  function handleCadClick() {
    navigate('/cad/assessment');
  }

  function handleReadmissionClick() {
    navigate('/readmission/assessment');
  }

  function handleDiabetesClick() {
    navigate('/diabetes/assessment');
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
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
          width: '100%'
        }}>
          {/* Left branding area — clickable, returns to the dashboard */}
          <div
            role="button"
            tabIndex={0}
            onClick={() => navigate('/')}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                navigate('/');
              }
            }}
            title="Back to Dashboard"
            style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}
          >
            <div style={{ position: 'relative' }}>
              <img
                src="../theme/icon.png"
                alt="App Icon"
                style={{
                  width: '34px',
                  height: '34px',
                  borderRadius: '8px',
                  objectFit: 'cover',
                  display: 'block'
                }}
              />
            </div>
            <div>
              <p className="eyebrow" style={{ margin: 0, fontSize: '0.75rem' }}>{moduleInfo.eyebrow}</p>
              <h1 className="app-title" style={{ fontSize: '1.15rem', margin: 0, lineHeight: 1.2 }}>{moduleInfo.title}</h1>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginLeft: 'auto' }}>
            <ThemeToggle />
            {user ? (
              <div style={{ position: 'relative' }}>
                <button
                  type="button"
                  onClick={() => setAccountMenuOpen(prev => !prev)}
                  title={user.name}
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    background: 'var(--accent)',
                    color: 'white',
                    border: '1px solid var(--border)',
                    fontSize: '0.8rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'grid',
                    placeItems: 'center'
                  }}
                >
                  {(user.name || '?').trim().split(/\s+/).map(part => part[0]).slice(0, 2).join('').toUpperCase()}
                </button>
                {accountMenuOpen && (
                  <div style={{
                    position: 'absolute',
                    right: 0,
                    top: 'calc(100% + 6px)',
                    background: 'var(--surface)',
                    border: '1px solid var(--border)',
                    borderRadius: '10px',
                    boxShadow: 'var(--shadow, 0 8px 24px rgba(0,0,0,0.25))',
                    minWidth: '180px',
                    zIndex: 50,
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      padding: '10px 14px',
                      borderBottom: '1px solid var(--border)',
                      fontSize: '0.8rem',
                      color: 'var(--text-muted)'
                    }}>
                      Signed in as<br />
                      <strong style={{ color: 'var(--text)' }}>{user.name}</strong>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setAccountMenuOpen(false);
                        setChangePasswordOpen(true);
                      }}
                      style={{
                        display: 'block',
                        width: '100%',
                        textAlign: 'left',
                        padding: '10px 14px',
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--text)',
                        fontSize: '0.85rem',
                        cursor: 'pointer'
                      }}
                    >
                      Change password
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setAccountMenuOpen(false);
                        onLogout();
                      }}
                      style={{
                        display: 'block',
                        width: '100%',
                        textAlign: 'left',
                        padding: '10px 14px',
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--danger, #dc2626)',
                        fontSize: '0.85rem',
                        cursor: 'pointer'
                      }}
                    >
                      Log out
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <button
                type="button"
                onClick={() => navigate('/login')}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  padding: '6px 12px',
                  borderRadius: '8px',
                  background: '#1e3a8a',
                  color: 'white',
                  border: '1px solid #1e3a8a',
                  fontSize: '0.82rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                Sign in
              </button>
            )}
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
          
          <div style={{ width: '1px', height: '18px', background: 'var(--border)', margin: '0 4px' }} />

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
        </div>
      </header>
      <main className="app-main">
        <Disclaimer />
        {(currentPath.startsWith('/cad') ||
          currentPath.startsWith('/readmission') ||
          currentPath.startsWith('/diabetes')) && (
            <button
              type="button"
              onClick={() => navigate('/')}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                alignSelf: 'flex-start',
                padding: '6px 14px',
                marginBottom: '12px',
                borderRadius: '8px',
                background: 'transparent',
                color: 'var(--text-muted)',
                border: '1px solid var(--border)',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'color 160ms ease, border-color 160ms ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = 'var(--text)';
                e.currentTarget.style.borderColor = 'var(--accent)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = 'var(--text-muted)';
                e.currentTarget.style.borderColor = 'var(--border)';
              }}
            >
              ← Back to Dashboard
            </button>
          )}
        {children}
      </main>
      {changePasswordOpen && (
        <ChangePasswordModal onClose={() => setChangePasswordOpen(false)} />
      )}
    </div>
  );
}
