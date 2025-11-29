# 🎨 Movie Recommender Color System

## Overview
This document describes the teal-based color system implemented for the Movie Recommender application. The design uses **CSS custom properties** for consistency and easy theming.

---

## Color Palette

### 🌊 Primary Colors (Teal)
The main brand color - used for interactive elements, buttons, and accents.

```css
--color-primary-900: hsl(180, 65%, 25%)  /* Darkest - rarely used */
--color-primary-700: hsl(180, 60%, 35%)  /* Dark hover states */
--color-primary-600: hsl(180, 55%, 42%)  /* Main brand color ⭐ */
--color-primary-500: hsl(180, 50%, 50%)  /* Logo, links */
--color-primary-400: hsl(180, 55%, 60%)  /* Light hover states */
--color-primary-300: hsl(180, 60%, 70%)  /* Very light accents */
```

**Usage:**
- Logo and app name
- Active filter buttons
- Selected states
- Links and interactive elements
- AI chatbot button (closed state)

---

### 🌺 Accent Colors (Coral/Rose)
Warm contrast color for CTAs and important highlights.

```css
--color-accent-600: hsl(350, 70%, 55%)  /* Dark accent */
--color-accent-500: hsl(350, 75%, 60%)  /* Main accent ⭐ */
--color-accent-400: hsl(350, 80%, 65%)  /* Light accent */
```

**Usage:**
- Rating stars
- AI chatbot button (open state)
- Important CTAs
- Notification badges

---

### 🌑 Background Colors
Dark theme backgrounds matching the base `#0d1117`.

```css
--color-bg-primary: #0d1117      /* Main background ⭐ */
--color-bg-secondary: #161b22    /* Cards, elevated surfaces */
--color-bg-tertiary: #1f2428     /* Hover states */
--color-bg-card: #161b22         /* Content cards */
--color-bg-card-hover: #1f2428   /* Card hover state */
--color-bg-elevated: #21262d     /* Header, modals */
```

---

### 🔲 Border Colors

```css
--color-border-primary: #30363d    /* Main borders ⭐ */
--color-border-secondary: #21262d  /* Subtle borders */
--color-border-accent: hsl(180, 55%, 42%)  /* Teal borders */
```

---

### 📝 Text Colors

```css
--color-text-primary: #e6edf3      /* Main text ⭐ */
--color-text-secondary: #8b949e    /* Secondary text */
--color-text-tertiary: #6e7681     /* Muted text */
--color-text-link: hsl(180, 55%, 60%)  /* Links */
```

---

### ✅ Status Colors

```css
--color-success: hsl(140, 60%, 50%)   /* Green - success states */
--color-warning: hsl(45, 90%, 55%)    /* Yellow - warnings */
--color-error: hsl(0, 70%, 60%)       /* Red - errors */
--color-info: hsl(210, 70%, 60%)      /* Blue - info */
```

---

## Component Usage

### Header
- **Background**: `var(--color-bg-elevated)`
- **Border**: `var(--color-border-primary)`
- **Logo/Title**: `var(--color-primary-500)`
- **Search input focus**: `var(--color-primary-500)` border + shadow

### Content Cards
- **Background**: `var(--color-bg-card)`
- **Hover**: `var(--color-bg-card-hover)`
- **Badge**: `var(--color-primary-600)`
- **Rating**: `var(--color-accent-400)`
- **Title hover**: `var(--color-primary-400)`

### Filter Buttons
- **Active**: `var(--color-primary-600)` background
- **Inactive**: `var(--color-bg-card)` background
- **Hover**: `var(--color-bg-card-hover)` background
- **Text (active)**: white
- **Text (inactive)**: `var(--color-text-secondary)`

### AI Chatbot
- **Button (closed)**: `var(--color-primary-600)`
- **Button (open)**: `var(--color-accent-500)`
- **Window background**: `var(--color-bg-secondary)`
- **Border**: `var(--color-border-primary)`
- **Loading spinner**: `var(--color-primary-500)`

---

## Design Principles

### 1. **Subtle & Sophisticated**
- Teal is calming and professional
- Not overly vibrant like typical streaming services
- Coral accents provide warmth without overwhelming

### 2. **Consistent Hierarchy**
- Primary (teal) = main actions and brand
- Accent (coral) = important highlights
- Backgrounds = dark, GitHub-inspired
- Text = clear hierarchy with 3 levels

### 3. **Accessibility**
- High contrast ratios for text
- Clear focus states
- Hover states for all interactive elements

### 4. **Unique Identity**
- Avoids Netflix red, Disney+ blue, Prime Video teal-blue
- Earthy teal + warm coral = unique combination
- Professional yet approachable

---

## Quick Reference

### Most Used Colors
```css
/* Backgrounds */
background: var(--color-bg-primary);      /* #0d1117 */
background: var(--color-bg-card);         /* #161b22 */

/* Interactive Elements */
background: var(--color-primary-600);     /* Teal buttons */
color: var(--color-primary-500);          /* Teal text/icons */

/* Text */
color: var(--color-text-primary);         /* Main text */
color: var(--color-text-secondary);       /* Secondary text */

/* Borders */
border-color: var(--color-border-primary); /* #30363d */

/* Accents */
color: var(--color-accent-500);           /* Coral highlights */
```

---

## Tailwind Equivalents (for reference)

If you need to use Tailwind classes:
- Primary: `teal-600`, `teal-500`, `teal-400`
- Accent: `rose-500`, `rose-400`
- Backgrounds: `slate-950`, `slate-900`, `slate-800`
- Text: `slate-100`, `slate-400`, `slate-500`

---

## Future Enhancements

Consider adding:
- Dark/Light mode toggle (adjust HSL lightness values)
- User-selectable themes
- Gradient overlays for hero sections
- Animated color transitions

---

**Last Updated**: 2025-11-24
**Color System Version**: 1.0
