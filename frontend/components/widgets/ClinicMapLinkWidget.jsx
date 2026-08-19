import React from 'react';

export default function ClinicMapLinkWidget({ data }) {
  if (!data) return null;

  const {
    facility_type = "Polyclinic",
    subsidy_tier = "CHAS Blue",
    url,
    label
  } = data;

  const mapUrl = url || `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${subsidy_tier} ${facility_type} near me`)}`;
  const buttonLabel = label || `Find Nearby ${subsidy_tier} ${facility_type}s on Google Maps`;

  return (
    <div style={{
      marginTop: '12px',
      marginBottom: '12px',
      padding: '16px',
      borderRadius: '12px',
      background: 'var(--surface-muted)',
      border: '1px solid var(--border)',
      color: 'var(--text)',
      boxShadow: 'var(--shadow)'
    }}>
      <div style={{
        display: 'flex',
        justify: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '8px',
        marginBottom: '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '1.3rem' }}>📍</span>
          <div>
            <div style={{ fontWeight: '700', fontSize: '0.95rem', color: 'var(--text)' }}>Singapore Care Routing</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Matched to Subsidy Tier: <strong style={{ color: 'var(--text)' }}>{subsidy_tier}</strong></div>
          </div>
        </div>
        <span style={{
          padding: '4px 8px',
          borderRadius: '8px',
          fontSize: '0.7rem',
          fontWeight: '700',
          backgroundColor: '#2563eb',
          color: 'white'
        }}>
          {facility_type}
        </span>
      </div>

      <a
        href={mapUrl}
        target="_blank"
        rel="noopener noreferrer"
        style={{
          display: 'flex',
          justify: 'center',
          alignItems: 'center',
          gap: '8px',
          width: '100%',
          padding: '10px 16px',
          borderRadius: '8px',
          background: '#2563eb',
          color: 'white',
          fontWeight: '700',
          fontSize: '0.9rem',
          textDecoration: 'none',
          boxSizing: 'border-box',
          transition: 'transform 0.15s ease, background 0.15s ease'
        }}
        onMouseOver={(e) => e.currentTarget.style.background = '#1d4ed8'}
        onMouseOut={(e) => e.currentTarget.style.background = '#2563eb'}
      >
        <span>🗺️</span>
        <span>{buttonLabel}</span>
        <span style={{ fontSize: '0.8rem' }}>↗</span>
      </a>
    </div>
  );
}
