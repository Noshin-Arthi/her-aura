/**
 * Feature: Daily symptom log
 * Requirement: docs/REQUIREMENTS.md, US-03 and US-13
 */
import { test, expect } from '../fixtures/test';
import { isoDaysAgo } from '../utils/testData';

test.describe('Symptom log @mobile', () => {
  test('US-03 AC1: saved log appears on the dashboard', async ({ pages, user }) => {
    const today = isoDaysAgo(0);

    await pages.symptomLog.open();
    await pages.symptomLog.submitLog({ date: today, flow: 'medium', pain: 6, symptoms: ['bloating'], notes: 'after lunch' });

    await pages.dashboard.expectSuccess('Log saved.');
    const row = pages.dashboard.logRowFor(today);
    await expect(row).toContainText('medium');
    await expect(row).toContainText('6/10');
    await expect(row).toContainText('bloating');
  });

  test('US-03 AC2: a future date is blocked by the form', async ({ pages, page, user }) => {
    await pages.symptomLog.open();
    await pages.symptomLog.fillLog({ date: isoDaysAgo(-1) });
    expect(await pages.symptomLog.dateIsInvalid()).toBe(true);

    await pages.symptomLog.save.click();
    await expect(page).toHaveURL(/\/log$/);   // browser refused to submit
    // The server also rejects it if the form is bypassed: see tests/api/test_logs_api.py::test_future_date_rejected
  });

  test('US-03 AC3: only one log per day', async ({ pages, user }) => {
    const today = isoDaysAgo(0);
    await pages.symptomLog.open();
    await pages.symptomLog.submitLog({ date: today });
    await pages.symptomLog.open();
    await pages.symptomLog.submitLog({ date: today });
    await pages.symptomLog.expectError('already have a log');
  });

  test('US-13 AC1: "Same as yesterday" copies yesterday\'s log to today', async ({ pages, page, user }) => {
    const res = await page.request.post('/api/logs', {
      data: { log_date: isoDaysAgo(1), period_flow: 'heavy', pain_level: 7, pelvic_or_abdominal_pain: true },
    });
    expect(res.status()).toBe(201);

    await pages.symptomLog.open();
    await pages.symptomLog.sameAsYesterday.click();

    await pages.dashboard.expectSuccess('Log saved.');
    const row = pages.dashboard.logRowFor(isoDaysAgo(0));
    await expect(row).toContainText('heavy');
    await expect(row).toContainText('7/10');
    await expect(row).toContainText('pain');
  });

  test('US-13 AC2: "Same as yesterday" with no log yesterday shows an error', async ({ pages, user }) => {
    await pages.symptomLog.open();
    await pages.symptomLog.sameAsYesterday.click();
    await pages.symptomLog.expectError('no log for the previous day');
  });
});
