import { act, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import GoogleSignInButton from '../GoogleSignInButton';

describe('GoogleSignInButton', () => {
  afterEach(() => {
    delete window.google;
  });

  it('uses Google Identity Services and returns only the credential', async () => {
    const onCredential = vi.fn();
    let googleCallback;

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

    act(() => {
      googleCallback({ credential: 'signed-google-id-token' });
    });

    await waitFor(() => {
      expect(onCredential).toHaveBeenCalledWith('signed-google-id-token');
    });
  });
});
