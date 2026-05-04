import { getToken } from "../../utils/auth";
import { Navigate } from "react-router-dom";

function ProtectedRoute({ children }) {
    if (!getToken()) {
        return <Navigate to="/" replace />;
    }
    return children;
}

export default ProtectedRoute;