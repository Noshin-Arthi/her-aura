import { expect, Locator, Page } from '@playwright/test';
import { BasePage } from './BasePage';

export type Flow = 'none' | 'light' | 'medium' | 'heavy';
export type Symptom = 'pelvic_or_abdominal_pain' | 'bloating' | 'early_fullness' | 'urinary_urgency';

export interface DailyLog {
  date?: string;          // yyyy-mm-dd, defaults to today
  flow?: Flow;
  pain?: number;          // 0-10
  symptoms?: Symptom[];
  notes?: string;
}

export class SymptomLogPage extends BasePage {
  protected readonly path = '/log';
  readonly date: Locator;
  readonly pain: Locator;
  readonly notesToggle: Locator;
  readonly notes: Locator;
  readonly save: Locator;
  readonly sameAsYesterday: Locator;

  constructor(page: Page) {
    super(page);
    this.date = page.locator('#log_date');
    this.pain = page.locator('#pain_level');
    this.notesToggle = page.getByText('Add a note (optional)');
    this.notes = page.locator('#notes');
    this.save = page.locator('#btn-save-log');
    this.sameAsYesterday = page.locator('#btn-same-as-yesterday');
  }

  async isLoaded(): Promise<void> {
    await expect(this.page.getByRole('heading', { name: 'Daily log' })).toBeVisible();
  }

  flowChip(flow: Flow): Locator {
    return this.page.locator(`#flow-${flow}`);
  }

  async setPain(level: number): Promise<void> {
    await this.pain.fill(String(level));
  }

  async fillLog(log: DailyLog): Promise<void> {
    if (log.date) await this.date.fill(log.date);
    if (log.flow) await this.flowChip(log.flow).check();
    if (log.pain !== undefined) await this.setPain(log.pain);
    for (const symptom of log.symptoms ?? []) {
      await this.page.locator(`#${symptom}`).check();
    }
    if (log.notes) {
      await this.notesToggle.click();
      await this.notes.fill(log.notes);
    }
  }

  async submitLog(log: DailyLog): Promise<void> {
    await this.fillLog(log);
    await this.save.click();
  }

  /** True when the browser's own validation (e.g. max date) would block submitting the date. */
  async dateIsInvalid(): Promise<boolean> {
    return this.date.evaluate((el) => !(el as HTMLInputElement).checkValidity());
  }
}
