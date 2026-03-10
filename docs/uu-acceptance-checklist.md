# UU Acceptance Checklist (WCAG 2.2 AA)

Use this checklist before each release.

## Perceivable

- [ ] Page has correct `lang` and direction (`dir`) settings.
- [ ] Text contrast meets AA for body, labels, and interactive UI.
- [ ] Information is not conveyed by color alone.
- [ ] Zoom at 200% and 400% keeps content usable without loss.
- [ ] UI supports forced colors and high contrast modes.

## Operable

- [ ] Skip links work for keyboard users.
- [ ] All controls reachable and usable by keyboard.
- [ ] Focus order is logical and visible.
- [ ] Modal dialogs trap focus and close with Escape.
- [ ] No keyboard trap in lanes, menus, filters, or dialogs.

## Understandable

- [ ] Forms show clear labels, required state, and helper text.
- [ ] Validation errors are announced and linked to fields.
- [ ] Confirmation is required for destructive actions.
- [ ] Undo is available for reversible destructive actions.
- [ ] Time and activity labels are understandable and localized.

## Robust

- [ ] Landmarks (`header`, `nav`, `main`, `footer`) are present.
- [ ] `aria-current`, `aria-expanded`, `aria-controls` reflect state.
- [ ] Dynamic status messages use `aria-live`.
- [ ] Lists, headings, and breadcrumb semantics are valid.
- [ ] No major Axe/Lighthouse accessibility findings.

## Release Gate

- [ ] Lighthouse + Axe CI checks pass.
- [ ] Manual keyboard pass completed on all key routes.
- [ ] Screen-reader smoke test completed for Home, Boards, Board, User, Settings, Activity.
