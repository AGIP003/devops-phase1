import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { removeToken } from "../../utils/auth";


function Layout() {
    const navigate =useNavigate();

    function handleLogout() {
        removeToken();
        navigate('/');
    } 

    return (
        <div className="app-shell">
            <aside className="sidebar">
                <div className="sidebar-brand">
                    <div className="brand-mark">F</div>
                    <div>
                        <strong>Finance</strong>
                        <span>Tracker</span>
                    </div>
                </div>
                <nav className="sidebar-nav">
                    <NavLink 
                        to="/dashboard"
                        className={({ isActive }) => isActive ? "sidebar-link active": "sidebar-link"}
                    >
                        Dashboard
                    </NavLink>
                    <NavLink 
                        to="/transactions"
                        className={({ isActive }) => isActive ? "sidebar-link active": "sidebar-link"}
                    >
                        Transactions
                    </NavLink>
                </nav>
                <button className="logout-btn" onClick={handleLogout}>Logout</button>
            </aside>
            <main className="main-content">
            
                <Outlet />
            </main>
        </div>
    );
}
export default Layout;