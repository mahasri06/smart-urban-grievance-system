import React from 'react'
import './Navbar.css'

export default function Navbar({ onLogin = () => {} }) {
  return (
    <nav className="app-navbar">
      <div className="nav-left">Smart Urban Grievance</div>
      <div className="nav-right">
        <button className="nav-btn" onClick={onLogin}>Login</button>
      </div>
    </nav>
  )
}
