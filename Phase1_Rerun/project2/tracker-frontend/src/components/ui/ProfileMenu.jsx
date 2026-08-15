import { useEffect, useRef, useState } from 'react';
import {
  ChevronDown,
  LogOut,
  PencilLine,
  ShieldCheck,
  UserRound,
  X,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import { removeAuthSession, updateCurrentUser } from '../../utils/auth';

function getInitials(name) {
  const words = String(name || 'User')
    .trim()
    .split(/\s+/)
    .filter(Boolean);

  return words.slice(0, 2).map((word) => word[0]).join('').toUpperCase() || 'U';
}

function ProfileMenu({ user, onUserChange }) {
  const navigate = useNavigate();
  const menuRef = useRef(null);
  const nameInputRef = useRef(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [editorOpen, setEditorOpen] = useState(false);
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState('');

  const visibleName = user?.display_name || user?.username || 'Your account';
  const email = user?.email || 'Sign in again to refresh your profile';

  useEffect(() => {
    function handlePointerDown(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setMenuOpen(false);
      }
    }

    function handleKeyDown(event) {
      if (event.key !== 'Escape') return;
      setEditorOpen(false);
      setMenuOpen(false);
    }

    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  useEffect(() => {
    if (editorOpen) nameInputRef.current?.focus();
  }, [editorOpen]);

  function openEditor() {
    setDisplayName(visibleName === 'Your account' ? '' : visibleName);
    setError('');
    setEditorOpen(true);
    setMenuOpen(false);
  }

  function saveDisplayName(event) {
    event.preventDefault();
    const cleanName = displayName.trim();

    if (!cleanName) {
      setError('Enter the name you want MoneyTiq to display.');
      return;
    }

    if (cleanName.length > 100) {
      setError('Display name must be 100 characters or fewer.');
      return;
    }

    const updatedUser = updateCurrentUser({ display_name: cleanName });
    if (!updatedUser) {
      setError('Sign in again before editing your profile.');
      return;
    }

    onUserChange?.(updatedUser);
    setEditorOpen(false);
  }

  function signOut() {
    removeAuthSession();
    navigate('/login', { replace: true });
  }

  return (
    <div className="account-menu-wrap dashboard-profile-menu" ref={menuRef}>
      <button
        type="button"
        className="profile-button"
        aria-label={`Open profile menu for ${visibleName}`}
        aria-haspopup="menu"
        aria-expanded={menuOpen}
        onClick={() => setMenuOpen((current) => !current)}
      >
        <span className="profile-initial" aria-hidden="true">
          {getInitials(visibleName)}
        </span>
        <ChevronDown className="profile-chevron" size={15} aria-hidden="true" />
      </button>

      {menuOpen && (
        <div className="account-menu" role="menu">
          <div className="account-menu-identity">
            <span className="account-menu-avatar" aria-hidden="true">
              {getInitials(visibleName)}
            </span>
            <div>
              <strong>{visibleName}</strong>
              <span>{email}</span>
            </div>
          </div>

          <div className="account-menu-actions">
            <button type="button" role="menuitem" onClick={openEditor}>
              <PencilLine size={17} aria-hidden="true" />
              <span>
                <strong>Edit display name</strong>
                <small>Personalise this device</small>
              </span>
            </button>
            <div className="account-menu-security" aria-label="Account security">
              <ShieldCheck size={17} aria-hidden="true" />
              <span>
                <strong>Secure sign-in</strong>
                <small>Password or Google</small>
              </span>
            </div>
          </div>

          <button className="account-menu-logout" type="button" role="menuitem" onClick={signOut}>
            <LogOut size={17} aria-hidden="true" />
            Sign out
          </button>
        </div>
      )}

      {editorOpen && (
        <div className="profile-dialog-backdrop" role="presentation">
          <section
            className="profile-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="profile-dialog-title"
          >
            <div className="profile-dialog-heading">
              <span className="profile-dialog-icon" aria-hidden="true">
                <UserRound size={20} />
              </span>
              <div>
                <h2 id="profile-dialog-title">Edit your profile</h2>
                <p>Choose how your name appears around MoneyTiq.</p>
              </div>
              <button
                type="button"
                className="profile-dialog-close"
                aria-label="Close profile editor"
                onClick={() => setEditorOpen(false)}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={saveDisplayName}>
              <label htmlFor="profile-display-name">Display name</label>
              <input
                ref={nameInputRef}
                id="profile-display-name"
                value={displayName}
                maxLength={100}
                onChange={(event) => {
                  setDisplayName(event.target.value);
                  setError('');
                }}
              />
              <p className="profile-dialog-note">
                For now, this preference is saved only in this browser. Server-side profile syncing comes next.
              </p>
              {error && <p className="profile-dialog-error" role="alert">{error}</p>}
              <div className="profile-dialog-actions">
                <button type="button" onClick={() => setEditorOpen(false)}>Cancel</button>
                <button type="submit">Save name</button>
              </div>
            </form>
          </section>
        </div>
      )}
    </div>
  );
}

export default ProfileMenu;
