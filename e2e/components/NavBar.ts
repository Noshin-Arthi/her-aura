import { expect, Locator, Page } from '@playwright/test';

/** The top navigation bar. A component, reused by every page that shows it. */
export class NavBar {
  readonly dashboard: Locator;
  readonly cycleTracker: Locator;
  readonly doctors: Locator;
  readonly appointments: Locator;
  readonly userName: Locator;
  readonly logoutButton: Locator;

  constructor(page: Page) {
    this.dashboard = page.locator('#nav-dashboard');
    this.cycleTracker = page.locator('#nav-cycle');
    this.doctors = page.locator('#nav-doctors');
    this.appointments = page.locator('#nav-appointments');
    this.userName = page.locator('#nav-user');
    this.logoutButton = page.locator('#btn-logout');
  }

  async expectLoggedInAs(fullName: string): Promise<void> {
    await expect(this.userName).toHaveText(fullName);
  }

  async logout(): Promise<void> {
    await this.logoutButton.click();
  }
}
