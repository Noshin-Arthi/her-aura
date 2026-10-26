import { expect, Locator, Page } from '@playwright/test';
import { BasePage } from './BasePage';

/** /doctors/{id}: profile, rating, the patient's own history with this doctor, reviews. */
export class DoctorProfilePage extends BasePage {
  protected path = '/doctors';
  readonly name: Locator;
  readonly rating: Locator;
  readonly historyRows: Locator;
  readonly reviews: Locator;
  readonly sampleBadges: Locator;

  constructor(page: Page) {
    super(page);
    this.name = page.locator('#doctor-name');
    this.rating = page.locator('#doctor-rating');
    this.historyRows = page.getByTestId('history-row');
    this.reviews = page.getByTestId('review');
    this.sampleBadges = page.getByTestId('sample-badge');
  }

  async openFor(doctorId: number): Promise<void> {
    await this.page.goto(`/doctors/${doctorId}`);
    await this.isLoaded();
  }

  async isLoaded(): Promise<void> {
    await expect(this.page.locator('#doctor-profile')).toBeVisible();
  }
}
