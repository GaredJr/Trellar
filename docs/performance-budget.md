# Performance Budget

This project uses a lightweight Flask + server-rendered architecture.

## Budgets

- HTML transfer per route: <= 60 KB gzip
- CSS (`/static/style.css`): <= 70 KB gzip
- JavaScript (`/static/app.js`): <= 35 KB gzip
- Font payload (critical preloaded): <= 160 KB total
- Largest Contentful Paint (desktop): <= 2.5s on simulated 4G
- Largest Contentful Paint (mobile): <= 3.0s on simulated 4G
- Cumulative Layout Shift: <= 0.1
- Time to Interactive (mobile): <= 3.5s

## Budget Gates

- Lighthouse Performance score: >= 90
- Lighthouse Accessibility score: >= 95
- Axe: 0 serious/critical violations

## Optimization Rules

- Prefer server-rendered HTML over client-heavy rendering.
- Keep custom JS focused on accessibility and interaction only.
- Avoid large visual effects and expensive paint operations.
- Preload only the fonts used in first viewport.
- Monitor CSS and JS growth on each pull request.
