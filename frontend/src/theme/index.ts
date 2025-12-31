/**
 * Enterprise RAG Chatbot - Unified Theme Configuration
 *
 * This theme provides a consistent design system across the entire application.
 * Based on Material Design 3 and Tailwind CSS principles.
 * Features sage green/teal color palette with light and dark mode support.
 *
 * @module theme
 */

import { lightColors, darkColors, ThemeMode, ColorPalette } from './colors';

export type { ThemeMode };

export interface Theme {
  mode: ThemeMode;
  colors: ColorPalette;
  typography: {
    fontFamily: {
      sans: string;
      mono: string;
    };
    fontSize: FontSizes;
    fontWeight: FontWeights;
    lineHeight: LineHeights;
  };
  spacing: Spacing;
  borderRadius: BorderRadius;
  shadows: Shadows;
  transitions: Transitions;
  zIndex: ZIndex;
}

export interface FontSizes {
  xs: string;
  sm: string;
  base: string;
  lg: string;
  xl: string;
  '2xl': string;
  '3xl': string;
  '4xl': string;
}

interface FontWeights {
  normal: number;
  medium: number;
  semibold: number;
  bold: number;
}

interface LineHeights {
  tight: number;
  normal: number;
  relaxed: number;
}

interface Spacing {
  0: string;
  1: string;
  2: string;
  3: string;
  4: string;
  5: string;
  6: string;
  8: string;
  10: string;
  12: string;
  16: string;
  20: string;
  24: string;
  32: string;
  40: string;
  48: string;
  56: string;
  64: string;
}

interface BorderRadius {
  none: string;
  sm: string;
  md: string;
  lg: string;
  xl: string;
  '2xl': string;
  full: string;
}

interface Shadows {
  none: string;
  sm: string;
  md: string;
  lg: string;
  xl: string;
  '2xl': string;
}

interface Transitions {
  fast: string;
  normal: string;
  slow: string;
}

interface ZIndex {
  dropdown: number;
  sticky: number;
  modal: number;
  popover: number;
  toast: number;
  tooltip: number;
}

/**
 * Light theme configuration
 *
 * Primary Color: Sage Green (#6b9080) - Natural, calming, professional
 * Secondary Color: Teal (#14b8a6) - Fresh, modern, trustworthy
 */
export const lightTheme: Theme = {
  mode: 'light',
  colors: lightColors,

  typography: {
    fontFamily: {
      sans: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      mono: '"Fira Code", "JetBrains Mono", Menlo, Monaco, Consolas, "Courier New", monospace',
    },

    fontSize: {
      xs: '0.75rem',      // 12px
      sm: '0.875rem',     // 14px
      base: '1rem',       // 16px
      lg: '1.125rem',     // 18px
      xl: '1.25rem',      // 20px
      '2xl': '1.5rem',    // 24px
      '3xl': '1.875rem',  // 30px
      '4xl': '2.25rem',   // 36px
    },

    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },

    lineHeight: {
      tight: 1.25,
      normal: 1.5,
      relaxed: 1.75,
    },
  },

  spacing: {
    0: '0',
    1: '0.25rem',    // 4px
    2: '0.5rem',     // 8px
    3: '0.75rem',    // 12px
    4: '1rem',       // 16px
    5: '1.25rem',    // 20px
    6: '1.5rem',     // 24px
    8: '2rem',       // 32px
    10: '2.5rem',    // 40px
    12: '3rem',      // 48px
    16: '4rem',      // 64px
    20: '5rem',      // 80px
    24: '6rem',      // 96px
    32: '8rem',      // 128px
    40: '10rem',     // 160px
    48: '12rem',     // 192px
    56: '14rem',     // 224px
    64: '16rem',     // 256px
  },

  borderRadius: {
    none: '0',
    sm: '0.25rem',    // 4px
    md: '0.5rem',     // 8px
    lg: '0.75rem',    // 12px
    xl: '1rem',       // 16px
    '2xl': '1.5rem',  // 24px
    full: '9999px',
  },

  shadows: {
    none: 'none',
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
  },

  transitions: {
    fast: '150ms cubic-bezier(0.4, 0, 0.2, 1)',
    normal: '300ms cubic-bezier(0.4, 0, 0.2, 1)',
    slow: '500ms cubic-bezier(0.4, 0, 0.2, 1)',
  },

  zIndex: {
    dropdown: 1000,
    sticky: 1020,
    modal: 1040,
    popover: 1060,
    toast: 1080,
    tooltip: 1100,
  },
};

/**
 * Helper function to get color with opacity
 * @param color - Hex color code
 * @param opacity - Opacity value between 0 and 1
 * @returns RGBA color string
 */
export function withOpacity(color: string, opacity: number): string {
  // Convert hex to RGB
  const hex = color.replace('#', '');
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);

  return `rgba(${r}, ${g}, ${b}, ${opacity})`;
}

/**
 * Dark theme configuration
 *
 * Same design principles as light theme but optimized for low-light viewing
 */
export const darkTheme: Theme = {
  mode: 'dark',
  colors: darkColors,

  typography: lightTheme.typography,
  spacing: lightTheme.spacing,
  borderRadius: lightTheme.borderRadius,
  shadows: {
    none: 'none',
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.3)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.3)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.5), 0 4px 6px -2px rgba(0, 0, 0, 0.3)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.6), 0 10px 10px -5px rgba(0, 0, 0, 0.4)',
    '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
  },
  transitions: lightTheme.transitions,
  zIndex: lightTheme.zIndex,
};

/**
 * Get theme based on mode
 */
export function getTheme(mode: ThemeMode): Theme {
  return mode === 'light' ? lightTheme : darkTheme;
}

/**
 * Export individual theme sections for direct access (light theme by default)
 */
export const colors = lightTheme.colors;
export const typography = lightTheme.typography;
export const spacing = lightTheme.spacing;
export const borderRadius = lightTheme.borderRadius;
export const shadows = lightTheme.shadows;
export const transitions = lightTheme.transitions;
export const zIndex = lightTheme.zIndex;

// Export the default theme (light)
export const theme = lightTheme;
export default lightTheme;
