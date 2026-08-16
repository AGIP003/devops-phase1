import { act, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import GoogleSignInButton from '../GoogleSignInButton';

describe('GoogleSignInButton', () => {
  afterEach(() => {
    delete window.google;
    vi.restoreAllMocks();
  });

  it('uses Google Identity Services and returns only the credential', async () => {
    const onCredential = vi.fn();
    let googleCallback;

    vi.spyOn(Element.prototype, 'getBoundingClientRect').mockReturnValue({
      bottom: 44,
      height: 44,
      left: 0,
      right: 248,
      top: 0,
      width: 248,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    });

    window.google = {
      accounts: {
        id: {
          initialize: vi.fn(({ callback }) => {
            googleCallback = callback;
          }),
          renderButton: vi.fn((container) => {
            const marker = document.createElement('span');
            marker.textContent = 'Google button rendered';
            container.appendChild(marker);
          }),
        },
      },
    };

    render(
      <GoogleSignInButton
        clientId="web-client.apps.googleusercontent.com"
        onCredential={onCredential}
      />,
    );

    expect(await screen.findByText(/google button rendered/i)).toBeInTheDocument();
    expect(window.google.accounts.id.initialize).toHaveBeenCalledWith(
      expect.objectContaining({
        client_id: 'web-client.apps.googleusercontent.com',
        callback: expect.any(Function),
      }),
    );
    expect(window.google.accounts.id.renderButton).toHaveBeenCalledWith(
      expect.any(HTMLElement),
      expect.objectContaining({ width: 248 }),
    );

    act(() => {
      googleCallback({ credential: 'signed-google-id-token' });
    });

    await waitFor(() => {
      expect(onCredential).toHaveBeenCalledWith('signed-google-id-token');
    });
  });

  it('shows progress while MoneyTiq exchanges the Google credential', () => {
    window.google = {
      accounts: {
        id: {
          initialize: vi.fn(),
          renderButton: vi.fn(),
        },
      },
    };

    render(
      <GoogleSignInButton
        clientId="progress-client.apps.googleusercontent.com"
        disabled
        onCredential={vi.fn()}
      />,
    );

    expect(screen.getByRole('status')).toHaveTextContent(/signing you in/i);
  });
});
