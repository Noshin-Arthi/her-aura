import { faker } from '@faker-js/faker';

export interface TestUser {
  fullName: string;
  email: string;
  password: string;
}

/** A unique, fake user per call. Never use real patient data in tests. */
export function newUser(): TestUser {
  const first = faker.person.firstName('female');
  const last = faker.person.lastName();
  return {
    fullName: `${first} ${last}`,
    email: `${first}.${last}.${faker.string.alphanumeric(6)}@example.com`.toLowerCase(),
    password: faker.internet.password({ length: 12 }) + 'A1!',
  };
}

export function isoDaysAgo(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  // Local date, not UTC, to match the server's date.today().
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}
