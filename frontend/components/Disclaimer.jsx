import React from 'react';
import { ShieldAlert } from 'lucide-react';

export default function Disclaimer({ message = null }) {
  return (
    <aside className="disclaimer" role="note">
      <ShieldAlert style={{ width: '20px', height: '20px', color: 'var(--text-muted)', flexShrink: 0 }} />
      <span>
        <strong style={{ color: 'var(--text)', fontWeight: 600 }}>Clinical Disclaimer:</strong>{' '}
        {message || (
          <>
            This clinical decision support prototype is for <b>educational and screening purposes only</b>. It does not replace professional medical diagnosis, urgent care, or specialist evaluation.
          </>
        )}
      </span>
    </aside>
  );
}

