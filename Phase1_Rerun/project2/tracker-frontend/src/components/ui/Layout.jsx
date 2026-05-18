import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { LayoutDashboard, LogOut, ReceiptText } from "lucide-react";
import { useState } from "react";
import { removeToken } from "../../utils/auth";


function Layout() {
    const navigate =useNavigate();
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
                        className={({ isActive }) => isActive ? "sidebar-link active": "sidebar-link"}
                        title="Dashboard"
                    >
                        <LayoutDashboard size={18} />
                        <span>Dashboard</span>
                    </NavLink>
                    <NavLink 
                        to="/transactions"
                        className={({ isActive }) => isActive ? "sidebar-link active": "sidebar-link"}
                        title="Transactions"
                    >
                        <ReceiptText size={18} />
                        <span>Transactions</span>
                    </NavLink>
                </nav>
                <button className="logout-btn" onClick={handleLogout} title="Logout">
                    <LogOut size={18} />
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
