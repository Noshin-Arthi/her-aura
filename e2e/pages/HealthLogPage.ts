import { expect, Locator, Page } from '@playwright/test';
import { BasePage } from './BasePage';

export type IssueCategory =
  | 'headache' | 'toothache' | 'skin_rash' | 'hair_fall' | 'fatigue'
  | 'fever' | 'stomach' | 'joint_pain' | 'low_mood' | 'other';

export interface HealthIssue {
  category: IssueCategory;
  severity: number;   // 1-10
  notes?: string;
}

export class HealthLogPage extends BasePage {
  protected readonly path = '/health';
  readonly severity: Locator;
  readonly detailsToggle: Locator;
  readonly notes: Locator;
  readonly save: Locator;

  constructor(page: Page) {
    super(page);
    this.severity = page.locator('#severity');
    this.detailsToggle = page.getByText('Add details (optional)');
    this.notes = page.locator('#health_notes');
    this.save = page.locator('#btn-save-issue');
  }

  async isLoaded(): Promise<void> {
    await expect(this.page.getByRole('heading', { name: 'How are you feeling?' })).toBeVisible();
  }

  async setSeverity(level: number): Promise<void> {
    await this.severity.fill(String(level));
  }

  async logIssue(issue: HealthIssue): Promise<void> {
    await this.page.locator(`#issue-${issue.category}`).check();
    await this.setSeverity(issue.severity);
    if (issue.notes) {
      await this.detailsToggle.click();
      await this.notes.fill(issue.notes);
    }
    await this.save.click();
  }
}
