import { expect, Locator, Page } from '@playwright/test';
import { BasePage } from './BasePage';

/** One doctor card on the Doctors page (component scoped to its own root locator). */
export class DoctorCard {
  readonly name: Locator;
  readonly specialty: Locator;
  readonly slotSelect: Locator;
  readonly reason: Locator;
  readonly bookButton: Locator;

  constructor(readonly root: Locator) {
    this.name = root.getByTestId('doctor-name');
    this.specialty = root.getByTestId('doctor-specialty');
    this.slotSelect = root.getByTestId('slot-select');
    this.reason = root.getByTestId('reason-input');
    this.bookButton = root.getByTestId('btn-book');
  }

  /** Books the first open slot and returns its visible label, e.g. "Mon 06 Oct, 10:00 AM". */
  async bookFirstSlot(reason = ''): Promise<string> {
    const label = (await this.slotSelect.locator('option').first().textContent())?.trim() ?? '';
    if (reason) await this.reason.fill(reason);
    await this.bookButton.click();
    return label;
  }
}

export class DoctorsPage extends BasePage {
  protected readonly path = '/doctors';
  readonly cards: Locator;
  readonly specialties: Locator;
  readonly specialtyFilter: Locator;

  constructor(page: Page) {
    super(page);
    this.cards = page.getByTestId('doctor-card');
    this.specialties = page.getByTestId('doctor-specialty');
    this.specialtyFilter = page.locator('#specialty');
  }

  async isLoaded(): Promise<void> {
    await expect(this.page.getByRole('heading', { name: 'Doctors', exact: true })).toBeVisible();
  }

  card(doctorName: string): DoctorCard {
    return new DoctorCard(this.cards.filter({ has: this.page.getByTestId('doctor-name').filter({ hasText: doctorName }) }));
  }

  firstCard(): DoctorCard {
    return new DoctorCard(this.cards.first());
  }
}
