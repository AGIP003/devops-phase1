import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { BadgePercent, CalendarClock, ClipboardCheck, Coins, FileText, HandCoins, Landmark, LayoutDashboard, LogOut, PiggyBank, ReceiptText } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { removeToken } from "../../utils/auth";
import { Toaster } from "react-hot-toast"
import TelegramLinkPanel, { TelegramIcon } from "./TelegramLinkPanel";
import api from "../../services/api";


function Layout() {
    const navigate = useNavigate();
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [showTelegramPanel, setShowTelegramPanel] = useState(false);
    const [telegramLinked, setTelegramLinked] = useState(false);

    const refreshTelegramStatus = useCallback(async () => {
        try {
            const response = await api.get("/telegram/status");
            setTelegramLinked(Boolean(response.data?.linked));
        } catch {
            setTelegramLinked(false);
        }
    }, []);

    useEffect(() => {
        refreshTelegramStatus();
    }, [refreshTelegramStatus]);

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
                        <span className="sidebar-link-label">Dashboard</span>
                    </NavLink>
                    <NavLink
                        to="/transactions"
                        className={({ isActive }) => isActive ? "sidebar-link active" : "sidebar-link"}
                        aria-label="Transactions"
                        title="Transactions"
                    >
                        <ReceiptText size={18} aria-hidden="true" />
                        <span className="sidebar-link-label">Transactions</span>
                    </NavLink>
                    <NavLink
                        to="/goals"
                        className={({ isActive }) => isActive ? "sidebar-link active" : "sidebar-link"}
                        aria-label="Goals"
                        title="Goals"
                    >
                        <PiggyBank size={18} aria-hidden="true" />
                        <span className="sidebar-link-label">Goals</span>
                    </NavLink>
                    <NavLink
                        to="/debts"
                        className={({ isActive }) => isActive ? "sidebar-link active" : "sidebar-link"}
                        aria-label="Debts"
                        title="Debts"
                    >
                        <Landmark size={18} aria-hidden="true" />
                        <span className="sidebar-link-label">Debts</span>
                    </NavLink>
                    <NavLink
                        to="/bills"
                        className={({ isActive }) => isActive ? "sidebar-link active" : "sidebar-link"}
                        aria-label="Bills"
                        title="Bills"
                    >
                        <CalendarClock size={18} aria-hidden="true" />
                        <span className="sidebar-link-label">Bills</span>
                    </NavLink>
                    <NavLink
                        to="/forex"
                        className={({ isActive }) => isActive ? "sidebar-link active" : "sidebar-link"}
                        aria-label="Forex"
                        title="Forex"
                    >
                        <Coins size={18} aria-hidden="true" />
                        <span className="sidebar-link-label">Forex</span>
                    </NavLink>
                    <NavLink
                        to="/quotations"
                        className={({ isActive }) => isActive ? "sidebar-link active" : "sidebar-link"}
                        aria-label="Quotations"
                        title="Quotations"
                    >
                        <FileText size={18} aria-hidden="true" />
                        <span className="sidebar-link-label">Quotes</span>
                    </NavLink>
                    <NavLink
                        to="/budgets"
                        className={({ isActive }) => isActive ? "sidebar-link active" : "sidebar-link"}
                        aria-label="Budgets"
                        title="Budgets"
                    >
                        <ClipboardCheck size={18} aria-hidden="true" />
                        <span className="sidebar-link-label">Budgets</span>
                    </NavLink>
                    <NavLink
                        to="/chamas"
                        className={({ isActive }) => isActive ? "sidebar-link active" : "sidebar-link"}
                        aria-label="Chamas"
                        title="Chamas"
                    >
                        <HandCoins size={18} aria-hidden="true" />
                        <span className="sidebar-link-label">Chamas</span>
                    </NavLink>
                    <NavLink
                        to="/fees"
                        className={({ isActive }) => isActive ? "sidebar-link active" : "sidebar-link"}
                        aria-label="Fees"
                        title="Fees"
                    >
                        <BadgePercent size={18} aria-hidden="true" />
                        <span className="sidebar-link-label">Fees</span>
                    </NavLink>
                    <button
                        type="button"
                        className={`sidebar-link sidebar-action sidebar-telegram ${telegramLinked ? "is-linked" : "is-unlinked"}`}
                        aria-label="Connect Telegram"
                        title="Connect Telegram"
                        onClick={() => {
                            setShowTelegramPanel(true);
                            refreshTelegramStatus();
                        }}
                    >
                        <span className="sidebar-telegram-icon">
                            <TelegramIcon size={18} />
                            <span className="sidebar-status-dot" aria-hidden="true" />
                        </span>
                        <span className="sidebar-link-label">Telegram</span>
                    </button>
                </nav>
                <button className="logout-btn" onClick={handleLogout} aria-label="Logout" title="Logout">
                    <LogOut size={18} aria-hidden="true" />
                    <span className="sidebar-link-label">Logout</span>
                </button>
            </aside>
            <main className="main-content">

                <Outlet context={{ sidebarCollapsed, toggleSidebar }} />
            </main>
            <TelegramLinkPanel
                open={showTelegramPanel}
                onClose={() => setShowTelegramPanel(false)}
                onStatusChange={setTelegramLinked}
            />
        </div>
    );
}
export default Layout;
