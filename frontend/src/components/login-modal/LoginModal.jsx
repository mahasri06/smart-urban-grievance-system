import React from 'react'
import './LoginModal.css'

export default function LoginModal({ open = false, onClose = () => {} }) {
  if (!open) return null
  return (
    <div className="login-overlay" onClick={onClose}>
      <div className="login-card" onClick={(e) => e.stopPropagation()}>
        <h3>Sign in</h3>
        <form className="login-form" onSubmit={(e) => e.preventDefault()}>
          <label>
            Email
            <input type="email" name="email" />
          </label>
          <label>
            Password
            <input type="password" name="password" />
          </label>
          <div className="login-actions">
            <button type="submit" className="btn-primary">Sign in</button>
            <button type="button" className="btn-link" onClick={onClose}>Cancel</button>
          </div>
        </form>
      </div>
    </div>
  )
}
import { useState } from 'react';
import './LoginModal.css';

function LoginModal({ setIsLoginOpen, setView }) {
  const [userId, setUserId] = useState('');
  const [accessCode, setAccessCode] = useState('');
  const [error, setError] = useState('');

  const handleOk = () => {
    if (userId === '123' && accessCode === '123') {
      setError('');
      setIsLoginOpen(false);
      setView('dashboard');
      return;
    }

    setError('Invalid ID or access code.');
  };

  const handleCancel = () => {
    setUserId('');
    setAccessCode('');
    setError('');
    setIsLoginOpen(false);
  };

  return (
    <div className="login-modal-backdrop">
      <div className="login-modal-card">
        {/* <h2 className="login-modal-title">Login</h2> */}
        <p className="login-modal-text">Enter your ID and access code to continue.</p>

        <div className="login-form">
          <label className="login-label">
            {/* <span className="login-label-text">ID</span> */}
            <input
              className="login-input"
              type="text"
              value={userId}
              onChange={(event) => setUserId(event.target.value)}
              placeholder="Enter ID"
            />
          </label>

          <label className="login-label">
            {/* <span className="login-label-text">Access Code</span> */}
            <input
              className="login-input"
              type="password"
              value={accessCode}
              onChange={(event) => setAccessCode(event.target.value)}
              placeholder="Enter access code"
            />
          </label>
        </div>

        {error && <p className="login-error">{error}</p>}

        <div className="login-actions">
          <button type="button" className="login-btn primary" onClick={handleOk}>
            OK
          </button>
          <button type="button" className="login-btn secondary" onClick={handleCancel}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

export default LoginModal;
