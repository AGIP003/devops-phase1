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
                <div className="app-name">Finance Tracker</div>
                <nav>
                    <NavLink to="/dashboard">Dashboard</NavLink>
                    <NavLink to="/transactions">Transactions</NavLink>
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