import { describe, expect, it } from 'vitest';
import { normalizeIntake } from './intake';
import { settingsDefaults } from '../config/settings';
import { site } from '../data/site';
import { content } from '../data';
const form = {
  name: ' Client Review ',
  email: 'review@example.test',
  company: ' Northline ',
  industry: site.industries[0]!.id,
  voice: content.voiceProfiles[0]!.id,
  message: ' Appointment enquiries ',
  team: site.teamChoices[0]!,
};
const rules = {
  maxTextLength: settingsDefaults.maxTextLength,
  onboarding: false,
  industryIds: site.industries.map((item) => item.id),
  voiceIds: content.voiceProfiles.map((item) => item.id),
  teamChoices: site.teamChoices,
};
describe('local intake validation', () => {
  it('normalizes review details without sending or persisting them', () => {
    const normalized = normalizeIntake(form, rules);
    expect(normalized.name).toBe('Client Review');
    expect(normalized.company).toBe('Northline');
    expect(normalized.message).toBe('Appointment enquiries');
    expect(form.name).toBe(' Client Review ');
  });
  for (const key of ['name', 'company', 'message'] as const)
    it(`rejects whitespace-only ${key}`, () => {
      expect(() => normalizeIntake({ ...form, [key]: '   ' }, rules)).toThrow();
    });
  it('rejects invalid email, unknown preferences, controls and excessive text', () => {
    for (const changed of [
      { email: 'invalid' },
      { voice: 'unknown' },
      { industry: 'unknown' },
      { team: 'unknown' },
      { name: 'name\u0000' },
      { company: 'x'.repeat(rules.maxTextLength + 1) },
    ])
      expect(() => normalizeIntake({ ...form, ...changed }, rules)).toThrow();
  });
  it('allows an onboarding request without a contact message while validating preferences', () => {
    expect(normalizeIntake({ ...form, message: '' }, { ...rules, onboarding: true }).message).toBe(
      '',
    );
  });
});
