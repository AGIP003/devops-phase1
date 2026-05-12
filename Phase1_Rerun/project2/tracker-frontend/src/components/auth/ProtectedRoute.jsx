import { getToken } from "../../utils/auth";
import { Navigate, useLocation } from "react-router-dom";

function ProtectedRoute({ children }) {
    const token = getToken();
    const location = useLocation();

    if (!token) {
        return <Navigate to="/" state={{ from: location }} replace />;
    }
    return children;
}

export default ProtectedRoute;