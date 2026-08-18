import React, { useState } from 'react';
import { changePassword } from '../services/authApi';

export default function ChangePasswordModal({ onClose }) {
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    if (next.length < 8) {
      setError('New password must be at least 8 characters.');
      return;
    }
    if (next !== confirm) {
      setError('New passwords do not match.');
      return;
    }
    setSubmitting(true);
    try {
      await changePassword(current, next);
      setSuccess(true);
      setTimeout(onClose, 1500);
    } catch (err) {
      setError(err.message || 'Failed to change password.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="diabetes-scope">
      <div className="dia-modal-overlay" role="dialog" aria-modal="true" onClick={onClose}>
        <form
          className="dia-modal"
          style={{ maxWidth: '400px' }}
          onClick={(e) => e.stopPropagation()}
          onSubmit={handleSubmit}
        >
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 'var(--dia-sp-4)' }}>
            <div>
              <p className="dia-eyebrow">Account</p>
              <h3 className="dia-section-title" style={{ marginTop: '6px' }}>Change password</h3>
            </div>
            <button type="button" className="dia-modal-close" onClick={onClose}>
              Close ✕
            </button>
          </div>

          {success ? (
            <p style={{ margin: 0, color: 'var(--risk-low-text, #16a34a)', fontWeight: 600 }}>
              Password updated successfully.
            </p>
          ) : (
            <>
              {error && <div className="dia-error" role="alert">{error}</div>}

              <label style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <span className="dia-muted" style={{ fontWeight: 600 }}>Current password</span>
                <input
                  className="dia-input"
                  type="password"
                  value={current}
                  onChange={(e) => setCurrent(e.target.value)}
                  autoComplete="current-password"
                  required
                />
              </label>

              <label style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <span className="dia-muted" style={{ fontWeight: 600 }}>New password</span>
                <input
                  className="dia-input"
                  type="password"
                  value={next}
                  onChange={(e) => setNext(e.target.value)}
                  autoComplete="new-password"
                  minLength={8}
                  required
                />
              </label>

              <label style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <span className="dia-muted" style={{ fontWeight: 600 }}>Confirm new password</span>
                <input
                  className="dia-input"
                  type="password"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  autoComplete="new-password"
                  minLength={8}
                  required
                />
              </label>

              <button className="dia-btn" type="submit" disabled={submitting}>
                {submitting ? 'Updating…' : 'Update Password'}
              </button>
            </>
          )}
        </form>
      </div>
    </div>
  );
}
