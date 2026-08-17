import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext(undefined);

const THEME_STORAGE_KEY = 'app-theme';
const DEFAULT_THEME = 'dark';
const VALID_THEMES = ['light', 'dark'];

/**
 * ThemeProvider component that manages global dark/light theme state.
 * - Persists theme to localStorage with key 'app-theme'
 * - Defaults to 'dark' so readmission page shows original design on first load
 * - Applies data-theme attribute to document.documentElement
 * - Falls back safely if localStorage is unavailable or stored value is invalid
 */
export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    // Try to get theme from localStorage
    let storedTheme = null;
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        storedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);
      }
    } catch (e) {
      // localStorage unavailable (private browsing, security settings, etc.)
      console.warn('[ThemeProvider] localStorage unavailable:', e);
    }
    
    // Validate stored theme or use default
    if (storedTheme && VALID_THEMES.includes(storedTheme)) {
      return storedTheme;
    }
    return DEFAULT_THEME;
  });

  // Apply theme to document and persist to localStorage
  useEffect(() => {
    // Apply data-theme attribute to html element
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('data-theme', theme);
    }
    
    // Persist to localStorage with error handling
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem(THEME_STORAGE_KEY, theme);
      }
    } catch (e) {
      console.warn('[ThemeProvider] Could not persist theme to localStorage:', e);
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
  };

  const value = {
    theme,
    setTheme,
    toggleTheme,
    isDark: theme === 'dark',
    isLight: theme === 'light'
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

/**
 * Custom hook to access theme context
 * @returns {{ theme: string, setTheme: Function, toggleTheme: Function, isDark: boolean, isLight: boolean }}
 */
export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

export default ThemeContext;
