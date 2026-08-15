import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import api from '../../services/api';
import ProfileMenu from './ProfileMenu';

vi.mock('../../services/api', () => ({
  default: {
    patch: vi.fn(),
  },
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

const userProfile = {
  id: '28bc1c02-c52d-4ec8-a644-ef4d087ae913',
  username: 'person',
  display_name: 'Person Name',
  email: 'person@example.com',
  role: 'user',
};

function renderMenu(onUserChange = vi.fn()) {
  window.localStorage.setItem('token', 'moneytiq-jwt');
  window.localStorage.setItem('moneytiq_user', JSON.stringify(userProfile));

  render(
    <MemoryRouter>
      <ProfileMenu user={userProfile} onUserChange={onUserChange} />
    </MemoryRouter>,
  );

  return onUserChange;
}

beforeEach(() => {
  vi.clearAllMocks();
  window.localStorage.clear();
});

describe('ProfileMenu', () => {
  it('persists the display name and refreshes the cached profile', async () => {
    const user = userEvent.setup();
    const onUserChange = renderMenu();
    api.patch.mockResolvedValue({
      data: {
        user: {
          ...userProfile,
          display_name: 'Updated Person',
        },
      },
    });

    await user.click(screen.getByRole('button', { name: /open profile menu/i }));
    expect(screen.getByText('person@example.com')).toBeInTheDocument();
    await user.click(screen.getByRole('menuitem', { name: /edit display name/i }));

    expect(screen.queryByText(/saved only in this browser/i)).not.toBeInTheDocument();
    const input = screen.getByLabelText(/display name/i);
    await user.clear(input);
    await user.type(input, 'Updated Person');
    await user.click(screen.getByRole('button', { name: /save name/i }));

    expect(api.patch).toHaveBeenCalledWith('/auth/profile', {
      display_name: 'Updated Person',
    });
    await waitFor(() => {
      expect(JSON.parse(window.localStorage.getItem('moneytiq_user')).display_name).toBe('Updated Person');
      expect(onUserChange).toHaveBeenCalledWith(
        expect.objectContaining({ display_name: 'Updated Person' }),
      );
    });
  });

  it('clears the complete session when signing out', async () => {
    const user = userEvent.setup();
    renderMenu();

    await user.click(screen.getByRole('button', { name: /open profile menu/i }));
    await user.click(screen.getByRole('menuitem', { name: /sign out/i }));

    expect(window.localStorage.getItem('token')).toBeNull();
    expect(window.localStorage.getItem('moneytiq_user')).toBeNull();
    expect(mockNavigate).toHaveBeenCalledWith('/login', { replace: true });
  });
});
