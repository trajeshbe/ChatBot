import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/router';

interface User {
  id: string;
  username: string;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check authentication status on mount
  useEffect(() => {
    checkAuth();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const checkAuth = () => {
    console.log('checkAuth called, pathname:', router.pathname);
    try {
      const storedToken = localStorage.getItem('access_token');
      const storedUser = localStorage.getItem('user');

      console.log('Stored token exists:', !!storedToken);
      console.log('Stored user exists:', !!storedUser);

      if (storedToken && storedUser) {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
        console.log('Auth restored from localStorage');
      } else {
        console.log('No auth in localStorage');
        // Don't redirect from AuthContext - let individual pages handle redirects
      }
    } catch (error) {
      console.error('Auth check failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (username: string, password: string) => {
    try {
      console.log('AuthContext.login called');
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const loginUrl = `${API_URL}/api/v1/auth/login`;
      console.log('Auth login URL:', loginUrl);

      const response = await fetch(loginUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      console.log('AuthContext login response:', response.status);

      if (!response.ok) {
        const data = await response.json();
        console.error('AuthContext login failed:', data);
        throw new Error(data.detail || 'Login failed');
      }

      const data = await response.json();
      console.log('AuthContext login successful:', data.user);

      // Store authentication data
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));

      setToken(data.access_token);
      setUser(data.user);

      console.log('AuthContext redirecting to /');
      // Redirect to main page
      router.push('/');
    } catch (error) {
      console.error('AuthContext login error:', error);
      throw error;
    }
  };

  const logout = () => {
    // Clear stored data
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);

    // Redirect to login
    router.push('/login');
  };

  const value: AuthContextType = {
    user,
    token,
    isAuthenticated: !!token && !!user,
    isLoading,
    login,
    logout,
    checkAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
