import { useEffect, useState } from "react";
import { getToken, saveAuthSession } from "../../utils/auth";
import api from '../../services/api'
import { useNavigate, useLocation } from "react-router-dom";
import { Link } from 'react-router-dom';
import { ArrowRight, Eye, EyeOff, HandCoins } from 'lucide-react';
import GoogleSignInButton from './GoogleSignInButton';
import ExistingAccountLinkDialog from './ExistingAccountLinkDialog';

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
    const [googleLoading, setGoogleLoading] = useState(false);
    const [linkCredential, setLinkCredential] = useState('');

    function completeAuthentication(data) {
        saveAuthSession({ token: data?.token, user: data?.user });
        const from = location.state?.from?.pathname || '/dashboard';
        navigate(from, { replace: true });
    }

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
            completeAuthentication(response.data);
            setSuccessMessage('Login Successful');
        } catch (err) {
            setErrorMessage(err.response?.data?.message || err.message || 'Unable to sign in');
            setFormData((prevFormData) => ({
                ...prevFormData,
                password: ''
            }));

        } finally {
            setLoading(false);
        }
    }

    async function handleGoogleCredential(credential) {
        setGoogleLoading(true);
        setErrorMessage('');
        setSuccessMessage('');

        try {
            const response = await api.post('/auth/google', { credential });
            completeAuthentication(response.data);
        } catch (err) {
            if (err.code === 'account_link_required' || err.status === 409) {
                setLinkCredential(credential);
            } else {
                setErrorMessage(err.message || 'Unable to sign in with Google');
            }
        } finally {
            setGoogleLoading(false);
        }
    }


    return (
        <div className="auth-page">
            <form className="auth-form" onSubmit={handleSubmit}>
                <div className="auth-brand">
                    <div className="brand-mark" aria-hidden="true">
                        <HandCoins size={22} strokeWidth={2.2} />
                    </div>
                    <div>
                        <strong>MoneyTiq</strong>
                    </div>
                </div>

                <div className="auth-heading">
                    <h2>Welcome back</h2>
                    <p>Log in to use your own money entries, or try MoneyTiq first with sample data.</p>
                </div>

                <GoogleSignInButton
                    onCredential={handleGoogleCredential}
                    disabled={loading || googleLoading}
                />

                <div className="auth-divider" aria-hidden="true">
                    <span>or use your email</span>
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
                        disabled={loading || googleLoading}
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
                            disabled={loading || googleLoading}
                        />
                        <button
                            aria-label={showPassword ? 'Hide password' : 'Show password'}
                            className="password-toggle"
                            type="button"
                            onClick={() => setShowPassword((current) => !current)}
                            disabled={loading || googleLoading}
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

                <button className="auth-submit" type="submit" disabled={loading || googleLoading}>
                    {loading ? 'Logging in...' : 'Login'}
                </button>

                <p className="auth-switch">
                    Don&apos;t have an account? <Link to="/register">Sign up</Link>
                </p>

                <Link className="auth-preview-link" to="/demo">
                    Try the preview <ArrowRight size={16} />
                </Link>
            </form>
            {linkCredential && (
                <ExistingAccountLinkDialog
                    credential={linkCredential}
                    onClose={() => setLinkCredential('')}
                    onLinked={completeAuthentication}
                />
            )}
        </div>
    )
}

export default LoginForm;
