import { useState } from "react";
import { getToken, saveToken } from "../../utils/auth";
import api from '../../services/api'
import { useNavigate, useLocation } from "react-router-dom";
import { useEffect } from "react";
import { formToJSON } from "axios";
import { Link } from 'react-router-dom';
//useState is a react hook that lets you add a state variable to your component
// inshort useState gives a component memory
//useEffect gives a component the ability to do sth after it appears on screen. runs after  component renders
//The convention is to name state variables like [something, setSomething] using array destructuring.
// initial state value you want the state to be initially. React saves it once and ignores in the next  render
// use state return an array with exactly two values; current state and set function
function LoginForm() {
    const navigate = useNavigate();
    const location = useLocation();
    useEffect(() => {
        if (getToken()) {
            navigate('/dashboard');
        }
    }, [navigate]);
    const [formData, setFormData] = useState({
        email: '',
        password: ''
    });
    const [loading, setLoading] = useState(false);
    const [errorMessage, setErrorMessage] = useState('');
    const [successMessage, setSuccessMessage] = useState('');

    function handleChange(e) {
        const { name, value } = e.target;
        setFormData({
            ...formData,
            [name]: value
        });
    }

    function validateForm() {
        if (!formData.email.trim() || !formData.password.trim()) {
            return 'Email and password are required';
        }
        return '';
    }

    
    async function handleSubmit(e) {
        //Prevent page reload
        e.preventDefault();

        const error = validateForm();
        if (error) {
            setErrorMessage(error);
            return;
        }

        setLoading(true);
        setErrorMessage('');
        setSuccessMessage('');

        try {
            //API call
            const response = await api.post('/auth/login', formData);
            saveToken(response.data.token);
            const from = location.state?.from?.pathname || '/dashboard';
            navigate(from, { replace: true });
            setSuccessMessage('Login Successful');
            console.log(response)
        } catch (err) {
            setErrorMessage(err.message);
            setFormData((prevFormData) => ({
                ...prevFormData,
                password: ''
            }));
            
        } finally {
            setLoading(false);
        }
    }


    return (
        <div>
            <form onSubmit={handleSubmit}>
                <input
                    type="email"
                    name="email"
                    placeholder="email"
                    value={formData.email}
                    onChange={handleChange}
                    disabled={loading}
                />
                <input
                    type="password"
                    name="password"
                    placeholder="password"
                    value={formData.password}
                    onChange={handleChange}
                    disabled={loading}
                />
                {errorMessage && <div style={{ color: 'red', border: '1px solid red', padding: '8px', marginBottom: '10px' }}>{errorMessage}</div>}
                {successMessage && <div style={{ color: 'green', border: '1px solid green', padding: '8px', marginBottom: '10px' }}>{successMessage}</div>}
                <button type="submit" disabled={loading}>
                    {loading ? 'Logging in...' : 'Login'}
                </button>
            </form>
            <p>Don't have an account? <Link to="/register">Sign up</Link></p>
        </div>
    )
}

export default LoginForm;
