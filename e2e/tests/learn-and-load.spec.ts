/**
 * Feature: Learn (featured articles, premium library, rewarded ads) and Emotional load
 * Requirement: docs/REQUIREMENTS.md, US-30, US-31, US-32
 */
import { test, expect } from '../fixtures/test';
import { isoDaysAgo } from '../utils/testData';

test.describe('Learn', () => {
  test('US-30 AC1: 10 featured articles are free, with safety guides marked always free', async ({ pages, user }) => {
    await pages.learn.open();
    await expect(pages.learn.featuredCards).toHaveCount(10);
    await pages.learn.article('ovarian-cysts').expectUnlocked(true);
    await expect(pages.learn.article('breast-checks').root.getByTestId('always-free')).toBeVisible();
  });

  test('US-31 AC1-2: a free user unlocks a premium article by watching an ad', async ({ pages, page, user }) => {
    await pages.learn.open();
    const card = pages.learn.article('endometriosis');
    await card.expectUnlocked(false);

    await card.watchAd.click();
    await pages.ad.watchToEndAndClaim();

    await pages.learn.expectSuccess('Unlocked for 24 hours');
    await card.expectUnlocked(true);
    await expect(card.readLink).toHaveAttribute('href', /who\.int/);
    await pages.learn.article('menopause').expectUnlocked(false);   // only that article
  });

  test('US-31 AC3: Premium (demo) unlocks the whole library', async ({ pages, user }) => {
    await pages.premium.open();
    await pages.premium.start.click();

    await pages.learn.isLoaded();
    await expect(pages.learn.plan).toHaveText('Premium');
    for (const slug of ['endometriosis', 'cervical-cancer', 'depression']) {
      await pages.learn.article(slug).expectUnlocked(true);
    }
  });
});

test.describe('Emotional load @mobile', () => {
  test('US-32 AC1-3: check-in shows averages, load sources and a hand-off tip', async ({ pages, page, user }) => {
    for (let i = 1; i <= 4; i++) {
      const res = await page.request.post('/api/emotional', {
        data: { log_date: isoDaysAgo(i), mood: 3, stress: 8, energy: 2, areas: ['caregiving'] },
      });
      expect(res.status()).toBe(201);
    }
    await pages.load.open();
    await pages.load.checkIn({ mood: 2, stress: 8, energy: 2, areas: ['caregiving', 'work'], handoff: 'school forms' });

    await pages.load.expectSuccess('Check-in saved');
    await expect(pages.load.avgStress).toHaveText('8.0');
    await expect(pages.load.topAreas.first()).toHaveAttribute('data-area', 'caregiving');
    await expect(pages.load.suggestions.filter({ hasText: 'High stress on 5' })).toBeVisible();
    await expect(pages.load.suggestions.filter({ hasText: 'Caring for children or elders:' })).toBeVisible();
  });

  test('US-32 AC5: the support line is always visible', async ({ pages, user }) => {
    await pages.load.open();
    await expect(pages.load.supportLine).toContainText('09612-119911');
    await expect(pages.load.supportLine).toContainText('999');
  });
});
