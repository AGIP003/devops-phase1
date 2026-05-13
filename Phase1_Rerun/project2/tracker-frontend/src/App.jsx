import './App.css';
import LoginForm from './components/auth/LoginForm';
import ProtectedRoute from './components/auth/ProtectedRoute';
import { Route, Routes } from 'react-router-dom';
import Layout from './components/ui/Layout';
import NotFound from './components/auth/NotFound';
import { lazy, Suspense} from 'react';
import Transaction from './pages/Transactions';
const Dashboard = lazy(() => import('./pages/Dashboard'));

function App() {
 
    return (
        <Suspense fallback={<div className="loading-screen">Loading...</div>}>
          <Routes>
             {/* public routes */}
            <Route path='/' element={<LoginForm />} />

             {/* protected routes – all share the same Layout */}
            <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>

                <Route path="/dashboard" element={<Dashboard />}/>
                <Route path="/transactions" element={<Transaction />}/>
            </Route>

             {/* 404 – catch all unmatched routes */}
             <Route path="*" element={<NotFound />}></Route>
          </Routes>
        </Suspense>
    );    
}

export default App
