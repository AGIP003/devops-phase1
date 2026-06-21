import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, Link } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import api from '../../services/api';
import { saveToken } from '../../utils/auth';

function Register() {
  const { register, handleSubmit, formState: { errors, isSubmitting }, watch, setError } = useForm({
    mode: 'onChange',
  });
  const navigate = useNavigate();
  const [serverError, setServerError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const password = watch('password');

  useEffect(() => {
    document.body.classList.add('auth-screen');
    return () => document.body.classList.remove('auth-screen');
  }, []);

  const onSubmit = async (data) => {
    setServerError('');
    try {
      const response = await api.post('/auth/register', {
        username: data.name,
        email: data.email,
        password: data.password,
      });
      if (!response.data || !response.data.token) {
        throw new Error('Invalid server response: missing token');
      }
      saveToken(response.data.token);
      navigate('/dashboard'); // or wherever your dashboard route is
    } catch (err) {
      const message = err.message || 'Registration failed';

      if (message.toLowerCase().includes('email')) {
        setError('email', { type: 'manual', message: 'Email already registered' });
      } else {
        setServerError(message);
      }
    }
  };

  return (
    <div className="auth-page">
      <form className="auth-form" onSubmit={handleSubmit(onSubmit)}>
        <div className="auth-brand">
          <div className="brand-mark">F</div>
          <div>
            <strong>Finance</strong>
            <span>Tracker</span>
          </div>
        </div>

        <div className="auth-heading">
          <h2>Create account</h2>
          <p>Start tracking your money with the same dashboard view.</p>
        </div>

        {serverError && <div className="auth-message auth-message-error">{serverError}</div>}

        <div className="form-field">
          <label htmlFor="register-name">Full name</label>
          <input
            id="register-name"
            type="text"
            {...register('name', { required: 'Name is required' })}
          />
          {errors.name && <span className="error">{errors.name.message}</span>}
        </div>

        <div className="form-field">
          <label htmlFor="register-email">Email</label>
          <input
            id="register-email"
            type="email"
            {...register('email', {
              required: 'Email is required',
              pattern: {
                value: /^\S+@\S+$/i,
                message: 'Invalid email address',
              },
            })}
          />
          {errors.email && <span className="error">{errors.email.message}</span>}
        </div>

        <div className="form-field">
          <label htmlFor="register-password">Password</label>
          <div className="password-input-wrap">
            <input
              id="register-password"
              type={showPassword ? 'text' : 'password'}
              {...register('password', {
                required: 'Password is required',
                minLength: {
                  value: 8,
                  message: 'Password must be at least 8 characters',
                },
                validate: {
                  hasNumber: value => /\d/.test(value) || 'Password must contain at least one number',
                  hasUppercase: value => /[A-Z]/.test(value) || 'Password must contain at least one uppercase letter',
                  hasLowercase: value => /[a-z]/.test(value) || 'Password must contain at least one lowercase letter',
                },
              })}
            />
            <button
              aria-label={showPassword ? 'Hide password' : 'Show password'}
              className="password-toggle"
              type="button"
              onClick={() => setShowPassword((current) => !current)}
              disabled={isSubmitting}
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
          {errors.password && <span className="error">{errors.password.message}</span>}
        </div>

        <div className="form-field">
          <label htmlFor="register-confirm-password">Confirm password</label>
          <div className="password-input-wrap">
            <input
              id="register-confirm-password"
              type={showConfirmPassword ? 'text' : 'password'}
              {...register('confirmPassword', {
                required: 'Please confirm your password',
                validate: value => value === password || 'Passwords do not match',
              })}
            />
            <button
              aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
              className="password-toggle"
              type="button"
              onClick={() => setShowConfirmPassword((current) => !current)}
              disabled={isSubmitting}
            >
              {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
          {errors.confirmPassword && <span className="error">{errors.confirmPassword.message}</span>}
        </div>

        <button className="auth-submit" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Registering...' : 'Register'}
        </button>

        <p className="auth-switch">
          Already have an account? <Link to="/">Sign in</Link>
        </p>
      </form>
    </div>
  );
}

export default Register;
