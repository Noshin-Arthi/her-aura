import { expect, Locator, Page } from '@playwright/test';
import { NavBar } from '../components/NavBar';

/**
 * Parent of every page object (inheritance).
 * - Holds shared state: the Playwright page and the nav bar component (composition).
 * - Declares `path` and `isLoaded()` as abstract: each child page MUST say where it lives
 *   and how to tell it has loaded (abstraction).
 */
export abstract class BasePage {
  readonly nav: NavBar;
  readonly errorMessage: Locator;
  readonly successMessage: Locator;

  protected abstract readonly path: string;

  constructor(protected readonly page: Page) {
    this.nav = new NavBar(page);
    this.errorMessage = page.locator('#error-message');
    this.successMessage = page.locator('#success-message');
  }

  /** Each page decides what "loaded" means for it. */
  abstract isLoaded(): Promise<void>;

  async open(): Promise<this> {
    await this.page.goto(this.path);
    await this.isLoaded();
    return this;
  }

  async expectError(text: string | RegExp): Promise<void> {
    await expect(this.errorMessage).toContainText(text);
  }

  async expectSuccess(text: string | RegExp): Promise<void> {
    await expect(this.successMessage).toContainText(text);
  }
}
