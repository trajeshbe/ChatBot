/**
 * Theme Toggle Component
 * Button to switch between light and dark modes
 */

import React from 'react';
import { useTheme } from './ThemeProvider';

interface ThemeToggleProps {
  className?: string;
  showLabel?: boolean;
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({
  className = '',
  showLabel = false,
}) => {
  const { mode, toggleMode } = useTheme();

  return (
    <button
      onClick={toggleMode}
      className={`
        relative inline-flex items-center gap-2
        px-3 py-2 rounded-md
        transition-colors duration-200
        hover:bg-gray-100 dark:hover:bg-gray-700
        focus:outline-none focus:ring-2 focus:ring-offset-2
        focus:ring-blue-500 dark:focus:ring-blue-400
        ${className}
      `}
      aria-label={`Switch to ${mode === 'light' ? 'dark' : 'light'} mode`}
      title={`Switch to ${mode === 'light' ? 'dark' : 'light'} mode`}
    >
      {/* Sun icon for light mode */}
      {mode === 'dark' && (
        <svg
          className="w-5 h-5 text-gray-700 dark:text-gray-300"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
          />
        </svg>
      )}

      {/* Moon icon for dark mode */}
      {mode === 'light' && (
        <svg
          className="w-5 h-5 text-gray-700 dark:text-gray-300"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
          />
        </svg>
      )}

      {showLabel && (
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {mode === 'light' ? 'Dark' : 'Light'}
        </span>
      )}
    </button>
  );
};

/**
 * Alternative toggle with switch design
 */
export const ThemeToggleSwitch: React.FC<ThemeToggleProps> = ({
  className = '',
}) => {
  const { mode, toggleMode } = useTheme();

  return (
    <button
      onClick={toggleMode}
      className={`
        relative inline-flex h-6 w-11 items-center rounded-full
        transition-colors duration-200 ease-in-out
        focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
        ${mode === 'dark' ? 'bg-blue-600' : 'bg-gray-200'}
        ${className}
      `}
      role="switch"
      aria-checked={mode === 'dark'}
      aria-label="Toggle theme"
    >
      <span
        className={`
          inline-block h-4 w-4 transform rounded-full bg-white transition duration-200 ease-in-out
          ${mode === 'dark' ? 'translate-x-6' : 'translate-x-1'}
        `}
      />
    </button>
  );
};

export default ThemeToggle;
