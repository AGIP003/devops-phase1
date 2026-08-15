import { useEffect, useRef, useState } from 'react';

const GOOGLE_SCRIPT_ID = 'google-identity-services';
const GOOGLE_SCRIPT_URL = 'https://accounts.google.com/gsi/client';

let googleScriptPromise;
let initializedClientId;
let activeCredentialHandler;

function loadGoogleIdentityServices() {
  if (window.google?.accounts?.id) {
    return Promise.resolve(window.google);
  }

  if (googleScriptPromise) return googleScriptPromise;

  googleScriptPromise = new Promise((resolve, reject) => {
    const existingScript = document.getElementById(GOOGLE_SCRIPT_ID);
    const script = existingScript || document.createElement('script');

    function handleLoad() {
      if (window.google?.accounts?.id) {
        resolve(window.google);
      } else {
        googleScriptPromise = undefined;
        reject(new Error('Google sign-in did not initialize'));
      }
    }

    function handleError() {
      googleScriptPromise = undefined;
      reject(new Error('Unable to load Google sign-in'));
    }

    script.addEventListener('load', handleLoad, { once: true });
    script.addEventListener('error', handleError, { once: true });

    if (!existingScript) {
      script.id = GOOGLE_SCRIPT_ID;
      script.src = GOOGLE_SCRIPT_URL;
      script.async = true;
      script.defer = true;
      document.head.appendChild(script);
    }
  });

  return googleScriptPromise;
}

function GoogleSignInButton({
  onCredential,
  disabled = false,
  text = 'continue_with',
  clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID,
}) {
  const buttonRef = useRef(null);
  const handlerRef = useRef(onCredential);
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    handlerRef.current = onCredential;
  }, [onCredential]);

  useEffect(() => {
    let cancelled = false;
    const buttonElement = buttonRef.current;

    if (!clientId) {
      setLoadError('Google sign-in is not configured yet.');
      return undefined;
    }

    activeCredentialHandler = (credential) => {
      handlerRef.current?.(credential);
    };

    loadGoogleIdentityServices()
      .then((google) => {
        if (cancelled || !buttonElement) return;

        if (initializedClientId !== clientId) {
          google.accounts.id.initialize({
            client_id: clientId,
            callback: (response) => {
              if (response?.credential) {
                activeCredentialHandler?.(response.credential);
              }
            },
          });
          initializedClientId = clientId;
        }

        buttonElement.replaceChildren();
        google.accounts.id.renderButton(buttonElement, {
          theme: 'outline',
          size: 'large',
          shape: 'pill',
          text,
          logo_alignment: 'left',
          width: 360,
        });
      })
      .catch((error) => {
        if (!cancelled) setLoadError(error.message);
      });

    return () => {
      cancelled = true;
      if (buttonElement) buttonElement.replaceChildren();
    };
  }, [clientId, text]);

  if (loadError) {
    return <p className="google-signin-status" role="status">{loadError}</p>;
  }

  return (
    <div
      className={`google-signin-shell ${disabled ? 'is-disabled' : ''}`}
      aria-busy={disabled}
    >
      <div className="google-signin-button" ref={buttonRef} />
    </div>
  );
}

export default GoogleSignInButton;
