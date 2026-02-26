import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/apiService';
import './LoginPage.css';

function RegisterPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [invitationToken, setInvitationToken] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [invitationValid, setInvitationValid] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleValidateInvitation = async (e) => {
    e.preventDefault();
    if (!invitationToken) {
      setError('Please enter an invitation token');
      return;
    }

    setIsValidating(true);
    setError('');
    try {
      const response = await apiService.validateInvitation(invitationToken);
      setEmail(response.email);
      setInvitationValid(true);
    } catch (err) {
      setError(err.message || 'Invalid or expired invitation token');
      setInvitationValid(false);
    } finally {
      setIsValidating(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    if (!password || !invitationToken) {
      setError('Please fill all fields');
      return;
    }

    setLoading(true);
    setError('');
    try {
      await apiService.registerViaInvitation({
        token: invitationToken,
        password: password
      });
      navigate('/login', { 
        state: { message: 'Registration successful! Please login.' } 
      });
    } catch (err) {
      setError(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-box">
          <h1>🧠 Atlas AI</h1>
          <h2>Register via Invitation</h2>

          {!invitationValid ? (
            <form onSubmit={handleValidateInvitation}>
              <div className="form-group">
                <label htmlFor="token">Invitation Token</label>
                <input
                  type="text"
                  id="token"
                  value={invitationToken}
                  onChange={(e) => setInvitationToken(e.target.value)}
                  placeholder="Paste your invitation token here"
                  required
                />
              </div>

              {error && <div className="error-message">{error}</div>}

              <button 
                type="submit" 
                className="btn-submit"
                disabled={isValidating}
              >
                {isValidating ? '⏳ Validating...' : '✓ Validate Token'}
              </button>

              <p className="info-text">
                💡 Ask your administrator for an invitation token to register
              </p>
            </form>
          ) : (
            <form onSubmit={handleRegister}>
              <div className="form-group">
                <label htmlFor="email">Email</label>
                <input
                  type="email"
                  id="email"
                  value={email}
                  disabled
                  readOnly
                />
              </div>

              <div className="form-group">
                <label htmlFor="password">Password</label>
                <input
                  type="password"
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Create a strong password"
                  required
                />
              </div>

              {error && <div className="error-message">{error}</div>}

              <button 
                type="submit" 
                className="btn-submit"
                disabled={loading}
              >
                {loading ? '⏳ Creating Account...' : '🎉 Create Account'}
              </button>

              <div className="form-divider">or</div>

              <button 
                type="button"
                className="btn-secondary"
                onClick={() => {
                  setInvitationToken('');
                  setEmail('');
                  setInvitationValid(false);
                  setError('');
                }}
              >
                ← Use Different Token
              </button>

              <p className="login-link">
                Already registered? <a href="/login">Login here</a>
              </p>
            </form>
          )}
        </div>

        <div className="login-info">
          <h3>🔐 Secure Registration</h3>
          <ul>
            <li>✅ Invitation-only onboarding</li>
            <li>✅ Admin approval workflow</li>
            <li>✅ Multi-tenant isolation</li>
            <li>✅ Enterprise security</li>
            <li>✅ Role-based access control</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default RegisterPage;
