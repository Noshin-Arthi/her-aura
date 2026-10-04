import { expect, Locator, Page } from '@playwright/test';
import { BasePage } from './BasePage';

/** One article card (component scoped to its root). */
export class ArticleCard {
  readonly readLink: Locator;
  readonly watchAd: Locator;
  readonly goPremium: Locator;

  constructor(readonly root: Locator) {
    this.readLink = root.getByTestId('read-link');
    this.watchAd = root.getByTestId('watch-ad');
    this.goPremium = root.getByTestId('go-premium');
  }

  async expectUnlocked(unlocked: boolean): Promise<void> {
    await expect(this.root).toHaveAttribute('data-unlocked', String(unlocked));
    await expect(this.readLink).toHaveCount(unlocked ? 1 : 0);
  }
}

export class LearnPage extends BasePage {
  protected readonly path = '/learn';
  readonly cards: Locator;
  readonly featuredCards: Locator;
  readonly plan: Locator;

  constructor(page: Page) {
    super(page);
    this.cards = page.getByTestId('article-card');
    this.featuredCards = page.locator('#featured [data-testid="article-card"]');
    this.plan = page.locator('#plan');
  }

  async isLoaded(): Promise<void> {
    await expect(this.page.getByRole('heading', { name: 'Learn', exact: true })).toBeVisible();
  }

  article(slug: string): ArticleCard {
    return new ArticleCard(this.page.locator(`[data-testid="article-card"][data-slug="${slug}"]`));
  }
}

export class AdPage {
  readonly claim: Locator;
  constructor(private readonly page: Page) {
    this.claim = page.locator('#btn-claim');
  }

  /** Waits for the countdown to finish (the button enables itself), then claims. */
  async watchToEndAndClaim(): Promise<void> {
    await expect(this.claim).toBeDisabled();
    await expect(this.claim).toBeEnabled({ timeout: 15_000 });
    await this.claim.click();
  }
}

export class PremiumPage extends BasePage {
  protected readonly path = '/premium';
  readonly start: Locator;
  readonly cancel: Locator;

  constructor(page: Page) {
    super(page);
    this.start = page.locator('#btn-start-premium');
    this.cancel = page.locator('#btn-cancel-premium');
  }

  async isLoaded(): Promise<void> {
    await expect(this.page.getByRole('heading', { name: 'Her Aura Premium' })).toBeVisible();
  }
}

export class LoadPage extends BasePage {
  protected readonly path = '/load';
  readonly mood: Locator;
  readonly stress: Locator;
  readonly energy: Locator;
  readonly handoff: Locator;
  readonly save: Locator;
  readonly avgStress: Locator;
  readonly topAreas: Locator;
  readonly suggestions: Locator;
  readonly supportLine: Locator;

  constructor(page: Page) {
    super(page);
    this.mood = page.locator('#mood');
    this.stress = page.locator('#stress');
    this.energy = page.locator('#energy');
    this.handoff = page.locator('#handoff');
    this.save = page.locator('#btn-save-load');
    this.avgStress = page.locator('#avg-stress');
    this.topAreas = page.getByTestId('top-area');
    this.suggestions = page.getByTestId('load-suggestion');
    this.supportLine = page.locator('#support-line');
  }

  async isLoaded(): Promise<void> {
    await expect(this.page.getByRole('heading', { name: 'Emotional load' })).toBeVisible();
  }

  async checkIn(c: { mood: number; stress: number; energy: number; areas?: string[]; handoff?: string }): Promise<void> {
    await this.mood.fill(String(c.mood));
    await this.stress.fill(String(c.stress));
    await this.energy.fill(String(c.energy));
    for (const area of c.areas ?? []) await this.page.locator(`#area-${area}`).check();
    if (c.handoff) await this.handoff.fill(c.handoff);
    await this.save.click();
  }
}
