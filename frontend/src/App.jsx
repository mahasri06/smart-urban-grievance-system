import React, { useState } from 'react'
import Navbar from './components/navbar/Navbar'
import LoginModal from './components/login-modal/LoginModal'
import MapView from './pages/map-view/Map'

export default function App() {
  const [loginOpen, setLoginOpen] = useState(false)

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar onLogin={() => setLoginOpen(true)} />
      <div style={{ flex: 1 }}>
        <MapView />
      </div>
      <LoginModal open={loginOpen} onClose={() => setLoginOpen(false)} />
    </div>
  )
}
