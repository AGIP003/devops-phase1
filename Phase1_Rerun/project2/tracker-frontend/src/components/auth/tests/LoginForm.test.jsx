import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import api from '../../../services/api';
import LoginForm from '../LoginForm';

vi.mock('../../../services/api', () => ({
  default: {
    post: vi.fn(),
  },
}));

vi.mock('../GoogleSignInButton', () => ({
  default: ({ onCredential, disabled }) => (
    <button
      type="button"
      disabled={disabled}
      onClick={() => onCredential('google-id-credential')}
    >
      Continue with Google
    </button>
  ),
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

const authenticatedUser = {
  id: '28bc1c02-c52d-4ec8-a644-ef4d087ae913',
  username: 'person',
  display_name: 'Person Name',
  email: 'person@example.com',
  role: 'user',
};

function renderLogin() {
  return render(
    <MemoryRouter>
      <LoginForm />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  window.localStorage.clear();
});

describe('LoginForm', () => {
  it('renders both password and Google sign-in choices', () => {
    renderLogin();

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /continue with google/i })).toBeInTheDocument();
  });

  it('validates empty password login without calling the API', async () => {
    const user = userEvent.setup();
    renderLogin();

    await user.click(screen.getByRole('button', { name: /login/i }));

    expect(await screen.findByText(/email and password are required/i)).toBeInTheDocument();
    expect(api.post).not.toHaveBeenCalled();
  });

  it('stores the complete session after password login', async () => {
    const user = userEvent.setup();
    api.post.mockResolvedValue({
      data: { token: 'moneytiq-jwt', user: authenticatedUser },
    });
    renderLogin();

    await user.type(screen.getByLabelText(/email/i), 'person@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'StrongPass123!');
    await user.click(screen.getByRole('button', { name: /login/i }));

    expect(api.post).toHaveBeenCalledWith('/auth/login', {
      email: 'person@example.com',
      password: 'StrongPass123!',
    });
    expect(window.localStorage.getItem('token')).toBe('moneytiq-jwt');
    expect(JSON.parse(window.localStorage.getItem('moneytiq_user'))).toEqual(authenticatedUser);
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true });
  });

  it('exchanges a Google credential for a MoneyTiq session', async () => {
    const user = userEvent.setup();
    api.post.mockResolvedValue({
      data: { token: 'google-moneytiq-jwt', user: authenticatedUser },
    });
    renderLogin();

    await user.click(screen.getByRole('button', { name: /continue with google/i }));

    expect(api.post).toHaveBeenCalledWith('/auth/google', {
      credential: 'google-id-credential',
    });
    expect(window.localStorage.getItem('token')).toBe('google-moneytiq-jwt');
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true });
  });

  it('links Google only after the existing MoneyTiq password succeeds', async () => {
    const user = userEvent.setup();
    const linkRequired = Object.assign(
      new Error('Sign in to the existing MoneyTiq account before linking Google.'),
      { code: 'account_link_required', status: 409 },
    );

    api.post
      .mockRejectedValueOnce(linkRequired)
      .mockResolvedValueOnce({
        data: { token: 'fresh-moneytiq-jwt', user: authenticatedUser },
      })
      .mockResolvedValueOnce({
        data: { user: authenticatedUser },
      });
    renderLogin();

    await user.click(screen.getByRole('button', { name: /continue with google/i }));
    expect(await screen.findByRole('dialog', { name: /link your existing account/i })).toBeInTheDocument();

    await user.type(screen.getByLabelText(/moneytiq email/i), 'person@example.com');
    await user.type(screen.getByLabelText(/moneytiq password/i), 'StrongPass123!');
    await user.click(screen.getByRole('button', { name: /sign in and link/i }));

    expect(api.post).toHaveBeenNthCalledWith(2, '/auth/login', {
      email: 'person@example.com',
      password: 'StrongPass123!',
    });
    expect(api.post).toHaveBeenNthCalledWith(
      3,
      '/auth/google/link',
      { credential: 'google-id-credential' },
      { headers: { Authorization: 'Bearer fresh-moneytiq-jwt' } },
    );
    await waitFor(() => {
      expect(window.localStorage.getItem('token')).toBe('fresh-moneytiq-jwt');
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true });
    });
  });

  it('does not link Google when the existing MoneyTiq password fails', async () => {
    const user = userEvent.setup();
    const linkRequired = Object.assign(new Error('Account linking required'), {
      code: 'account_link_required',
      status: 409,
    });

    api.post
      .mockRejectedValueOnce(linkRequired)
      .mockRejectedValueOnce(new Error('Invalid email or password'));
    renderLogin();

    await user.click(screen.getByRole('button', { name: /continue with google/i }));
    await user.type(await screen.findByLabelText(/moneytiq email/i), 'person@example.com');
    await user.type(screen.getByLabelText(/moneytiq password/i), 'wrong-password');
    await user.click(screen.getByRole('button', { name: /sign in and link/i }));

    expect(await screen.findByText(/invalid email or password/i)).toBeInTheDocument();
    expect(api.post).not.toHaveBeenCalledWith(
      '/auth/google/link',
      expect.anything(),
      expect.anything(),
    );
    expect(window.localStorage.getItem('token')).toBeNull();
  });

  it('shows the backend message when authentication fails', async () => {
    const user = userEvent.setup();
    api.post.mockRejectedValue(new Error('Invalid email or password'));
    renderLogin();

    await user.type(screen.getByLabelText(/email/i), 'person@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'wrong-password');
    await user.click(screen.getByRole('button', { name: /login/i }));

    expect(await screen.findByText(/invalid email or password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password$/i)).toHaveValue('');
  });

  it('disables sign-in choices while password login is pending', async () => {
    const user = userEvent.setup();
    api.post.mockReturnValue(new Promise(() => {}));
    renderLogin();

    await user.type(screen.getByLabelText(/email/i), 'person@example.com');
    await user.type(screen.getByLabelText(/^password$/i), 'StrongPass123!');
    await user.click(screen.getByRole('button', { name: /login/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /logging in/i })).toBeDisabled();
      expect(screen.getByRole('button', { name: /continue with google/i })).toBeDisabled();
    });
  });
});
