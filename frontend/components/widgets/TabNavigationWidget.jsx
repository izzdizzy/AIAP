import React from 'react';

export default function TabNavigationWidget({ data, onNavigateTab }) {
  if (!data) return null;

  const {
    target_tab,
    button_label = 'Switch Tab & Ask Assistant',
    prompt_text = '',
    description = ''
  } = data;

  const handleClick = () => {
    if (onNavigateTab) {
      onNavigateTab(target_tab, prompt_text);
    }
  };

  return (
    <div style={{
      marginTop: '12px',
      marginBottom: '12px',
      padding: '12px 16px',
      borderRadius: '10px',
      background: 'rgba(59, 130, 246, 0.08)',
      border: '1px solid rgba(59, 130, 246, 0.3)',
      display: 'flex',
      flexDirection: 'column',
      gap: '8px'
    }}>
      {description && (
        <div style={{ fontSize: '0.82rem', color: 'var(--text-muted, #94a3b8)', lineHeight: '1.4' }}>
          {description}
        </div>
      )}
      <button
        type="button"
        onClick={handleClick}
        style={{
          alignSelf: 'flex-start',
          padding: '8px 16px',
          borderRadius: '8px',
          background: '#3b82f6',
          color: '#ffffff',
          fontWeight: '600',
          fontSize: '0.85rem',
          border: 'none',
          cursor: 'pointer',
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          boxShadow: '0 2px 8px rgba(59, 130, 246, 0.3)',
          transition: 'all 0.15s ease'
        }}
        onMouseOver={(e) => e.currentTarget.style.opacity = '0.9'}
        onMouseOut={(e) => e.currentTarget.style.opacity = '1.0'}
      >
        <span>{button_label}</span>
      </button>
    </div>
  );
}
