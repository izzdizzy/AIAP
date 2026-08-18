import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';

export default function RegisterPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { register } = useAuth();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const redirectTo = searchParams.get('redirect') || '/';

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    if (password !== confirm) {
      setError('Passwords do not match.');
      return;
    }
    setSubmitting(true);
    try {
      await register(name, email, password);
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="diabetes-scope dia-auth-page">
      <form className="dia-auth-card" onSubmit={handleSubmit}>
        <div>
          <p className="dia-eyebrow">Health Assessment Hub</p>
          <h1 className="dia-section-title" style={{ fontSize: '1.5rem', marginTop: '8px' }}>
            Create your account
          </h1>
          <p className="dia-muted" style={{ marginTop: '6px', marginBottom: 0 }}>
            Save every assessment and watch your risk trend over time.
          </p>
        </div>

        {error && <div className="dia-error" role="alert">{error}</div>}

        <label style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <span className="dia-muted" style={{ fontWeight: 600 }}>Name</span>
          <input
            className="dia-input"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            autoComplete="name"
            required
          />
        </label>

        <label style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <span className="dia-muted" style={{ fontWeight: 600 }}>Email</span>
          <input
            className="dia-input"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
          />
        </label>

        <label style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <span className="dia-muted" style={{ fontWeight: 600 }}>Password</span>
          <input
            className="dia-input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
            minLength={8}
            required
          />
        </label>

        <label style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <span className="dia-muted" style={{ fontWeight: 600 }}>Confirm password</span>
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
          {submitting ? 'Creating account…' : 'Create Account'}
        </button>

        <p className="dia-muted" style={{ margin: 0, textAlign: 'center' }}>
          Already have an account?{' '}
          <Link className="dia-link" to={`/login?redirect=${encodeURIComponent(redirectTo)}`}>
            Sign in
          </Link>
        </p>
      </form>
    </div>
  );
}
