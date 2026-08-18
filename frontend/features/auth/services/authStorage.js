const TOKEN_KEY = 'app-auth-token';

export function getToken() {
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch (error) {
    return null;
  }
}

export function setToken(token) {
  try {
    window.localStorage.setItem(TOKEN_KEY, token);
  } catch (error) {
    // Storage unavailable; session will not persist across refreshes.
  }
}

export function clearToken() {
  try {
    window.localStorage.removeItem(TOKEN_KEY);
  } catch (error) {
    // Ignore.
  }
}
