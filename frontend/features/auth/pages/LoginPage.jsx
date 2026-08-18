import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';

export default function LoginPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const redirectTo = searchParams.get('redirect') || '/';

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setError(err.message || 'Login failed. Please try again.');
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
            Welcome back
          </h1>
          <p className="dia-muted" style={{ marginTop: '6px', marginBottom: 0 }}>
            Sign in to view your saved assessments and track your risk over time.
          </p>
        </div>

        {error && <div className="dia-error" role="alert">{error}</div>}

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
            autoComplete="current-password"
            required
          />
        </label>

        <button className="dia-btn" type="submit" disabled={submitting}>
          {submitting ? 'Signing in…' : 'Sign In'}
        </button>

        <p className="dia-muted" style={{ margin: 0, textAlign: 'center' }}>
          No account yet?{' '}
          <Link className="dia-link" to={`/register?redirect=${encodeURIComponent(redirectTo)}`}>
            Create one
          </Link>
        </p>

        <p className="dia-muted" style={{ margin: 0, textAlign: 'center' }}>
          <Link className="dia-link" to="/">Back to overview</Link>
        </p>
      </form>
    </div>
  );
}
