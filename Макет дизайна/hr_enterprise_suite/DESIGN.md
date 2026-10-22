---
name: HR Enterprise Suite
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#45474c'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#75777d'
  outline-variant: '#c5c6cd'
  surface-tint: '#545f73'
  primary: '#091426'
  on-primary: '#ffffff'
  primary-container: '#1e293b'
  on-primary-container: '#8590a6'
  inverse-primary: '#bcc7de'
  secondary: '#0051d5'
  on-secondary: '#ffffff'
  secondary-container: '#316bf3'
  on-secondary-container: '#fefcff'
  tertiary: '#201100'
  on-tertiary: '#ffffff'
  tertiary-container: '#3c2300'
  on-tertiary-container: '#c88000'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d8e3fb'
  primary-fixed-dim: '#bcc7de'
  on-primary-fixed: '#111c2d'
  on-primary-fixed-variant: '#3c475a'
  secondary-fixed: '#dbe1ff'
  secondary-fixed-dim: '#b4c5ff'
  on-secondary-fixed: '#00174b'
  on-secondary-fixed-variant: '#003ea8'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb95f'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  display-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.015em
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 22px
    fontWeight: '700'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 26px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 22px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.03em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 0.75rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system establishes a high-performance, precision-engineered visual environment for enterprise HR intelligence, applicant screening, and candidate tracking. Designed to empower HR professionals, talent acquisition leads, and recruitment operations teams, it translates dense analytical workflows into an effortless, friction-free interface.

### Brand Personality
- **Authoritative & Trustworthy:** Anchored in deep slate and crisp typography that convey institutional stability and data integrity.
- **Efficient & Nimble:** Clean structural architecture optimized for rapid scanning, batch evaluations, and focused document verification.
- **Inviting & Human:** Softened by balanced geometric curves, airy canvases, and warm accent micro-moments that prevent administrative fatigue.

### Design Aesthetic
The aesthetic balances **Modern Corporate Precision** with **Subtle Tonal Depth**. Crisp white surfaces float over calm slate-tinted canvas backdrops (`#F8FAFC` and `#F1F5F9`). Depth is achieved through refined single-pixel outlines (`#E2E8F0`) paired with whisper-quiet ambient drop shadows. Interactive states and ecosystem badges utilize deliberate jewel accents—dynamic royal blues for active interactions, warm ambers for review alerts, emeralds for success states, and crimson roses for validation alerts.

## Colors

The color palette provides high contrast for dense data visualization and legibility while maintaining a light, calming environment.

### Core Swatches
- **Primary Canvas & Slate (`#0F172A` / `#1E293B`):** The primary color anchors the interface through high-contrast typography, primary headers, active navigation pills, and critical controls.
- **Brand Accent Royal Blue (`#2563EB` / `#3B82F6`):** The engine of interaction. Used for primary CTAs, active tab underlines, upload drop zone triggers, focused input borders, and primary link text.
- **Star & Attention Amber (`#F59E0B`):** Employed for warning indicators, pending verification states, star ratings, and subtle gradient highlights.
- **Neutral Foundations (`#F8FAFC` background, `#FFFFFF` cards, `#E2E8F0` borders, `#64748B` secondary text):** Guarantees maximum content readability without visual clutter.

### Semantic Status Badges
- **Uploaded / Processing (`#EFF6FF` background, `#2563EB` text, `#BFDBFE` border):** Active candidate intake, uploaded CVs.
- **Pending HR Review (`#FFFBEB` background, `#D97706` text, `#FDE68A` border):** Awaiting human intervention or validation.
- **Ready / Approved (`#ECFDF5` background, `#059669` text, `#A7F3D0` border):** Screened, verified, and complete.
- **Error / Rejected (`#FFF1F2` background, `#E11D48` text, `#FECDD3` border):** Parsing issue, invalid file type, or disqualification.

## Typography

The typography pairs **Plus Jakarta Sans** for headlines and branding with **Inter** for body copy, tabular numbers, and user controls.

- **Plus Jakarta Sans:** Injects approachable, modern authority into headers, module titles (CVHelper, SearchHelper, SuperHR), modal dialogs, and key metric cards.
- **Inter:** Ensures exceptional legibility across dense candidate tables, metadata key-value rows, form labels, and nested verification logs. Tabular figures (`tnum`) must be enabled on numeric table cells to ensure column alignment across financial and candidate metric comparisons.

## Layout & Spacing

The layout is built upon an adaptive 12-column fluid grid system anchored by a maximum desktop container width of 1440px.

### Breakpoints & Layout Adapters
- **Desktop (>= 1280px):** 12-column grid with `24px` (`1.5rem`) gutters and `32px` (`2rem`) outer page margins. Enables persistent split-view experiences (e.g., CV parsing upload and extraction side-by-side with interactive preview panes).
- **Tablet (768px - 1279px):** 8-column layout with `16px` gutters. Split screens collapse into segmented control views or sticky secondary sheets.
- **Mobile (< 768px):** 4-column layout with `12px` (`0.75rem`) gutters and `16px` (`1rem`) outer margins. Full-width cards and touch targets (minimum 44px height).

### Spacing Discipline
Spacing follows an exact 4px/8px modular scale. Spacing tokens govern internal padding and relative gaps:
- `space-xs` (4px): Inner badge paddings and icon-to-label gaps.
- `space-sm` (8px): Stacked field labels, chip lists, and input icon insets.
- `space-md` (16px): Card internal padding on compact tables, button horizontal padding.
- `space-lg` (24px): Standard card container padding and section dividers.
- `space-xl` (40px): Major section separations and hero stage padding.

## Elevation & Depth

This system avoids heavy drop shadows, opting instead for **low-contrast borders combined with ultra-diffused atmospheric shadows**.

### Elevation Scale
1. **Level 0 (Canvas):** `#F8FAFC` base surface without elevation.
2. **Level 1 (Card Default):** `#FFFFFF` surface bounded by a subtle `1px solid #E2E8F0` border and an ambient shadow: `0 1px 3px 0 rgba(15, 23, 42, 0.05), 0 1px 2px -1px rgba(15, 23, 42, 0.03)`.
3. **Level 2 (Hover / Active Cards):** `0 10px 15px -3px rgba(15, 23, 42, 0.06), 0 4px 6px -4px rgba(15, 23, 42, 0.04)`.
4. **Level 3 (Modals / Dropdowns / Command Palettes):** `0 20px 25px -5px rgba(15, 23, 42, 0.08), 0 8px 10px -6px rgba(15, 23, 42, 0.04)`, enclosed with a `1px solid #CBD5E1` outline.

### Glassmorphic Elements
Top sticky headers (with module navigation and global settings) use a frosted backdrop filter (`backdrop-blur-md bg-white/85 border-b border-slate-200/80`) to provide continuous orientation while reading lengthy candidate lists.

## Shapes

The geometric architecture relies on **roundedness level 2**, prioritizing soft, approachable curves that remain orderly in high-density data views.

- **Primary Cards & Modals:** Standardized on `rounded-2xl` (16px / 1rem radius) to present clean containers for document dropzones and preview panes.
- **Form Controls & Buttons:** Standardized on `rounded-lg` (8px / 0.5rem radius) to maintain structural alignment when inputs, select triggers, and action buttons are grouped inline.
- **Pills & Status Badges:** Fully rounded (`rounded-full` / 9999px) for status indicators, counter tags, and avatar rings.
- **Dropzones:** Rounded outer container (`rounded-2xl`) housing an inner dashed border region with `rounded-xl` corners and 1.5px dashed stroke width.

## Components

### Buttons
- **Primary:** Filled `#2563EB`, text `#FFFFFF`, font `label-lg`, hover `#1D4ED8`, active `#1E40AF`. Subtle `0 1px 2px rgba(37, 99, 235, 0.2)` shadow. `rounded-lg`, height 40px (compact 34px in table actions).
- **Secondary / Ghost:** Transparent or white background, border `1px solid #E2E8F0`, text `#1E293B`. Hover background `#F1F5F9`.
- **Destructive:** Border and text `#E11D48`, hover background `#FFF1F2`.

### File Upload & Parsing Zone
- Outer canvas: Card `#FFFFFF`, `rounded-2xl`, border `1px solid #E2E8F0`.
- Inner drop surface: Tinted `#EFF6FF` with `1.5px dashed #93C5FD`, `rounded-xl`, padding `space-xl`.
- Upload trigger: Elevated white pill button with subtle border, centered icon, and bold call-to-action text.
- Drag-active state: Border changes to `#2563EB` with `#DBEAFE` background tint.

### Status Chips & Badges
- Inline items rendered with `height: 24px`, padding `0 10px`, `rounded-full`, and `label-sm` font weight 600.
- Colors follow the semantic definitions (Loaded: Blue, Pending HR: Amber, Ready: Emerald, Error: Rose), always featuring a 1px border matching the accent tint.

### Interactive Form Controls
- **Inputs & Selects:** Height 40px, background `#FFFFFF`, border `1px solid #CBD5E1`, `rounded-lg`, typography `body-md`. Focus ring: `2px solid #2563EB` with `2px` offset.
- **Checkboxes & Radios:** Size 18px, border `#94A3B8`, active state filled `#2563EB` with white check mark. `rounded-md` for checkboxes, `rounded-full` for radios.

### Data Tables
- Header row: Background `#F8FAFC`, uppercase `label-sm`, text `#64748B`, height 40px, border-b `1px solid #E2E8F0`.
- Body rows: Background `#FFFFFF`, height 52px, text `#1E293B`, border-b `1px solid #F1F5F9`. Hover state `#F8FAFC` transition 150ms.
- High-density spacing mode: Row height 40px, cell padding `space-sm` horizontal.

### Top Navigation Suite Bar
- Height: 64px, background `rgba(255, 255, 255, 0.9)`, backdrop blur 12px.
- Left zone: Brand mark (gradient star accent) + Suite Module Switcher (CVHelper, SearchHelper, SuperHR) with active pill indicators (`#1E293B` text and subtle bottom indicator).
- Right zone: Global Search bar, quick upload button, and ghost settings trigger (`rounded-full`, border `#E2E8F0`).