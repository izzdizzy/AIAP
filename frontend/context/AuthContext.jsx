import React, { createContext, useContext, useEffect, useState } from 'react';
import { getToken, setToken, clearToken } from '../features/auth/services/authStorage';
import * as authApi from '../features/auth/services/authApi';

const AuthContext = createContext(undefined);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(() => Boolean(getToken()));

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    let cancelled = false;
    authApi
      .fetchMe()
      .then((me) => {
        if (!cancelled) setUser(me);
      })
      .catch(() => {
        if (!cancelled) clearToken();
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function login(email, password) {
    const data = await authApi.login(email, password);
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  }

  async function register(name, email, password) {
    const data = await authApi.register(name, email, password);
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  }

  function logout() {
    clearToken();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
