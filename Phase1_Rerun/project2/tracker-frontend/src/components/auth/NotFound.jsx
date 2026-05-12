import { Link } from 'react-router-dom';

function NotFound() {
    return (
        <div style={{ textAlign: 'center', padding: '4rem'}}>
            <h1>404</h1>
            <p>Page not found</p>
            <Link to="/dashboard">Go to Dashboard</Link>
        </div>
    );
}

export default NotFound;