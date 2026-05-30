import { createContext, useContext, useState } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('wf_user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });
  const [token, setToken] = useState(() => localStorage.getItem('wf_token') || null);
  const role = user?.role || null;

  function login(tokenValue, userData) {
    // Normalize: backend returns full_name, frontend uses name
    const normalized = {
      ...userData,
      name: userData.name || userData.full_name || 'User',
    };
    localStorage.setItem('wf_token', tokenValue);
    localStorage.setItem('wf_user', JSON.stringify(normalized));
    setToken(tokenValue);
    setUser(normalized);
  }

  function logout() {
    localStorage.removeItem('wf_token');
    localStorage.removeItem('wf_user');
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, role, token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
