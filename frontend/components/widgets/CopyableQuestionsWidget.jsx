import React, { useState } from 'react';

export default function CopyableQuestionsWidget({ data }) {
  if (!data) return null;

  const { title = "Questions for Your Doctor", questions = [] } = data;
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    const textToCopy = `${title}:\n` + questions.map((q, i) => `${i + 1}. ${q}`).join('\n');
    navigator.clipboard.writeText(textToCopy)
      .then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2500);
      })
      .catch((err) => {
        console.error("Failed to copy questions: ", err);
      });
  }

  return (
    <div style={{
      marginTop: '12px',
      marginBottom: '12px',
      padding: '16px',
      borderRadius: '12px',
      background: 'rgba(13, 148, 136, 0.1)',
      border: '1px solid #0d9488',
      color: 'var(--text, #f8fafc)',
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.12)'
    }}>
      <div style={{
        display: 'flex',
        justify: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '10px',
        marginBottom: '10px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '1.2rem' }}>🩺</span>
          <strong style={{ fontSize: '0.95rem', color: '#2dd4bf' }}>{title}</strong>
        </div>
        <button
          onClick={handleCopy}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            borderRadius: '6px',
            background: copied ? '#10b981' : '#0d9488',
            color: 'white',
            border: 'none',
            fontSize: '0.8rem',
            fontWeight: '600',
            cursor: 'pointer',
            transition: 'background 0.2s ease'
          }}
        >
          {copied ? '✓ Copied to Clipboard!' : '📋 Copy Questions'}
        </button>
      </div>

      <ul style={{
        margin: 0,
        paddingLeft: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '6px',
        fontSize: '0.85rem',
        lineHeight: 1.4
      }}>
        {questions.map((q, idx) => (
          <li key={idx} style={{ color: '#e2e8f0' }}>{q}</li>
        ))}
      </ul>
    </div>
  );
}
