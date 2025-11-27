/**
 * Enterprise RAG Chatbot - Unified Theme Configuration
 *
 * This theme provides a consistent design system across the entire application.
 * Based on Material Design 3 and Tailwind CSS principles.
 *
 * @module theme
 */

export interface Theme {
  colors: {
    primary: ColorScale;
    secondary: ColorScale;
    success: string;
    warning: string;
    error: string;
    info: string;
    background: BackgroundColors;
    text: TextColors;
    border: BorderColors;
    ui: UIColors;
  };
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

interface ColorScale {
  50: string;
  100: string;
  200: string;
  300: string;
  400: string;
  500: string;  // Main color
  600: string;
  700: string;
  800: string;
  900: string;
  950: string;
}

interface BackgroundColors {
  primary: string;
  secondary: string;
  tertiary: string;
  elevated: string;
  overlay: string;
}

interface TextColors {
  primary: string;
  secondary: string;
  tertiary: string;
  disabled: string;
  inverse: string;
  link: string;
  linkHover: string;
}

interface BorderColors {
  default: string;
  light: string;
  strong: string;
  focus: string;
  error: string;
}

interface UIColors {
  hover: string;
  active: string;
  selected: string;
  disabled: string;
  skeleton: string;
  divider: string;
}

interface FontSizes {
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
 * Main theme configuration
 *
 * Primary Color: Blue (#2563eb) - Trust, professionalism, technology
 * Secondary Color: Violet (#7c3aed) - Creativity, innovation
 *
 * This theme is designed to work in light mode. Dark mode will be added in future.
 */
export const theme: Theme = {
  colors: {
    // Primary - Blue scale (Material Blue 600 based)
    primary: {
      50: '#eff6ff',
      100: '#dbeafe',
      200: '#bfdbfe',
      300: '#93c5fd',
      400: '#60a5fa',
      500: '#2563eb',  // Main
      600: '#1d4ed8',
      700: '#1e40af',
      800: '#1e3a8a',
      900: '#1e293b',
      950: '#0f172a',
    },

    // Secondary - Violet scale
    secondary: {
      50: '#faf5ff',
      100: '#f3e8ff',
      200: '#e9d5ff',
      300: '#d8b4fe',
      400: '#c084fc',
      500: '#7c3aed',  // Main
      600: '#9333ea',
      700: '#7e22ce',
      800: '#6b21a8',
      900: '#581c87',
      950: '#3b0764',
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
      elevated: '#ffffff',       // For cards, modals
      overlay: 'rgba(0, 0, 0, 0.5)',
    },

    // Text colors
    text: {
      primary: '#111827',        // Gray 900
      secondary: '#6b7280',      // Gray 500
      tertiary: '#9ca3af',       // Gray 400
      disabled: '#d1d5db',       // Gray 300
      inverse: '#ffffff',
      link: '#2563eb',           // Primary 500
      linkHover: '#1d4ed8',      // Primary 600
    },

    // Border colors
    border: {
      default: '#e5e7eb',        // Gray 200
      light: '#f3f4f6',          // Gray 100
      strong: '#d1d5db',         // Gray 300
      focus: '#2563eb',          // Primary 500
      error: '#ef4444',          // Red 500
    },

    // UI element colors
    ui: {
      hover: '#f3f4f6',          // Gray 100
      active: '#e5e7eb',         // Gray 200
      selected: '#dbeafe',       // Primary 100
      disabled: '#f9fafb',       // Gray 50
      skeleton: '#e5e7eb',       // Gray 200
      divider: '#e5e7eb',        // Gray 200
    },
  },

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
 * Export individual theme sections for direct access
 */
export const colors = theme.colors;
export const typography = theme.typography;
export const spacing = theme.spacing;
export const borderRadius = theme.borderRadius;
export const shadows = theme.shadows;
export const transitions = theme.transitions;
export const zIndex = theme.zIndex;

export default theme;
