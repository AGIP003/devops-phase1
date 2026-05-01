// Authentication token helpers for localStorage

export function saveToken(token) {
    window.localStorage.setItem('token', token)
}

export function getToken() {
    return window.localStorage.getItem('token')
}

export function removeToken() {
    window.localStorage.removeItem('token')
}

export function isAuthenticated() {
    return Boolean(getToken())
}
