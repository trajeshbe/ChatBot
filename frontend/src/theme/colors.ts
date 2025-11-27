/**
 * Color Palette Configuration
 * Includes the sage green/teal theme from UI_Theme.png
 */

export type ThemeMode = 'light' | 'dark';

// Sage Green/Teal palette (from UI_Theme.png)
export const sageGreen = {
  50: '#f0f7f4',
  100: '#d9ede3',
  200: '#b3dbc7',
  300: '#85c4a6',
  400: '#5ca885',
  500: '#6b9080',  // Main sage green from image
  600: '#527566',
  700: '#3f5c50',
  800: '#334a42',
  900: '#2b3d37',
  950: '#172320',
};

// Complementary teal palette
export const teal = {
  50: '#f0fdfa',
  100: '#ccfbf1',
  200: '#99f6e4',
  300: '#5eead4',
  400: '#2dd4bf',
  500: '#14b8a6',
  600: '#0d9488',
  700: '#0f766e',
  800: '#115e59',
  900: '#134e4a',
  950: '#042f2e',
};

// Light theme colors
export const lightColors = {
  primary: {
    50: sageGreen[50],
    100: sageGreen[100],
    200: sageGreen[200],
    300: sageGreen[300],
    400: sageGreen[400],
    500: sageGreen[500],  // Main
    600: sageGreen[600],
    700: sageGreen[700],
    800: sageGreen[800],
    900: sageGreen[900],
    950: sageGreen[950],
  },

  secondary: {
    50: teal[50],
    100: teal[100],
    200: teal[200],
    300: teal[300],
    400: teal[400],
    500: teal[500],  // Main
    600: teal[600],
    700: teal[700],
    800: teal[800],
    900: teal[900],
    950: teal[950],
  },

  // Semantic colors
  success: '#10b981',   // Green 500
  warning: '#f59e0b',   // Amber 500
  error: '#ef4444',     // Red 500
  info: '#3b82f6',      // Blue 500

  // Background colors
  background: {
    primary: '#ffffff',
    secondary: '#f9fafb',     // Gray 50
    tertiary: '#f3f4f6',      // Gray 100
    elevated: '#ffffff',
    overlay: 'rgba(0, 0, 0, 0.5)',
  },

  // Text colors
  text: {
    primary: '#111827',        // Gray 900
    secondary: '#6b7280',      // Gray 500
    tertiary: '#9ca3af',       // Gray 400
    disabled: '#d1d5db',       // Gray 300
    inverse: '#ffffff',
    link: sageGreen[600],
    linkHover: sageGreen[700],
  },

  // Border colors
  border: {
    default: '#e5e7eb',        // Gray 200
    light: '#f3f4f6',          // Gray 100
    strong: '#d1d5db',         // Gray 300
    focus: sageGreen[500],
    error: '#ef4444',
  },

  // UI element colors
  ui: {
    hover: sageGreen[50],
    active: sageGreen[100],
    selected: sageGreen[100],
    disabled: '#f9fafb',
    skeleton: '#e5e7eb',
    divider: '#e5e7eb',
  },
};

// Dark theme colors
export const darkColors = {
  primary: {
    50: sageGreen[950],
    100: sageGreen[900],
    200: sageGreen[800],
    300: sageGreen[700],
    400: sageGreen[600],
    500: sageGreen[400],  // Main (lighter in dark mode)
    600: sageGreen[300],
    700: sageGreen[200],
    800: sageGreen[100],
    900: sageGreen[50],
    950: sageGreen[50],
  },

  secondary: {
    50: teal[950],
    100: teal[900],
    200: teal[800],
    300: teal[700],
    400: teal[600],
    500: teal[400],  // Main (lighter in dark mode)
    600: teal[300],
    700: teal[200],
    800: teal[100],
    900: teal[50],
    950: teal[50],
  },

  // Semantic colors (slightly lighter for dark mode)
  success: '#34d399',   // Green 400
  warning: '#fbbf24',   // Amber 400
  error: '#f87171',     // Red 400
  info: '#60a5fa',      // Blue 400

  // Background colors
  background: {
    primary: '#0f172a',       // Slate 900
    secondary: '#1e293b',     // Slate 800
    tertiary: '#334155',      // Slate 700
    elevated: '#1e293b',
    overlay: 'rgba(0, 0, 0, 0.7)',
  },

  // Text colors
  text: {
    primary: '#f8fafc',       // Slate 50
    secondary: '#cbd5e1',     // Slate 300
    tertiary: '#94a3b8',      // Slate 400
    disabled: '#64748b',      // Slate 500
    inverse: '#0f172a',
    link: sageGreen[400],
    linkHover: sageGreen[300],
  },

  // Border colors
  border: {
    default: '#334155',       // Slate 700
    light: '#475569',         // Slate 600
    strong: '#64748b',        // Slate 500
    focus: sageGreen[400],
    error: '#f87171',
  },

  // UI element colors
  ui: {
    hover: '#1e293b',         // Slate 800
    active: '#334155',        // Slate 700
    selected: sageGreen[950],
    disabled: '#1e293b',
    skeleton: '#334155',
    divider: '#334155',
  },
};

export type ColorPalette = typeof lightColors;
