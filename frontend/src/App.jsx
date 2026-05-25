import { useState } from 'react';
import MapView from './pages/map-view/Map';
import DashboardView from './pages/dashboard-view/DashBoard';
import Navbar from './components/navbar/Navbar';
import LoginModal from './components/login-modal/LoginModal';

function App() {
  const [view, setView] = useState('map');
  const [isLoginOpen, setIsLoginOpen] = useState(false);

  return (
    <>
      <Navbar setView={setView} view={view} setIsLoginOpen={setIsLoginOpen} />

      {view === 'map' && <MapView />}
      {view === 'dashboard' && <DashboardView />}

      {isLoginOpen && (
        <LoginModal
          setIsLoginOpen={setIsLoginOpen}
          setView={setView}
        />
      )}
    </>
  )
}

export default App