import './App.css'
import LoginForm from './components/auth/LoginForm'
import ProtectedRoute from './components/auth/ProtectedRoute'
import Dashboard from './pages/Dashboard'
import { Route, Routes } from 'react-router-dom'

function App() {
 
    return (
      <Routes>
        <Route path='/' element={<LoginForm />} />
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }/>
      </Routes>
    );
}

export default App
