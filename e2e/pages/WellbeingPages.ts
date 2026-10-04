import { expect, Locator, Page } from '@playwright/test';
import { BasePage } from './BasePage';

export class SleepPage extends BasePage {
  protected readonly path = '/sleep';
  readonly date: Locator;
  readonly hours: Locator;
  readonly quality: Locator;
  readonly save: Locator;
  readonly avgHours: Locator;
  readonly avgQuality: Locator;
  readonly windDownItems: Locator;

  constructor(page: Page) {
    super(page);
    this.date = page.locator('#sleep_date');
    this.hours = page.locator('#hours');
    this.quality = page.locator('#quality');
    this.save = page.locator('#btn-save-sleep');
    this.avgHours = page.locator('#avg-hours');
    this.avgQuality = page.locator('#avg-quality');
    this.windDownItems = page.getByTestId('wind-down-item');
  }

  async isLoaded(): Promise<void> {
    await expect(this.page.getByRole('heading', { name: 'Sleep', exact: true })).toBeVisible();
  }

  async logNight(hours: number, quality: number, date?: string): Promise<void> {
    if (date) await this.date.fill(date);
    await this.hours.fill(String(hours));
    await this.quality.fill(String(quality));
    await this.save.click();
  }
}

export class MindPage extends BasePage {
  protected readonly path = '/mind';
  readonly progress: Locator;

  constructor(page: Page) {
    super(page);
    this.progress = page.locator('#mind-progress');
  }

  async isLoaded(): Promise<void> {
    await expect(this.page.getByRole('heading', { name: 'Mindfulness for beginners' })).toBeVisible();
  }

  day(n: number): Locator {
    return this.page.locator(`[data-testid="mind-day"][data-day="${n}"]`);
  }

  async completeCurrentDay(n: number): Promise<void> {
    await this.day(n).getByTestId('btn-complete-day').click();
  }
}
