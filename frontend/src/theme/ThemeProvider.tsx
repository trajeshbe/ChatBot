/**
 * Theme Provider Component
 * Provides theme context to all child components and manages theme switching
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Theme, ThemeMode, lightTheme, darkTheme, getTheme } from './index';

interface ThemeContextType {
  theme: Theme;
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
  toggleMode: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface ThemeProviderProps {
  children: ReactNode;
  defaultMode?: ThemeMode;
  storageKey?: string;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  children,
  defaultMode = 'light',
  storageKey = 'chatbot-theme-mode',
}) => {
  // Initialize theme from localStorage or default
  const [mode, setModeState] = useState<ThemeMode>(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(storageKey);
      if (stored === 'light' || stored === 'dark') {
        return stored;
      }
      // Check system preference
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark';
      }
    }
    return defaultMode;
  });

  const [theme, setTheme] = useState<Theme>(getTheme(mode));

  // Update theme when mode changes
  useEffect(() => {
    setTheme(getTheme(mode));

    // Save to localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem(storageKey, mode);
    }

    // Update document root classes for Tailwind dark mode
    if (typeof document !== 'undefined') {
      const root = document.documentElement;
      if (mode === 'dark') {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
    }
  }, [mode, storageKey]);

  // Listen for system theme changes
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      // Only auto-switch if user hasn't manually set a preference
      const stored = localStorage.getItem(storageKey);
      if (!stored) {
        setModeState(e.matches ? 'dark' : 'light');
      }
    };

    // Modern browsers
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
    // Legacy browsers
    else if (mediaQuery.addListener) {
      mediaQuery.addListener(handleChange);
      return () => mediaQuery.removeListener(handleChange);
    }
  }, [storageKey]);

  const setMode = (newMode: ThemeMode) => {
    setModeState(newMode);
  };

  const toggleMode = () => {
    setModeState((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  const value: ThemeContextType = {
    theme,
    mode,
    setMode,
    toggleMode,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

/**
 * Hook to access theme context
 * @throws Error if used outside ThemeProvider
 */
export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

/**
 * Hook to get current theme colors
 */
export const useColors = () => {
  const { theme } = useTheme();
  return theme.colors;
};

/**
 * Hook to get current theme typography
 */
export const useTypography = () => {
  const { theme } = useTheme();
  return theme.typography;
};

/**
 * Hook to get current theme spacing
 */
export const useSpacing = () => {
  const { theme } = useTheme();
  return theme.spacing;
};

export default ThemeProvider;
