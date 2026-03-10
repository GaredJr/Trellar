# Dag 2

### 10.03.2026

Jeg startet dagen med å først lære meg flask fullstendig, så det jeg kommer til å få KI til å gjøre for meg senere, ikke blir noe jeg ikke kunne gjort selv. Så sketchet et simpelt design for sidene. Dette er ikke det ferdige designet, men heller bare referansematerial.
Så lagde jeg en prompt for css designet med codex.

```
Create a single production-ready `/static/style.css` for a Trello-style app with a **clean VS Code-inspired dark UI** that feels intentional and handcrafted, not generic.

Project context:
- Stack: Flask + server-rendered HTML templates.
- CSS target: `/static/style.css`
- Dark mode is default.
- Use fonts from `/static/fonts` via `@font-face` with `font-display: swap`:
  - `Lemon Milk Pro Ultra Light.woff2` (300)
  - `Lemon Milk Pro Regular.woff2` (400)
  - `Lemon Milk Pro Medium.woff2` (500)
  - `Lemon Milk Pro Bold.woff2` (700)
  - Include matching italic files.
- Use these selectors so styles are reusable across pages:
  `.app`, `.topbar`, `.brand`, `.topnav`, `.page`, `.container`, `.footer`,
  `.board-shell`, `.board-header`, `.board-title`, `.board-actions`,
  `.lanes`, `.lane`, `.lane-head`, `.lane-title`, `.lane-count`, `.lane-foot`,
  `.card-list`, `.card`, `.card-title`, `.card-meta`,
  `.button`, `.button-primary`, `.button-ghost`,
  `.input`, `.textarea`, `.panel`, `.tag`, `.avatar`.

Aesthetic direction (anti-AI-slop constraints):
- Visual language should be disciplined and product-like, not “template-y”.
- No glassmorphism, no neon glow, no giant soft blobs, no overdone gradients.
- No purple-heavy palettes.
- Keep radii consistent and restrained (small/medium only).
- Use a tight spacing system and clear hierarchy; avoid random spacing.
- Use subtle depth and contrast like VS Code Dark+, not flashy effects.
- Motion should be minimal and purposeful only.

Color and tone:
- Define all design tokens in `:root` (colors, spacing, radii, shadows, typography, z-index).
- Use a VS Code-like palette family:
  - app background near `#1e1e1e`
  - elevated surfaces near `#252526`/`#2d2d30`
  - borders near `#3e3e42`
  - primary text near `#d4d4d4`
  - muted text near `#9da3ad`
  - accent blues in the `#0e639c` to `#3794ff` family
- Include `color-scheme: dark`.

Typography:
- Use Lemon Milk Pro from `/static/fonts`.
- Keep typography readable and professional:
  - headings/labels can be stronger weights
  - body/copy should prioritize legibility (size, line-height, letter-spacing)
- Build a clear type scale with CSS variables.

Layout and components:
- Include a modern reset/base (`box-sizing`, media defaults, form inheritance, button reset, etc.).
- `.app` should support full-height layout (`min-height: 100dvh`) with topbar, content, footer.
- Trello-like board UX:
  - fixed/sticky topbar
  - board header with title/actions
  - horizontal lane row with smooth scrolling
  - lanes as distinct surfaces
  - cards as compact readable items
- Inputs/buttons/panels/tags/avatars/modal-friendly baseline styles should be included.
- Add subtle hover/active/focus states for interactive elements.

Responsive behavior:
- Desktop: multi-lane horizontal board.
- Tablet: lane widths adapt without breaking rhythm.
- Mobile: lanes become swipe-friendly/full-width-ish, compact spacing, touch-first controls.
- Use breakpoints around `1024px`, `768px`, `480px`.
- Maintain minimum 44px touch targets for clickable controls.

Accessibility and UX:
- High contrast defaults (target WCAG-friendly contrast).
- Strong, visible `:focus-visible` treatment.
- `prefers-reduced-motion` support that disables non-essential motion.
- Ensure scrolling containers behave well on mobile (momentum scrolling, no awkward overflow traps).

Implementation requirements:
- CSS only, no HTML or JS output.
- No framework utilities (no Tailwind/Bootstrap).
- Use comments to separate major sections for maintainability.
- Output should be drop-in ready as a single `style.css`.

Definition of done:
- The result should look like a polished product UI, not a generated demo.
- It should feel like a Trello clone wearing a VS Code-inspired skin: clean, calm, efficient.
- Must be responsive, phone-friendly, and immediately usable across multiple pages.

```

Deretter brukte jeg litt mer enn en times tid på å refine dette produktet. Jeg lagde også et kanban brett for å tracke endringer og planer.

Flask prosjektet fungerer fint, og det eneste som mangler for morgendagen er litt backend + cloudflare + supabase

<img src="assets/Screenshot%202026-03-10%20at%2015.21.27-1.png" alt="" width="520" height="325" />

