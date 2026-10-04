import { expect, Locator, Page } from '@playwright/test';
import { BasePage } from './BasePage';

export class AppointmentsPage extends BasePage {
  protected readonly path = '/appointments';
  readonly rows: Locator;

  constructor(page: Page) {
    super(page);
    this.rows = page.getByTestId('appointment-row');
  }

  async isLoaded(): Promise<void> {
    await expect(this.page.getByRole('heading', { name: 'My appointments' })).toBeVisible();
  }

  rowForDoctor(doctorName: string): Locator {
    return this.rows.filter({ has: this.page.getByTestId('appointment-doctor').filter({ hasText: doctorName }) });
  }

  async cancel(doctorName: string): Promise<void> {
    await this.rowForDoctor(doctorName).getByTestId('btn-cancel').click();
  }

  async expectStatus(doctorName: string, status: 'booked' | 'cancelled'): Promise<void> {
    await expect(this.rowForDoctor(doctorName).getByTestId('appointment-status')).toHaveText(status);
  }
}
