import { useEffect, useRef, useState } from 'react';
import { Link2, X } from 'lucide-react';

import api from '../../services/api';

function ExistingAccountLinkDialog({ credential, onClose, onLinked }) {
  const emailInputRef = useRef(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [linking, setLinking] = useState(false);

  useEffect(() => {
    emailInputRef.current?.focus();
  }, []);

  async function linkExistingAccount(event) {
    event.preventDefault();

    const cleanEmail = email.trim();
    if (!cleanEmail || !password) {
      setError('Enter your existing MoneyTiq email and password.');
      return;
    }

    setLinking(true);
    setError('');

    try {
      const loginResponse = await api.post('/auth/login', {
        email: cleanEmail,
        password,
      });
      const token = loginResponse.data?.token;

      if (typeof token !== 'string' || !token) {
        throw new Error('MoneyTiq returned an invalid sign-in response.');
      }

      const linkResponse = await api.post(
        '/auth/google/link',
        { credential },
        { headers: { Authorization: `Bearer ${token}` } },
      );

      onLinked({
        token,
        user: linkResponse.data?.user || loginResponse.data?.user,
      });
    } catch (requestError) {
      setPassword('');
      setError(requestError.message || 'Unable to link this Google account.');
    } finally {
      setLinking(false);
    }
  }

  return (
    <div className="profile-dialog-backdrop" role="presentation">
      <section
        className="profile-dialog account-link-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="account-link-title"
      >
        <div className="profile-dialog-heading">
          <span className="profile-dialog-icon" aria-hidden="true">
            <Link2 size={20} />
          </span>
          <div>
            <h2 id="account-link-title">Link your existing account</h2>
            <p>Confirm the MoneyTiq account you already own.</p>
          </div>
          <button
            type="button"
            className="profile-dialog-close"
            aria-label="Close account linking"
            disabled={linking}
            onClick={onClose}
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={linkExistingAccount}>
          <label htmlFor="account-link-email">MoneyTiq email</label>
          <input
            ref={emailInputRef}
            id="account-link-email"
            type="email"
            autoComplete="email"
            value={email}
            disabled={linking}
            onChange={(event) => {
              setEmail(event.target.value);
              setError('');
            }}
          />

          <label htmlFor="account-link-password">MoneyTiq password</label>
          <input
            id="account-link-password"
            type="password"
            autoComplete="current-password"
            value={password}
            disabled={linking}
            onChange={(event) => {
              setPassword(event.target.value);
              setError('');
            }}
          />

          <p className="account-link-security-note">
            Your password confirms ownership. MoneyTiq never stores the Google
            credential in browser storage.
          </p>

          {error && <p className="profile-dialog-error" role="alert">{error}</p>}

          <div className="profile-dialog-actions">
            <button type="button" disabled={linking} onClick={onClose}>Cancel</button>
            <button type="submit" disabled={linking}>
              {linking ? 'Linking...' : 'Sign in and link'}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

export default ExistingAccountLinkDialog;
