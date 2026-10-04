/**
 * Feature: Account registration and login
 * Requirement: docs/REQUIREMENTS.md, US-01 and US-02
 */
import { test, expect } from '../fixtures/test';
import { newUser } from '../utils/testData';

test.describe('Authentication @mobile', () => {
  test('US-01 AC1: new user can register and lands on the dashboard', async ({ pages, page }) => {
    const user = newUser();

    await test.step('Register through the UI', async () => {
      await pages.register.open();
      await pages.register.register(user);
    });

    await test.step('Dashboard greets the user by name', async () => {
      await expect(page).toHaveURL(/\/dashboard/);
      await expect(pages.dashboard.heading).toHaveText(`Hello, ${user.fullName}`);
      await pages.dashboard.nav.expectLoggedInAs(user.fullName);
    });
  });

  test('US-01 AC2: duplicate email shows an error', async ({ pages, user }) => {
    await pages.dashboard.open();
    await pages.dashboard.nav.logout();

    await pages.register.open();
    await pages.register.register({ ...user, email: user.email.toUpperCase() });
    await pages.register.expectError('already registered');
  });

  test('US-02 AC2: wrong password shows a generic error', async ({ pages, user }) => {
    await pages.dashboard.open();
    await pages.dashboard.nav.logout();

    await pages.login.open();
    await pages.login.login(user.email, 'WrongPassword1!');
    await pages.login.expectError('Invalid email or password.');
  });

  test('US-02 AC3: logged-out user is redirected to login', async ({ pages, page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/);
    await pages.login.isLoaded();
  });
});
