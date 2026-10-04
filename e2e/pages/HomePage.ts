import { expect, Locator, Page } from '@playwright/test';
import { BasePage } from './BasePage';

/** Public landing page with the "Try it" demo widget. */
export class HomePage extends BasePage {
  protected readonly path = '/';
  readonly createAccount: Locator;
  readonly trustPoints: Locator;
  readonly demoSeverity: Locator;
  readonly demoDays: Locator;
  readonly demoResult: Locator;
  readonly demoSuggestions: Locator;
  readonly specialtyChips: Locator;

  constructor(page: Page) {
    super(page);
    this.createAccount = page.locator('#link-register');
    this.trustPoints = page.locator('#trust-points li');
    this.demoSeverity = page.locator('#demo-severity');
    this.demoDays = page.locator('#demo-days');
    this.demoResult = page.locator('#demo-result');
    this.demoSuggestions = page.getByTestId('demo-suggestion');
    this.specialtyChips = page.getByTestId('specialty-chip');
  }

  async isLoaded(): Promise<void> {
    await expect(this.page.getByRole('heading', { name: /Know when to see a doctor/ })).toBeVisible();
  }

  async tryDemo(categories: string[], severity: number, days: number): Promise<void> {
    await this.demoSeverity.fill(String(severity));
    await this.demoDays.fill(String(days));
    for (const category of categories) {
      await this.page.locator(`#demo-${category}`).check();
    }
  }
}
