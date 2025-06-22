import React, { useState } from 'react';
import './Login.css';

interface LoginProps {
  onLogin: (token: string) => void;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const endpoint = isLoginMode ? '/auth/login' : '/auth/register';
      const body = isLoginMode
        ? new URLSearchParams({
            username,
            password,
            grant_type: 'password'
          })
        : JSON.stringify({
            username,
            email,
            password
          });

      const headers = isLoginMode
        ? { 'Content-Type': 'application/x-www-form-urlencoded' }
        : { 'Content-Type': 'application/json' };

      let response;
      if ((window as any).electronAPI) {
        response = await (window as any).electronAPI.apiRequest(endpoint, 'POST', body, headers);
      } else {
        const res = await fetch(`http://127.0.0.1:8000${endpoint}`, {
          method: 'POST',
          headers,
          body
        });
        response = await res.json();
        if (!res.ok) {
          throw new Error(response.detail || 'Authentication failed');
        }
      }

      if (response.access_token) {
        onLogin(response.access_token);
      } else {
        throw new Error('No access token received');
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred during authentication');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <div className="login-header">
          <h1>OrdnungsHub</h1>
          <p>{isLoginMode ? 'Sign in to your account' : 'Create a new account'}</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>

          {!isLoginMode && (
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
          )}

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <button type="submit" className="login-button" disabled={isLoading}>
            {isLoading ? 'Loading...' : (isLoginMode ? 'Sign In' : 'Sign Up')}
          </button>
        </form>

        <div className="login-footer">
          <p>
            {isLoginMode ? "Don't have an account? " : "Already have an account? "}
            <button
              type="button"
              onClick={() => {
                setIsLoginMode(!isLoginMode);
                setError('');
              }}
              className="toggle-mode-button"
              disabled={isLoading}
            >
              {isLoginMode ? 'Sign Up' : 'Sign In'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;