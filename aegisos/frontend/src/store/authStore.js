import { useState, useEffect, useCallback } from 'react';

let userState = JSON.parse(localStorage.getItem('evolvixos_user') || 'null');
let tokenState = localStorage.getItem('evolvixos_token');
const listeners = new Set();

const notify = () => listeners.forEach(l => l());

export const useAuthStore = () => {
  const [, forceUpdate] = useState({});

  useEffect(() => {
    const listener = () => forceUpdate({});
    listeners.add(listener);
    return () => listeners.delete(listener);
  }, []);

  const login = useCallback((token, userData) => {
    tokenState = token;
    userState = userData;
    localStorage.setItem('evolvixos_token', token);
    localStorage.setItem('evolvixos_user', JSON.stringify(userData));
    notify();
  }, []);

  const logout = useCallback(() => {
    tokenState = null;
    userState = null;
    localStorage.removeItem('evolvixos_token');
    localStorage.removeItem('evolvixos_user');
    notify();
  }, []);

  return { user: userState, token: tokenState, login, logout };
};
