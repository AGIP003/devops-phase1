const TOKEN_KEY = "token";
const USER_KEY = "moneytiq_user";

// Browser storage is a UI convenience, never an authorization source.
// The API still validates the signed token and record ownership on every request.
export function isAuthenticated() {
    return Boolean(getToken());
}

export function saveToken(token) {
    window.localStorage.setItem(TOKEN_KEY, token);
}

export function getToken() {
    return window.localStorage.getItem(TOKEN_KEY);
}

export function saveAuthSession({ token, user }) {
    if (typeof token !== "string" || !token) {
        throw new Error("Invalid authentication response: missing token");
    }

    if (!user || typeof user !== "object" || Array.isArray(user)) {
        throw new Error("Invalid authentication response: missing user");
    }

    saveToken(token);
    window.localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getCurrentUser() {
    const storedUser = window.localStorage.getItem(USER_KEY);
    if (!storedUser) return null;

    try {
        const user = JSON.parse(storedUser);
        return user && typeof user === "object" && !Array.isArray(user)
            ? user
            : null;
    } catch {
        window.localStorage.removeItem(USER_KEY);
        return null;
    }
}

export function updateCurrentUser(changes) {
    const currentUser = getCurrentUser();
    if (!currentUser) return null;

    const updatedUser = { ...currentUser, ...changes };
    window.localStorage.setItem(USER_KEY, JSON.stringify(updatedUser));
    return updatedUser;
}

export function removeToken() {
    window.localStorage.removeItem(TOKEN_KEY);
}

export function removeAuthSession() {
    window.localStorage.removeItem(TOKEN_KEY);
    window.localStorage.removeItem(USER_KEY);
}
