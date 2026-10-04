/**
 * Feature: Landing page and "Try it" demo
 * Requirement: docs/REQUIREMENTS.md, US-24
 */
import { test, expect } from '../fixtures/test';

test.describe('Landing page @mobile', () => {
  test('US-24 AC1: demo shows a live suggestion without an account', async ({ pages }) => {
    await pages.home.open();
    await pages.home.tryDemo(['toothache'], 9, 1);

    await expect(pages.home.demoSuggestions.first()).toContainText('See a doctor soon: Dentistry');
    await expect(pages.home.demoSuggestions.first()).toHaveAttribute('data-urgency', 'soon');
    await expect(pages.home.demoResult).toContainText('not a diagnosis');
  });

  test('US-24 AC2: demo uses the real recurring rule (3 days no, 4 days yes)', async ({ pages }) => {
    await pages.home.open();
    await pages.home.tryDemo(['headache'], 3, 3);
    await expect(pages.home.demoResult).toContainText('Nothing to flag yet');

    await pages.home.demoDays.fill('4');
    await expect(pages.home.demoSuggestions.first()).toContainText('Neurology');
  });

  test('US-24 AC3: only honest trust points and fictional-data notice are shown', async ({ pages, page }) => {
    await pages.home.open();
    await expect(pages.home.trustPoints).toHaveText([
      'Your logs are private to your account',
      'Every suggestion explains why',
      'A tracking tool, not a diagnosis',
    ]);
    await expect(page.getByText('all doctors and clinics shown are fictional')).toBeVisible();
    await expect(pages.home.specialtyChips).not.toHaveCount(0);
  });

  test('US-24 AC4: logged-in users skip the landing page', async ({ page, user }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/\/dashboard/);
  });
});
