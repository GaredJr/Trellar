const { test, expect } = require('@playwright/test');

const DEMO_EMAIL = process.env.TRELLAR_DEMO_EMAIL || 'demo@trellar.local';
const DEMO_PASSWORD = process.env.TRELLAR_DEMO_PASSWORD || 'trellar-demo';

async function login(page) {
  await page.goto('/login');
  await page.fill('#email', DEMO_EMAIL);
  await page.fill('#password', DEMO_PASSWORD);
  await page.locator('form[action="/login"] button[type="submit"]').click();
  await expect(page).toHaveURL(/\/$/);
}

test.beforeEach(async ({ page }) => {
  await login(page);
});

test('skip links are keyboard reachable', async ({ page }) => {
  await page.goto('/');
  await page.keyboard.press('Tab');
  await expect(page.getByText(/Skip to main content|Hopp til hovedinnhold/)).toBeVisible();
});

test('board card can move with keyboard shortcut', async ({ page }) => {
  await page.goto('/boards/product-roadmap');

  const firstCard = page.locator('.card').first();
  await firstCard.focus();

  await page.keyboard.down('Alt');
  await page.keyboard.press('ArrowRight');
  await page.keyboard.up('Alt');

  const live = page.locator('#board-live');
  await expect(live).toContainText(/Moved|Flyttet/);
});

test('user form shows validation summary on invalid email', async ({ page }) => {
  await page.goto('/user');
  await page.fill('#email', 'invalid-email');
  await page.locator('form[action="/user"] button[type="submit"]').click();
  await expect(page.locator('.error-summary')).toBeVisible();
});
