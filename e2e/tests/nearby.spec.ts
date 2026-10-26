/**
 * Feature: Doctors near me (map, distance, rating sort) and doctor profiles
 * Requirement: docs/REQUIREMENTS.md, US-22 and US-21
 * The test server reads OpenStreetMap answers from tests/fixtures, so no real network calls happen.
 */
import { test, expect } from '../fixtures/test';

const DHANMONDI = { latitude: 23.7461, longitude: 90.3742 };

test.describe('Doctors near me', () => {
  test.use({ geolocation: DHANMONDI, permissions: ['geolocation'] });

  test('US-22 AC1: "Use my location" lists Her Aura doctors and nearby places with distances', async ({ pages, user }) => {
    await pages.doctors.open();
    await pages.doctors.useLocation.click();

    await expect(pages.doctors.nearStatus).toContainText('your location');
    await expect(pages.doctors.herAuraResults.first()).toBeVisible();
    await expect(pages.doctors.externalResults.filter({ hasText: 'Sample City Hospital' })).toBeVisible();
    await expect(pages.doctors.herAuraResults.first().getByTestId('near-distance')).toHaveText(/\d+(\.\d)? km/);
    await expect(pages.doctors.externalResults.first().getByTestId('near-directions')).toHaveAttribute('href', /google\.com\/maps\/dir/);
  });

  test('US-22 AC2: "Nearest" sorts by distance', async ({ pages, user }) => {
    await pages.doctors.open();
    await pages.doctors.useLocation.click();
    await expect(pages.doctors.herAuraResults.first()).toBeVisible();

    await pages.doctors.nearSort.selectOption('distance');
    await expect.poll(async () => {
      const d = await pages.doctors.herAuraDistances();
      return d.length > 1 && d.every((v, i) => i === 0 || d[i - 1] <= v);
    }).toBe(true);
  });

  test('US-22 AC3: a typed area works without sharing location', async ({ pages, user }) => {
    await pages.doctors.open();
    await pages.doctors.searchArea('Dhanmondi');
    await expect(pages.doctors.nearStatus).toContainText('Dhanmondi');
    await expect(pages.doctors.herAuraResults.first()).toBeVisible();
  });

  test('US-22 AC4: specialty filter narrows both lists', async ({ pages, page, user }) => {
    await page.goto('/doctors?specialty=Dermatology');
    await pages.doctors.useLocation.click();
    await expect(pages.doctors.herAuraResults).toHaveCount(1);
    await expect(pages.doctors.externalResults.filter({ hasText: 'Sample Skin Clinic' })).toBeVisible();
    await expect(pages.doctors.externalResults.filter({ hasText: 'Sample Dental Care' })).toHaveCount(0);
  });
});

test.describe('Doctor profile', () => {
  test('US-21 AC1: profile shows details, rating and clearly labelled sample reviews', async ({ pages, page, user }) => {
    await pages.doctors.open();
    await pages.doctors.card('Dr. Tanvir Ahmed').root.getByTestId('doctor-profile-link').click();

    await pages.doctorProfile.isLoaded();
    await expect(pages.doctorProfile.name).toHaveText('Dr. Tanvir Ahmed');
    await expect(pages.doctorProfile.rating).toContainText('★');
    await expect(pages.doctorProfile.reviews).toHaveCount(4);
    await expect(pages.doctorProfile.sampleBadges).toHaveCount(4);
    await expect(page.locator('#no-history')).toBeVisible();
  });

  test('US-21 AC2: a booked future visit shows in history but cannot be rated yet', async ({ pages, page, user }) => {
    await pages.doctors.open();
    await pages.doctors.card('Dr. Mehedi Hasan').bookFirstSlot('Recurring headaches');
    await pages.appointments.isLoaded();

    await pages.doctors.open();
    await pages.doctors.card('Dr. Mehedi Hasan').root.getByTestId('doctor-profile-link').click();
    await expect(pages.doctorProfile.historyRows).toHaveCount(1);
    await expect(pages.doctorProfile.historyRows.first()).toContainText('Recurring headaches');
    await expect(page.getByTestId('review-form')).toHaveCount(0);
  });
});
