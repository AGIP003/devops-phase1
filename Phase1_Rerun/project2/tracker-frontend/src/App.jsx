import './App.css';
import LoginForm from './components/auth/LoginForm';
import ProtectedRoute from './components/auth/ProtectedRoute';
import { Route, Routes } from 'react-router-dom';
import Layout from './components/ui/Layout';
import NotFound from './components/auth/NotFound';
import { lazy, Suspense} from 'react';
import Transaction from './pages/Transactions';
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Goals = lazy(() => import('./pages/Goals'));
const Debts = lazy(() => import('./pages/Debts'));
const Forex = lazy(() => import('./pages/Forex'));
const Bills = lazy(() => import('./pages/Bills'));
const Quotations = lazy(() => import('./pages/Quotations'));
const Budgets = lazy(() => import('./pages/Budgets'));
const Chamas = lazy(() => import('./pages/Chamas'));
const Fees = lazy(() => import('./pages/Fees'));
import EditTransaction from './components/auth/EditTransaction';
import Register from './components/auth/Register';
import ForgotPassword from './components/auth/ForgotPassword';
import ResetPassword from './components/auth/ResetPassword';
import ErrorBoundary from './components/ui/ErrorBoundary';

function App() {
 
    return (
        <Suspense fallback={<div className="loading-screen">Loading...</div>}>
          <Routes>
             {/* public routes */}
            <Route path='/' element={<LoginForm />} />
            <Route path="/register" element={<Register />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />

             {/* protected routes – all share the same Layout */}
            <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
                
                <Route path="/dashboard" element={<ErrorBoundary><Dashboard /></ErrorBoundary>}/>
                <Route path="/transactions" element={<ErrorBoundary><Transaction /></ErrorBoundary>}/>
                <Route path="/goals" element={<ErrorBoundary><Goals /></ErrorBoundary>}/>
                <Route path="/debts" element={<ErrorBoundary><Debts /></ErrorBoundary>}/>
                <Route path="/bills" element={<ErrorBoundary><Bills /></ErrorBoundary>}/>
                <Route path="/forex" element={<ErrorBoundary><Forex /></ErrorBoundary>}/>
                <Route path="/quotations" element={<ErrorBoundary><Quotations /></ErrorBoundary>}/>
                <Route path="/budgets" element={<ErrorBoundary><Budgets /></ErrorBoundary>}/>
                <Route path="/chamas" element={<ErrorBoundary><Chamas /></ErrorBoundary>}/>
                <Route path="/fees" element={<ErrorBoundary><Fees /></ErrorBoundary>}/>
                <Route path="transactions/edit/:id" element={<ErrorBoundary><EditTransaction /></ErrorBoundary>} />
                
            </Route>

             {/* 404 – catch all unmatched routes */}
             <Route path="*" element={<NotFound />}></Route>
          </Routes>
        </Suspense>
    );    
}

export default App
