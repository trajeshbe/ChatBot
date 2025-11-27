# Theme System - Quick Start Guide

## 🚀 5-Minute Setup

### 1. Already Integrated! ✅

The theme system is already set up in `_app.tsx`. You're ready to use it!

### 2. Add Theme Toggle to Your Page

```tsx
import { ThemeToggle } from '@/theme/ThemeToggle';

export default function MyPage() {
  return (
    <div>
      <header className="flex justify-between p-4">
        <h1>My App</h1>
        <ThemeToggle showLabel />
      </header>
      {/* Your content */}
    </div>
  );
}
```

### 3. Use Theme in Components

**Option A: Tailwind Classes (Recommended)**

```tsx
<div className="bg-white dark:bg-slate-900">
  <h1 className="text-gray-900 dark:text-white">Hello</h1>
  <button className="bg-primary-500 hover:bg-primary-600 text-white">
    Click Me
  </button>
</div>
```

**Option B: Theme Hooks**

```tsx
import { useColors } from '@/theme/ThemeProvider';

function MyComponent() {
  const colors = useColors();

  return (
    <div style={{ backgroundColor: colors.background.primary }}>
      <h1 style={{ color: colors.text.primary }}>Hello</h1>
    </div>
  );
}
```

## 📚 Common Patterns

### Background Colors

```html
<!-- Page backgrounds -->
<div className="bg-white dark:bg-slate-900">
<div className="bg-gray-50 dark:bg-slate-800">

<!-- Card backgrounds -->
<div className="bg-white dark:bg-slate-800">

<!-- Hover states -->
<div className="hover:bg-gray-100 dark:hover:bg-slate-700">
```

### Text Colors

```html
<!-- Headings -->
<h1 className="text-gray-900 dark:text-white">

<!-- Body text -->
<p className="text-gray-600 dark:text-slate-400">

<!-- Links -->
<a className="text-primary-600 dark:text-primary-400">
```

### Buttons

```html
<!-- Primary button -->
<button className="bg-primary-500 hover:bg-primary-600 text-white">
  Primary Action
</button>

<!-- Secondary button -->
<button className="bg-secondary-500 hover:bg-secondary-600 text-white">
  Secondary Action
</button>

<!-- Outline button -->
<button className="border border-gray-300 dark:border-slate-600 text-gray-700 dark:text-slate-300">
  Outline
</button>
```

### Borders

```html
<div className="border border-gray-200 dark:border-slate-700">
<input className="focus:border-primary-500 dark:focus:border-primary-400">
```

## 🎨 Color Reference

### Primary (Sage Green)

- `primary-50` to `primary-950`
- Main: `primary-500` (#6b9080)
- Use for: Buttons, links, accents

### Secondary (Teal)

- `secondary-50` to `secondary-950`
- Main: `secondary-500` (#14b8a6)
- Use for: Secondary actions, highlights

### Semantic

- `green-500` - Success (#10b981)
- `amber-500` - Warning (#f59e0b)
- `red-500` - Error (#ef4444)
- `blue-500` - Info (#3b82f6)

## 🔧 Hooks

```tsx
import { useTheme, useColors } from '@/theme/ThemeProvider';

function MyComponent() {
  const { mode, toggleMode } = useTheme();
  const colors = useColors();

  return (
    <div>
      <p>Current mode: {mode}</p>
      <button onClick={toggleMode}>Toggle</button>
    </div>
  );
}
```

## ✨ Tips

1. **Always add dark mode classes** when styling
2. **Test in both modes** before committing
3. **Use semantic colors** for consistency
4. **Maintain contrast** for accessibility

## 📖 Full Documentation

See `frontend/src/theme/README.md` for complete guide.

## ❓ Need Help?

- Check examples in existing components
- Read the full README
- Review TypeScript types for autocomplete
