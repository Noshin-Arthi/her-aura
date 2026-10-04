import { expect, Locator, Page } from '@playwright/test';
import { BasePage } from './BasePage';
import { TestUser } from '../utils/testData';

export class RegisterPage extends BasePage {
  protected readonly path = '/register';
  readonly fullName: Locator;
  readonly email: Locator;
  readonly password: Locator;
  readonly submit: Locator;

  constructor(page: Page) {
    super(page);
    this.fullName = page.locator('#full_name');
    this.email = page.locator('#email');
    this.password = page.locator('#password');
    this.submit = page.locator('#btn-register');
  }

  async isLoaded(): Promise<void> {
    await expect(this.page.getByRole('heading', { name: 'Create account' })).toBeVisible();
  }

  async register(user: TestUser): Promise<void> {
    await this.fullName.fill(user.fullName);
    await this.email.fill(user.email);
    await this.password.fill(user.password);
    await this.submit.click();
  }
}

export class LoginPage extends BasePage {
  protected readonly path = '/login';
  readonly email: Locator;
  readonly password: Locator;
  readonly submit: Locator;

  constructor(page: Page) {
    super(page);
    this.email = page.locator('#email');
    this.password = page.locator('#password');
    this.submit = page.locator('#btn-login');
  }

  async isLoaded(): Promise<void> {
    await expect(this.page.getByRole('heading', { name: 'Log in' })).toBeVisible();
  }

  async login(email: string, password: string): Promise<void> {
    await this.email.fill(email);
    await this.password.fill(password);
    await this.submit.click();
  }
}
