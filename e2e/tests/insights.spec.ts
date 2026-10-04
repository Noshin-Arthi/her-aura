/**
 * Feature: Red-flag insight (Goff symptom index, 12+ symptom days in 30)
 * Requirement: docs/REQUIREMENTS.md, US-04
 * Test data is created through the API so the test only exercises what it is checking.
 */
import { APIRequestContext } from '@playwright/test';
import { test, expect } from '../fixtures/test';
import { isoDaysAgo } from '../utils/testData';

async function logSymptomDays(request: APIRequestContext, days: number) {
  for (let i = 0; i < days; i++) {
    const res = await request.post('/api/logs', { data: { log_date: isoDaysAgo(i), pelvic_or_abdominal_pain: true } });
    expect(res.status()).toBe(201);
  }
}

test.describe('Health insight', () => {
  test('US-04 AC1: 12 symptom days shows the red flag and a doctor link', async ({ pages, page, user }) => {
    await logSymptomDays(page.request, 12);
    await pages.dashboard.open();

    await pages.dashboard.expectRedFlag(true);
    await expect(pages.dashboard.insightMessage).toContainText('12 of the last 30 days');
    await expect(pages.dashboard.findDoctorButton).toBeVisible();
  });

  test('US-04 AC2: 11 symptom days does not show the red flag (boundary)', async ({ pages, page, user }) => {
    await logSymptomDays(page.request, 11);
    await pages.dashboard.open();

    await pages.dashboard.expectRedFlag(false);
    await expect(pages.dashboard.findDoctorButton).toHaveCount(0);
  });

  test('US-04 AC5: neutral symptom-day counter with an explanation', async ({ pages, page, user }) => {
    await logSymptomDays(page.request, 4);
    await pages.dashboard.open();

    await expect(pages.dashboard.symptomDays).toHaveText('4');
    await expect(pages.dashboard.symptomDaysBar).toHaveAttribute('value', '4');
    await pages.dashboard.expectRedFlag(false);

    await pages.dashboard.openExplainer();
    await expect(pages.dashboard.goffExplainer).toContainText('not a diagnosis');
  });

  test('US-04 AC3: the medical disclaimer is always shown', async ({ pages, user }) => {
    await pages.dashboard.open();
    await expect(pages.dashboard.disclaimer).toContainText('not a medical device');
  });
});
