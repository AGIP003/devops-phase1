import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import LoginForm from './components/auth/LoginForm'
import { getToken } from './utils/auth'
import ProtectedRoute from './components/auth/ProtectedRoute'
import Dashboard from './pages/Dashboard'

function App() {
  const [authVersion, setAuthVersion] = useState(0)
  const token = getToken();
  const isLoggedIn = Boolean(getToken())

  function handleLoginSuccess() {
    setAuthVersion(v => v + 1) //forces re-render
  }

  if (isLoggedIn) {
    return (
      <ProtectedRoute>
        <Dashboard />
      </ProtectedRoute>
    )
  }
  return (
    <>
      <div>
        {token && (
          <div
            style={{
              background: '#14532d',
              color: '#dcfce7',
              padding: '12px 16px',
              textAlign: 'center',
              fontWeight: '600',
            }}
          >
            JWT token found in localStorage.
          </div>
        )}

      </div>
      <div>
        <LoginForm onLoginSuccess={handleLoginSuccess} />
      </div>

    </>
  )
}

export default App
