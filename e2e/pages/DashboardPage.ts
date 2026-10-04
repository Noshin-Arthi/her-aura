import { expect, Locator, Page } from '@playwright/test';
import { BasePage } from './BasePage';

export class DashboardPage extends BasePage {
  protected readonly path = '/dashboard';
  readonly heading: Locator;
  readonly insightCard: Locator;
  readonly insightMessage: Locator;
  readonly disclaimer: Locator;
  readonly findDoctorButton: Locator;
  readonly logRows: Locator;
  readonly symptomDays: Locator;
  readonly symptomDaysBar: Locator;
  readonly goffExplainer: Locator;
  readonly issueRows: Locator;
  readonly emergencyNote: Locator;

  constructor(page: Page) {
    super(page);
    this.heading = page.locator('#dashboard-heading');
    this.insightCard = page.locator('#insight-card');
    this.insightMessage = page.locator('#insight-message');
    this.disclaimer = page.locator('#insight-disclaimer');
    this.findDoctorButton = page.locator('#btn-find-doctor');
    this.logRows = page.getByTestId('log-row');
    this.symptomDays = page.locator('#symptom-days');
    this.symptomDaysBar = page.locator('#symptom-days-bar');
    this.goffExplainer = page.locator('#goff-explainer');
    this.issueRows = page.getByTestId('issue-row');
    this.emergencyNote = page.locator('#emergency-note');
  }

  async isLoaded(): Promise<void> {
    await expect(this.heading).toBeVisible();
  }

  logRowFor(isoDate: string): Locator {
    return this.page.locator(`[data-testid="log-row"][data-date="${isoDate}"]`);
  }

  suggestion(category: string): Locator {
    return this.page.locator(`[data-testid="suggestion"][data-category="${category}"]`);
  }

  async openExplainer(): Promise<void> {
    await this.goffExplainer.locator('summary').click();
  }

  async expectRedFlag(shown: boolean): Promise<void> {
    await expect(this.insightCard).toHaveAttribute('data-red-flag', String(shown));
  }
}
