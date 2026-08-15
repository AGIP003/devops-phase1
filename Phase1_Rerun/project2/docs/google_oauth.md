# Google sign-in: architecture, configuration, and verification

## What this implementation does

MoneyTiq uses Google as an identity provider, but MoneyTiq still owns its application session.

1. Google Identity Services renders the official button in the browser.
2. Google returns a short-lived signed ID credential to the browser callback.
3. The frontend sends that credential to `POST /api/auth/google`.
4. The backend verifies the credential with Google's official `google-auth` library and checks the intended Google client ID.
5. MoneyTiq identifies the external account by Google's stable `sub` claim, not by email.
6. MoneyTiq creates or loads the local user and returns a MoneyTiq access token.
7. The frontend stores the token and the safe user summary. The summary is presentation data only; the backend remains the authorization authority.

The browser never receives a Google client secret, and MoneyTiq never accepts a client-provided user ID as proof of identity.

## Required configuration

Create one Google OAuth 2.0 **Web application** client in Google Cloud Console. Add each frontend address as an authorized JavaScript origin, for example:

- `http://localhost:5173`
- the deployed frontend origin, such as `https://your-frontend.example`

Use the same Web client ID in both environments:

```dotenv
# Flask / Railway
GOOGLE_CLIENT_ID=example.apps.googleusercontent.com

# Vite frontend
VITE_GOOGLE_CLIENT_ID=example.apps.googleusercontent.com
```

The frontend also needs its API base URL:

```dotenv
VITE_API_URL=http://127.0.0.1:5000/api
```

Vite embeds `VITE_*` values at build time. Changing a deployed frontend variable therefore requires a frontend rebuild. Never place secrets in a `VITE_*` variable.

## Account-linking policy

MoneyTiq does not automatically merge a Google login into an existing password account merely because the emails match. Email is an attribute; the provider and stable provider subject form the external identity.

An existing password user must authenticate to MoneyTiq recently and then call the protected linking endpoint. This prevents an untrusted identity assertion from silently taking over an existing account.

## Profile behavior in this slice

Login and registration store the backend's safe user summary so the dashboard can display the name and email without decoding private database identifiers from the JWT.

The profile menu persists display-name changes through the authenticated
`PATCH /api/auth/profile` endpoint. The route derives the user from the
validated MoneyTiq token and never accepts a client-selected user ID. After a
successful response, the frontend refreshes its cached user summary so the
new name appears immediately and remains consistent across devices.

## Automated verification

Backend tests use the real isolated PostgreSQL test database and mock only Google's network boundary:

```bash
./venv/bin/python -m pytest
```

The OAuth coverage includes:

- Google claim validation and verified-email enforcement
- provider-network failure mapping
- new OAuth user creation
- idempotent repeat login
- prevention of unsafe email auto-linking
- explicit linking with recent authentication
- uniqueness constraints and rollback recovery
- existing transaction and Telegram regression paths

Frontend verification:

```bash
cd tracker-frontend
npm test -- --run
npm run lint
npm run build
```

Component tests cover password login, Google credential exchange, session
persistence, server-persisted profile editing, and complete sign-out cleanup.

## Primary references

- [Google Identity Services: render the Sign in with Google button](https://developers.google.com/identity/gsi/web/guides/display-button)
- [Google Identity Services JavaScript API reference](https://developers.google.com/identity/gsi/web/reference/js-reference)
- [Google: authenticate with a backend server](https://developers.google.com/identity/sign-in/web/backend-auth)
- [PyJWT usage and NumericDate claims](https://pyjwt.readthedocs.io/en/latest/usage.html)
