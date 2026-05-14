import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, Link } from 'react-router-dom';
import api from '../../services/api';
import { saveToken } from '../../utils/auth';

function Register() {
  const { register, handleSubmit, formState: { errors, isSubmitting }, watch, setError } = useForm();
  const navigate = useNavigate();
  const [serverError, setServerError] = useState('');

  const password = watch('password');

  const onSubmit = async (data) => {
    setServerError('');
    try {
      const response = await api.post('/auth/register', {
        username: data.name,
        email: data.email,
        password: data.password,
      });
      saveToken(response.data.token);
      navigate('/dashboard'); // or wherever your dashboard route is
    } catch (err) {
      if (err.response?.status === 409) {
        setError('email', { type: 'manual', message: 'Email already registered' });
      } else {
        setServerError(err.response?.data?.message || 'Registration failed');
      }
    }
  };

  return (
    <div className="register-container">
      <form className="register-form" onSubmit={handleSubmit(onSubmit)}>
        <h2>Create account</h2>

        {serverError && <div className="error-message">{serverError}</div>}

        <div className="form-field">
          <label>Full name</label>
          <input
            type="text"
            {...register('name', { required: 'Name is required' })}
          />
          {errors.name && <span className="error">{errors.name.message}</span>}
        </div>

        <div className="form-field">
          <label>Email</label>
          <input
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
          <label>Password</label>
          <input
            type="password"
            {...register('password', {
              required: 'Password is required',
              minLength: {
                value: 8,
                message: 'Password must be at least 8 characters',
              },
            })}
          />
          {errors.password && <span className="error">{errors.password.message}</span>}
        </div>

        <div className="form-field">
          <label>Confirm password</label>
          <input
            type="password"
            {...register('confirmPassword', {
              required: 'Please confirm your password',
              validate: value => value === password || 'Passwords do not match',
            })}
          />
          {errors.confirmPassword && <span className="error">{errors.confirmPassword.message}</span>}
        </div>

        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Registering...' : 'Register'}
        </button>

        <p className="login-link">
          Already have an account? <Link to="/">Sign in</Link>
        </p>
      </form>
    </div>
  );
}

export default Register;