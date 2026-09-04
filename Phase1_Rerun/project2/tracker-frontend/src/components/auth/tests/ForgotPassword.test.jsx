import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import api from '../../../services/api';
import ForgotPassword from '../ForgotPassword';


vi.mock('../../../services/api', () => ({
  default: {
    post: vi.fn(),
  },
}));

afterEach(() => {
  vi.unstubAllEnvs();
  vi.clearAllMocks();
});

function renderPage() {
  return render(
    <MemoryRouter>
      <ForgotPassword />
    </MemoryRouter>,
  );
}

describe('ForgotPassword availability', () => {
  it('explains the outage and prevents reset requests while disabled', async () => {
    const user = userEvent.setup();
    renderPage();

    expect(screen.getByRole('status')).toHaveTextContent(
      /reset links are unavailable right now/i,
    );
    expect(screen.getByLabelText(/email/i)).toBeDisabled();

    const submitButton = screen.getByRole('button', {
      name: /send reset link/i,
    });
    expect(submitButton).toBeDisabled();

    await user.click(submitButton);
    expect(api.post).not.toHaveBeenCalled();
  });

  it('keeps the reset form available behind its deployment flag', async () => {
    vi.stubEnv('VITE_PASSWORD_RESET_ENABLED', 'true');
    api.post.mockResolvedValue({
      data: { message: 'A reset link has been sent' },
    });
    const user = userEvent.setup();
    renderPage();

    await user.type(screen.getByLabelText(/email/i), 'person@example.com');
    await user.click(screen.getByRole('button', { name: /send reset link/i }));

    expect(api.post).toHaveBeenCalledWith('/auth/password_reset_request', {
      email: 'person@example.com',
    });
    expect(
      await screen.findByText(/a reset link has been sent/i),
    ).toBeInTheDocument();
  });
});
