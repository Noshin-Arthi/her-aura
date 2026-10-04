import { test as base, expect } from '@playwright/test';
import { PageManager } from '../pages/PageManager';
import { newUser, TestUser } from '../utils/testData';

type Fixtures = {
  pages: PageManager;
  /** A brand-new user, already logged in. Created through the API (fast), not the UI. */
  user: TestUser;
};

export const test = base.extend<Fixtures>({
  pages: async ({ page }, use) => {
    await use(new PageManager(page));
  },

  user: async ({ page }, use) => {
    const user = newUser();
    // page.request shares cookies with the browser, so the UI is logged in too.
    const response = await page.request.post('/api/auth/register', {
      data: { email: user.email, full_name: user.fullName, password: user.password },
    });
    expect(response.status(), await response.text()).toBe(201);
    await use(user);
  },
});

export { expect };
