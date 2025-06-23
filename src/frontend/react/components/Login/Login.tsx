import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { apiClient } from '@lib/api';
import type { LoginRequest } from '@types/api';
import './Login.css';

const Login: React.FC = () => {
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const credentials: LoginRequest = {
        username: username.trim(),
        password
      };

      console.log('🔐 Attempting login for user:', credentials.username);

      const response = await apiClient.login(credentials);

      if (response.access_token) {
        console.log('✅ Login successful, token received');
        await login(response.access_token);
      } else {
        throw new Error('No token received from server');
      }
    } catch (err: any) {
      console.error('❌ Login failed:', err);
      
      // Handle different error types
      if (err.error) {
        setError(err.error);
      } else if (err.message) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred during authentication');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <div className="login-header">
          <h1>OrdnungsHub</h1>
          <p>Sign in to your account</p>
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
            {isLoading ? 'Loading...' : 'Sign In'}
          </button>
        </form>

        <div className="login-footer">
          <p className="demo-accounts">
            <strong>Demo Accounts:</strong><br />
            Admin: admin / admin123<br />
            User: user / user123
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;