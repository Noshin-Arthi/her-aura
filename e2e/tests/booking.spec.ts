/**
 * Feature: Book and cancel an appointment
 * Requirement: docs/REQUIREMENTS.md, US-05 and US-06
 * Serial: these tests share the same pool of seeded slots, so running them in parallel would
 * make them race for the same "first" slot (that race is covered by the API double-booking test).
 */
import { test, expect } from '../fixtures/test';

test.describe.configure({ mode: 'serial' });

const DOCTOR = 'Dr. Nusrat Jahan';

test.describe('Appointments', () => {
  test('US-05 AC1: patient books the first open slot', async ({ pages, page, user }) => {
    await pages.doctors.open();
    const slotLabel = await pages.doctors.card(DOCTOR).bookFirstSlot('Pelvic pain follow-up');

    await expect(page).toHaveURL(/\/appointments/);
    await pages.appointments.expectSuccess('Appointment booked.');
    await pages.appointments.expectStatus(DOCTOR, 'booked');
    await expect(pages.appointments.rowForDoctor(DOCTOR)).toContainText(slotLabel);
  });

  test('US-05 AC2: a booked slot is no longer offered', async ({ pages, user }) => {
    await pages.doctors.open();
    const card = pages.doctors.card(DOCTOR);
    const bookedLabel = await card.bookFirstSlot();

    await pages.doctors.open();
    await expect(card.slotSelect.locator('option', { hasText: bookedLabel })).toHaveCount(0);
  });

  test('US-06 AC1: patient cancels a booking', async ({ pages, user }) => {
    await pages.doctors.open();
    await pages.doctors.card(DOCTOR).bookFirstSlot();

    await pages.appointments.cancel(DOCTOR);
    await pages.appointments.expectStatus(DOCTOR, 'cancelled');
  });
});
