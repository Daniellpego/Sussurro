---
name: Obsidian Pulse
source: Google Stitch project "Sussurro Voice Interface" (id 3417433058416388239)
extracted_at: 2026-06-25
colors:
  surface: '#111317'
  surface-dim: '#111317'
  surface-bright: '#37393e'
  surface-container-lowest: '#0c0e12'
  surface-container-low: '#1a1c20'
  surface-container: '#1e2024'
  surface-container-high: '#282a2e'
  surface-container-highest: '#333539'
  on-surface: '#e2e2e8'
  on-surface-variant: '#c7c4d7'
  inverse-surface: '#e2e2e8'
  inverse-on-surface: '#2f3035'
  outline: '#908fa0'
  outline-variant: '#464554'
  surface-tint: '#c0c1ff'
  primary: '#c0c1ff'
  on-primary: '#1000a9'
  primary-container: '#8083ff'
  on-primary-container: '#0d0096'
  inverse-primary: '#494bd6'
  secondary: '#ffb0cd'
  on-secondary: '#640039'
  secondary-container: '#aa0266'
  on-secondary-container: '#ffbad3'
  tertiary: '#c4c6cf'
  on-tertiary: '#2d3037'
  tertiary-container: '#8e9098'
  on-tertiary-container: '#272a30'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  background: '#111317'
  on-background: '#e2e2e8'
  surface-variant: '#333539'
  brand-bg: '#0B0D11'
  accent-indigo: '#6366F1'
  accent-pink: '#EC4899'
  surface-card: '#14171D'
typography:
  display:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '600'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 22px
    fontWeight: '500'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 26px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
  mono-label:
    fontFamily: Courier Prime
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 12px
  caption:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  xs: 0.25rem
  sm: 0.5rem
  md: 1rem
  lg: 1.5rem
  xl: 2rem
  window_margin: 12px
  gutter: 16px
---

## Brand & Style
The design system is engineered for a premium, local-first utility focused on speed, privacy, and technical excellence. The aesthetic leans heavily into **Glassmorphism** and **Minimalism**, drawing inspiration from modern productivity powerhouses.

The UI should feel like a sophisticated instrument—unobtrusive when idle, but visually striking during interaction. It utilizes a deep, "ink-pool" background strategy to minimize eye strain and maximize the impact of soft indigo-to-pink glows. Layouts are strictly organized, prioritizing functional density and clarity, evoking a sense of calm and control.

## Colors
The palette is rooted in a near-black foundation to provide a high-contrast backdrop for vibrant accents.

- **Foundational Neutrals**: Use `#0B0D11` for the main canvas. Sidebars and secondary panels use subtly lighter shades to create structural separation without harsh lines.
- **Accents**: Indigo (`#6366F1`) and Pink (`#EC4899`) are reserved for active states, brand marks, and primary actions.
- **Borders**: Avoid solid colors. Use the low-opacity white (`0.06`) to create a "glass edge" effect that defines boundaries without adding visual weight.

## Typography
The system uses **Inter** for all interface elements to maintain a clean, systematic look. **Courier Prime** (as a proxy for Cascadia Mono) is used exclusively for technical readouts, keyboard shortcuts, and code-like metadata.

- **Scale**: The hierarchy is tight, ranging from 11px to 36px.
- **Readability**: Large body text (16px/18px) should be used for transcriptions. Labels and utility text use the 11px-13px range to maximize screen real estate.
- **Monospace**: Apply to keycaps and file paths only.

## Layout & Spacing
This design system utilizes a **Fixed Grid** approach for its primary desktop windows, supplemented by a **Fluid Overlay** model for the floating recording bar.

- **Windows**: Use 16px gutters for internal card layouts. Standard sidebars are fixed at 240px width.
- **Margins**: A consistent 12px margin should exist between the window edge and the internal content containers.
- **The Floating Bar**: A specialized layout fixed at 360x64px, anchored to the bottom-center of the screen with a 32px offset from the taskbar.

## Elevation & Depth
Depth is created through **Backdrop Blurs** and **Tonal Layering** rather than traditional drop shadows.

- **Surface Layering**: The background (`#0B0D11`) is the lowest level. Cards and surfaces (`#14171D`) sit above it, defined by their `0.06` white border.
- **The Glow**: High-priority elements (like the active recording state) should emit a soft, 20px Gaussian blur glow using the Indigo/Pink gradient colors at 15% opacity.
- **Glassmorphism**: Floating overlays must use a 92% background opacity with a 12px backdrop blur to ensure legibility against varying desktop wallpapers.

## Shapes
The shape language is sophisticated and soft.
- **Main Containers**: Use a 14px radius for all windows and primary dashboard cards.
- **Interactive Elements**: Buttons and inputs follow the standard 8px (Level 2) roundedness.
- **Specific Geometry**: The brand mark uses a distinct 22% super-ellipse (squircle). Chips, status indicators, and the floating overlay use a full pill radius for a modern, friendly feel.

## Components

### Brand Mark
A stylized waveform consisting of 5 vertical bars of varying heights. Apply the Indigo-to-Pink gradient across the bars. The background is a `#14171D` squircle with 22% roundedness.

### Keycap
Technical shortcuts are displayed as "Keycaps." Use 12px Monospace text inside a small rectangle with a 1px white border (10% alpha). The background is slightly lighter than the surface.

### Mode Chip
Used for transcription modes (e.g., "Dictation", "Coding"). 10px bold uppercase text. Background is 33% opacity of the assigned mode color (e.g., Emerald for 'Ready').

### Status Pill
- **Ready**: An 8px Emerald dot next to "Ready" text in a pill container.
- **Recording**: An 8px Gradient (Indigo/Pink) dot that pulses gently, indicating active voice capture.

### Floating Overlay
A 360x64px pill. This is the primary interaction point during recording. It uses the 92% alpha background with a 12px blur and a subtle 1px border.

### Custom Checkbox
18x18px with 5px rounded corners. In the unchecked state, it has a subtle border. When checked, the entire box is filled with the Indigo-to-Pink gradient, with a white checkmark icon.

### Buttons
Primary buttons use the Indigo-to-Pink gradient with white text. Secondary buttons are "ghost" style with a 1px border and no fill.
