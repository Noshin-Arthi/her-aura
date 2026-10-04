/**
 * Feature: Sleep, mindfulness programme, basal body temperature
 * Requirement: docs/REQUIREMENTS.md, US-25, US-26, US-27
 */
import { test, expect } from '../fixtures/test';
import { isoDaysAgo } from '../utils/testData';

test.describe('Wellbeing @mobile', () => {
  test('US-26 AC1: logged nights show in the 7-night summary', async ({ pages, user }) => {
    await pages.sleep.open();
    await pages.sleep.logNight(6, 2, isoDaysAgo(1));
    await pages.sleep.expectSuccess('Sleep saved.');
    await pages.sleep.logNight(8, 4, isoDaysAgo(0));

    await expect(pages.sleep.avgHours).toHaveText('7.0');
    await expect(pages.sleep.avgQuality).toHaveText('3.0');
    await expect(pages.sleep.windDownItems).toHaveCount(3);
  });

  test('US-27 AC1: mindfulness days unlock one after another', async ({ pages, user }) => {
    await pages.mind.open();
    await expect(pages.mind.day(1)).toHaveAttribute('data-state', 'current');
    await expect(pages.mind.day(2)).toHaveAttribute('data-state', 'locked');

    await pages.mind.completeCurrentDay(1);

    await expect(pages.mind.day(1)).toHaveAttribute('data-state', 'done');
    await expect(pages.mind.day(2)).toHaveAttribute('data-state', 'current');
    await expect(pages.mind.progress).toContainText('1 of 7');
  });

  test('US-25 AC2: a temperature rise confirms ovulation, with the not-contraception warning', async ({ pages, page, user }) => {
    const temps = [36.40, 36.35, 36.45, 36.38, 36.42, 36.40, 36.55, 36.60, 36.70];
    for (let i = 0; i < temps.length; i++) {
      const res = await page.request.post('/api/logs', { data: { log_date: isoDaysAgo(temps.length - 1 - i), bbt_celsius: temps[i] } });
      expect(res.status()).toBe(201);
    }
    await pages.dashboard.open();
    await expect(page.locator('#ovulation-confirmed')).toContainText('ovulation likely happened');
    await expect(page.locator('#not-contraception')).toContainText('not a contraceptive');
  });

  test('US-25 AC1: temperature can be entered on the cycle form', async ({ pages, page, user }) => {
    await pages.symptomLog.open();
    await page.locator('#bbt_celsius').fill('36.45');
    await pages.symptomLog.save.click();
    await pages.dashboard.expectSuccess('Log saved.');
    await expect(page.locator('#ovulation-pending')).toContainText('1 temperature reading');
  });
});
