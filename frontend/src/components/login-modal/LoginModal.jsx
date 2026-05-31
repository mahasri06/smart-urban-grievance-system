import React, { useState } from 'react'
import './LoginModal.css'

export default function LoginModal({ open = false, onClose = () => {} }) {
  const [userId, setUserId] = useState('')
  const [accessCode, setAccessCode] = useState('')
  const [error, setError] = useState('')

  if (!open) return null

  const handleOk = () => {
    if (userId === '123' && accessCode === '123') {
      setError('')
      onClose()
      return
    }

    setError('Invalid ID or access code.')
  }

  const handleCancel = () => {
    setUserId('')
    setAccessCode('')
    setError('')
    onClose()
  }

  return (
    <div className="login-modal-backdrop" onClick={handleCancel}>
      <div className="login-modal-card" onClick={(e) => e.stopPropagation()}>
        <p className="login-modal-text">Enter your ID and access code to continue.</p>

        <div className="login-form">
          <label className="login-label">
            <input
              className="login-input"
              type="text"
              value={userId}
              onChange={(event) => setUserId(event.target.value)}
              placeholder="Enter ID"
            />
          </label>

          <label className="login-label">
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
  )
}
