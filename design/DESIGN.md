---
name: Fractal Deep Space
colors:
  surface: '#10141a'
  surface-dim: '#10141a'
  surface-bright: '#353940'
  surface-container-lowest: '#0a0e14'
  surface-container-low: '#181c22'
  surface-container: '#1c2026'
  surface-container-high: '#262a31'
  surface-container-highest: '#31353c'
  on-surface: '#dfe2eb'
  on-surface-variant: '#b9cacb'
  inverse-surface: '#dfe2eb'
  inverse-on-surface: '#2d3137'
  outline: '#849495'
  outline-variant: '#3a494b'
  surface-tint: '#00dbe7'
  primary: '#e1fdff'
  on-primary: '#00363a'
  primary-container: '#00f2ff'
  on-primary-container: '#006a71'
  inverse-primary: '#00696f'
  secondary: '#4edea3'
  on-secondary: '#003824'
  secondary-container: '#00a572'
  on-secondary-container: '#00311f'
  tertiary: '#f9f5ff'
  on-tertiary: '#1000a9'
  tertiary-container: '#d8d7ff'
  on-tertiary-container: '#4a4cd7'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#74f5ff'
  primary-fixed-dim: '#00dbe7'
  on-primary-fixed: '#002022'
  on-primary-fixed-variant: '#004f54'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#e1e0ff'
  tertiary-fixed-dim: '#c0c1ff'
  on-tertiary-fixed: '#07006c'
  on-tertiary-fixed-variant: '#2f2ebe'
  background: '#10141a'
  on-background: '#dfe2eb'
  surface-variant: '#31353c'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.2'
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  mono-label:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: '1.0'
    letterSpacing: 0.05em
  mono-data:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: '1.4'
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  gutter: 24px
  margin-desktop: 48px
  margin-mobile: 16px
  container-max: 1440px
---

## Brand & Style
The design system is engineered for the high-science domain of neuro-digital networking. The brand personality is academic, authoritative, and clinical, yet pulsates with the energy of cutting-edge exploration. It targets a demographic of researchers, neuro-engineers, and AI architects who require high information density without cognitive overload.

The aesthetic follows a **Deep Space Technical** style, a synthesis of **Glassmorphism** and **Minimalist Science-Fiction**. It utilizes high-contrast accents against abyssal backgrounds to represent the clarity of signal against noise. Visual interest is driven by procedural geometry and fractal-inspired line work, suggesting infinite complexity governed by mathematical order.

## Colors
The palette is optimized for low-light research environments, prioritizing eye comfort and signal hierarchy.

- **Background (Neutral):** The primary canvas is a deep navy (#0A0E14), providing a void-like depth that allows UI layers to stack using luminosity rather than just color.
- **Signal (Primary):** Electric cyan (#00F2FF) is reserved for active data streams, interactive elements, and primary focus areas. It should be used with "glow" filters to simulate light-emitting hardware.
- **Stability (Secondary):** A crisp emerald (#10B981) denotes successful neural synchrony, stable connections, and positive system states.
- **Structure (Borders):** Muted slate (#1E293B) defines the skeleton of the UI, providing visible but unobtrusive containment for complex data sets.

## Typography
This design system employs a dual-font strategy to distinguish between narrative content and technical data.

- **Inter:** Used for all structural headings and descriptive body text. It provides a human-centric, highly legible anchor to the complex subject matter.
- **JetBrains Mono:** Utilized for all metrics, coordinates, labels, and code snippets. The monospaced nature reflects the precision of the underlying algorithms and allows for easier comparison of fluctuating numerical values.

All headings should use tighter letter-spacing to maintain a dense, "engineered" look. Labels should be set in uppercase when using the monospaced font to enhance the "instrumentation" feel.

## Layout & Spacing
The layout follows a **Fluid Grid** model based on a 4px baseline rhythm. 

- **Desktop:** A 12-column grid with 24px gutters. Sections are often separated by thin 1px vertical rules rather than wide margins to maximize information density.
- **Mobile:** A 4-column grid with 16px margins. Complex data visualizations should pivot to horizontal scrolling "strips" rather than vertical stacking to preserve the integrity of the fractal charts.
- **Spacing Philosophy:** Use tight padding (8px or 12px) within data cards to simulate laboratory instrumentation. Larger "breathing rooms" (32px+) are reserved only for separating distinct cognitive modules.

## Elevation & Depth
Depth is created through **Luminous Stacking** rather than traditional shadows.

1. **Base Layer:** The deepest navy background.
2. **Surface Layer:** Semi-transparent overlays (Alpha: 0.4) with a 12px backdrop blur (Glassmorphism). 
3. **Stroke:** Every elevated surface must have a 1px solid border in the slate neutral or a low-opacity cyan for active states.
4. **Glow:** Highly critical elements (active nodes or alerts) use a 0px 0px 15px outer glow matching the element's primary color to simulate light refraction within a digital visor.

## Shapes
The shape language is "Technical Soft." While the overall architecture is rectilinear and sharp to reflect mathematical precision, interactive components use a subtle 4px (Soft) radius to prevent the UI from feeling hostile.

Fractal elements should be strictly geometric—triangles, hexagons, and circles—rendered in 0.5pt to 1pt line weights. Avoid heavy or filled shapes; transparency and wireframes are preferred to maintain the "Glassmorphism" aesthetic.

## Components
- **Buttons:** Primary buttons use a cyan ghost style with a subtle fill on hover. Text is always uppercase JetBrains Mono.
- **Data Cards:** Glassmorphic containers with a 1px slate border. Headers include a "timestamp" or "coordinate" label in the top-right corner.
- **Neural Chips:** Small, pill-shaped indicators for status. Use the success green (#10B981) with a soft inner pulse animation to show active signal connectivity.
- **Input Fields:** Bottom-border only or thin outlined fields. On focus, the border glows cyan and the label undergoes a slight "glitch" or "slide" transition.
- **Fractal Dividers:** Instead of solid lines, use dithered patterns or repeating geometric sequences to separate major sections.
- **HUD Overlays:** Fixed position elements for global metrics (CPU/Neural Load) using high-transparency backgrounds and monospace fonts.