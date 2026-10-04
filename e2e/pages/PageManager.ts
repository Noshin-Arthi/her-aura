import { Page } from '@playwright/test';
import { LoginPage, RegisterPage } from './AuthPages';
import { DashboardPage } from './DashboardPage';
import { SymptomLogPage } from './SymptomLogPage';
import { DoctorsPage } from './DoctorsPage';
import { AppointmentsPage } from './AppointmentsPage';
import { HealthLogPage } from './HealthLogPage';
import { HomePage } from './HomePage';
import { MindPage, SleepPage } from './WellbeingPages';
import { AdPage, LearnPage, LoadPage, PremiumPage } from './LearnPages';

/** One entry point to every page object, so tests never construct pages or touch locators. */
export class PageManager {
  readonly register: RegisterPage;
  readonly login: LoginPage;
  readonly dashboard: DashboardPage;
  readonly symptomLog: SymptomLogPage;
  readonly doctors: DoctorsPage;
  readonly appointments: AppointmentsPage;
  readonly healthLog: HealthLogPage;
  readonly home: HomePage;
  readonly sleep: SleepPage;
  readonly mind: MindPage;
  readonly learn: LearnPage;
  readonly ad: AdPage;
  readonly premium: PremiumPage;
  readonly load: LoadPage;

  constructor(page: Page) {
    this.register = new RegisterPage(page);
    this.login = new LoginPage(page);
    this.dashboard = new DashboardPage(page);
    this.symptomLog = new SymptomLogPage(page);
    this.doctors = new DoctorsPage(page);
    this.appointments = new AppointmentsPage(page);
    this.healthLog = new HealthLogPage(page);
    this.home = new HomePage(page);
    this.sleep = new SleepPage(page);
    this.mind = new MindPage(page);
    this.learn = new LearnPage(page);
    this.ad = new AdPage(page);
    this.premium = new PremiumPage(page);
    this.load = new LoadPage(page);
  }
}
