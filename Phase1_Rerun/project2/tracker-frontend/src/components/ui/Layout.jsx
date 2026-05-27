import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { LayoutDashboard, LogOut, ReceiptText } from "lucide-react";
import { useState } from "react";
import { removeToken } from "../../utils/auth";
import { Toaster } from "react-hot-toast"


function Layout() {
    const navigate = useNavigate();
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

    function handleLogout() {
        removeToken();
        navigate('/');
    }

    function toggleSidebar() {
        setSidebarCollapsed(prev => !prev);
    }

    return (
        <div className={`app-shell ${sidebarCollapsed ? "sidebar-collapsed" : ""}`}>
            <Toaster
                position="top-right"
                toastOptions={{
                    duration: 3000,
                    style: {
                        background: '#1e293b',
                        color: '#f8fafc',
                        borderRadius: '8px',
                        fontSize: '14px',
                    },
                    success: {
                        iconTheme: { primary: '#10b981', secondary: '#f8fafc' }
                    },
                    error: {
                        iconTheme: { primary: '#ef4444', secondary: '#f8fafc' }
                    }
                }}
            />
            <aside className="sidebar">
                <div className="sidebar-brand">
                    <div className="brand-mark">F</div>
                    <div className="sidebar-brand-text">
                        <strong>Finance</strong>
                        <span>Tracker</span>
                    </div>
                </div>
                <nav className="sidebar-nav">
                    <NavLink
                        to="/dashboard"
                        className={({ isActive }) => isActive ? "sidebar-link active" : "sidebar-link"}
                        aria-label="Dashboard"
                        title="Dashboard"
                    >
                        <LayoutDashboard size={18} aria-hidden="true" />
                        <span>Dashboard</span>
                    </NavLink>
                    <NavLink
                        to="/transactions"
                        className={({ isActive }) => isActive ? "sidebar-link active" : "sidebar-link"}
                        aria-label="Transactions"
                        title="Transactions"
                    >
                        <ReceiptText size={18} aria-hidden="true" />
                        <span>Transactions</span>
                    </NavLink>
                </nav>
                <button className="logout-btn" onClick={handleLogout} aria-label="Logout" title="Logout">
                    <LogOut size={18} aria-hidden="true" />
                    <span>Logout</span>
                </button>
            </aside>
            <main className="main-content">

                <Outlet context={{ sidebarCollapsed, toggleSidebar }} />
            </main>
        </div>
    );
}
export default Layout;
