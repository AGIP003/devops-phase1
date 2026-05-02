import { getToken } from "../../utils/auth";

function ProtectedRoute({ children }) {
    if (!getToken()) {
        window.location.href = '/';
        return null;
    }
    return children;
}

export default ProtectedRoute;