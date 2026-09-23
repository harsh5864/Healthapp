import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { authApi } from '../services/appServices';

const AuthContext = createContext(null);
const savedUser = JSON.parse(localStorage.getItem('health_companion_user') || 'null');

export function AuthProvider({ children }) {
  const [user, setUser] = useState(savedUser);
  const [loading, setLoading] = useState(false);
  const save = useCallback((payload) => { localStorage.setItem('health_companion_token', payload.token); localStorage.setItem('health_companion_user', JSON.stringify(payload.user)); setUser(payload.user); }, []);
  const login = useCallback(async (data) => { setLoading(true); try { const { data: payload } = await authApi.login(data); save(payload); return payload; } finally { setLoading(false); } }, [save]);
  const register = useCallback(async (data) => { setLoading(true); try { const { data: payload } = await authApi.register(data); save(payload); return payload; } finally { setLoading(false); } }, [save]);
  const logout = useCallback(() => { localStorage.removeItem('health_companion_token'); localStorage.removeItem('health_companion_user'); setUser(null); }, []);
  const value = useMemo(() => ({ user, loading, login, register, logout, setUser }), [user, loading, login, register, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() { return useContext(AuthContext); }
