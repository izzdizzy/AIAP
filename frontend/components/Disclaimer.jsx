import React from 'react';
import { ShieldAlert } from 'lucide-react';

export default function Disclaimer({ message = null }) {
  return (
    <aside className="disclaimer" role="note">
      <ShieldAlert style={{ width: '20px', height: '20px', color: '#94A3B8', flexShrink: 0 }} />
      <span>
        <strong style={{ color: '#E2E8F0', fontWeight: 600 }}>Clinical Disclaimer:</strong>{' '}
        This clinical decision support prototype is for <b>educational and screening purposes only</b>. It does not replace professional medical diagnosis, urgent care, or specialist evaluation.
      </span>
    </aside>
  );
}

