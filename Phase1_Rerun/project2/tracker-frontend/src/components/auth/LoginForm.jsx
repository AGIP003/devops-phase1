import { useState } from "react";
import { getToken, saveToken } from "../../utils/auth";
import api from '../../services/api'
import { useNavigate, useLocation } from "react-router-dom";
import { useEffect } from "react";
import { Link } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
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
        document.body.classList.add('auth-screen');
        return () => document.body.classList.remove('auth-screen');
    }, []);

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
    const [showPassword, setShowPassword] = useState(false);

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
            setErrorMessage(err.response?.data?.message || err.message);
            setFormData((prevFormData) => ({
                ...prevFormData,
                password: ''
            }));

        } finally {
            setLoading(false);
        }
    }


    return (
        <div className="auth-page">
            <form className="auth-form" onSubmit={handleSubmit}>
                <div className="auth-brand">
                    <div className="brand-mark">F</div>
                    <div>
                        <strong>Finance</strong>
                        <span>Tracker</span>
                    </div>
                </div>

                <div className="auth-heading">
                    <h2>Welcome back</h2>
                    <p>Sign in to view your dashboard.</p>
                </div>

                <div className="form-field">
                    <label htmlFor="login-email">Email</label>
                    <input
                        id="login-email"
                        type="email"
                        name="email"
                        placeholder="Enter your email"
                        value={formData.email}
                        onChange={handleChange}
                        disabled={loading}
                    />
                </div>

                <div className="form-field">
                    <label htmlFor="login-password">Password</label>
                    <div className="password-input-wrap">
                        <input
                            id="login-password"
                            type={showPassword ? 'text' : 'password'}
                            name="password"
                            placeholder="Enter your password"
                            value={formData.password}
                            onChange={handleChange}
                            disabled={loading}
                        />
                        <button
                            aria-label={showPassword ? 'Hide password' : 'Show password'}
                            className="password-toggle"
                            type="button"
                            onClick={() => setShowPassword((current) => !current)}
                            disabled={loading}
                        >
                            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                        </button>
                    </div>
                </div>

                <div className="auth-row">
                    <Link to="/forgot-password">Forgot password?</Link>
                </div>

                {errorMessage && <div className="auth-message auth-message-error">{errorMessage}</div>}
                {successMessage && <div className="auth-message auth-message-success">{successMessage}</div>}

                <button className="auth-submit" type="submit" disabled={loading}>
                    {loading ? 'Logging in...' : 'Login'}
                </button>

                <p className="auth-switch">
                    Don't have an account? <Link to="/register">Sign up</Link>
                </p>
            </form>
        </div>
    )
}

export default LoginForm;
