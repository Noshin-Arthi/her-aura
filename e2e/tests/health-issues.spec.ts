/**
 * Feature: Log any health issue and get a "which doctor, when?" suggestion
 * Requirement: docs/REQUIREMENTS.md, US-16 and US-17
 */
import { test, expect } from '../fixtures/test';
import { isoDaysAgo } from '../utils/testData';

test.describe('Health issues @mobile', () => {
  test('US-16 AC1: logged issue appears in the history', async ({ pages, user }) => {
    await pages.healthLog.open();
    await pages.healthLog.logIssue({ category: 'hair_fall', severity: 4, notes: 'more than usual when combing' });

    await pages.dashboard.expectSuccess('Log saved.');
    const row = pages.dashboard.issueRows.filter({ hasText: 'Hair fall' });
    await expect(row).toContainText('4/10');
    await expect(row).toContainText('more than usual when combing');
  });

  test('US-17 AC1: severe toothache suggests a dentist and links to dentists only', async ({ pages, page, user }) => {
    await pages.healthLog.open();
    await pages.healthLog.logIssue({ category: 'toothache', severity: 9 });

    const suggestion = pages.dashboard.suggestion('toothache');
    await expect(suggestion).toHaveAttribute('data-urgency', 'soon');
    await expect(suggestion).toContainText('See a doctor soon: Dentistry');

    await suggestion.getByTestId('suggestion-find-doctor').click();
    await pages.doctors.isLoaded();
    await expect(page).toHaveURL(/specialty=Dentistry/);
    await expect(pages.doctors.specialties).not.toHaveCount(0);
    for (const text of await pages.doctors.specialties.allTextContents()) {
      expect(text).toBe('Dentistry');
    }
  });

  test('US-17 AC2: recurring headaches suggest a neurologist', async ({ pages, page, user }) => {
    for (let i = 0; i < 4; i++) {
      const res = await page.request.post('/api/health-issues', { data: { log_date: isoDaysAgo(i), category: 'headache', severity: 3 } });
      expect(res.status()).toBe(201);
    }
    await pages.dashboard.open();
    await expect(pages.dashboard.suggestion('headache')).toContainText('Neurology');
  });

  test('US-17 AC4: emergency guidance is always visible', async ({ pages, user }) => {
    await pages.dashboard.open();
    await expect(pages.dashboard.emergencyNote).toContainText('999');
  });
});
