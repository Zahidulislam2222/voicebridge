import { describe, it, expect } from 'vitest';
import content from './content.json';
import demo from './demo.json';
import { validateContent, validateFixture } from './contracts';

describe('maintained data contracts', () => {
  it('rejects missing required interface and action text', () => {
    for (const group of [
      'labels',
      'messages',
      'fixedLabels',
      'usageUnits',
      'auditActions',
    ] as const) {
      const copy = structuredClone(content);
      const values = copy[group] as Record<string, string>;
      const key = Object.keys(values)[0];
      if (!key) throw new Error('Missing contract fixture key');
      delete values[key];
      expect(() => validateContent(copy)).toThrow();
    }
  });
  it('accepts the coherent synthetic workspace', () => {
    expect(() => validateFixture(demo, validateContent(content))).not.toThrow();
  });
  it('rejects invalid job references', () => {
    const input = structuredClone(demo);
    input.jobs[0]!.appointmentId = 'missing';
    expect(() => validateFixture(input, content)).toThrow('Invalid job reference');
  });
  it('rejects duplicate IDs and broken reciprocal links', () => {
    const input = structuredClone(demo);
    input.calls[1]!.id = input.calls[0]!.id;
    expect(() => validateFixture(input, content)).toThrow();
    const broken = structuredClone(demo);
    broken.appointments[0]!.contactId = 'ct-2';
    expect(() => validateFixture(broken, content)).toThrow();
  });
  it('rejects invalid dates, states and missing evaluation mappings', () => {
    const badDate = structuredClone(demo);
    badDate.appointments[0]!.date = '2026-11-31T09:00';
    expect(() => validateFixture(badDate, content)).toThrow();
    const badStatus = structuredClone(demo);
    Object.assign(badStatus.jobs[0]!, { status: 'Unknown' });
    expect(() => validateFixture(badStatus, content)).toThrow();
    const copy = structuredClone(content);
    delete (copy.evaluationResults as Record<string, string>)['ev-1'];
    expect(() => validateFixture(demo, copy)).toThrow('Missing evaluation result mapping');
  });
  it('rejects incomplete or duplicate navigation and unsafe asset paths', () => {
    const copy = structuredClone(content);
    copy.nav.pop();
    expect(() => validateContent(copy)).toThrow();
    const duplicate = structuredClone(content);
    duplicate.nav[1]!.id = duplicate.nav[0]!.id;
    expect(() => validateContent(duplicate)).toThrow();
    const unsafe = structuredClone(content);
    unsafe.assets.hero = '../../.env';
    expect(() => validateContent(unsafe)).toThrow();
  });
});
