import { describe, expect, it } from 'vitest';
import data from './core-console.json';
import { parseCoreConsole } from './core-console-contract';

describe('maintained core interface contract', () => {
  it('keeps navigation identity when business-facing labels change', () => {
    const changed = {
      ...data,
      navigation: data.navigation.map((entry) => ({
        ...entry,
        label: `Translated ${entry.label}`,
      })),
    };
    const parsed = parseCoreConsole(changed);
    expect(parsed.navigation.map((entry) => entry.id)).toEqual(
      data.navigation.map((entry) => entry.id),
    );
    expect(parsed.navigation[0]?.label).toContain('Translated');
  });
  it('rejects missing, empty, duplicate and unknown maintained content', () => {
    const missing: Record<string, unknown> = { ...data };
    delete missing.title;
    for (const invalid of [
      missing,
      { ...data, title: '' },
      { ...data, unexpected: 'unsupported content' },
      { ...data, navigation: [data.navigation[0], data.navigation[0]] },
      { ...data, fieldLabels: { ...data.fieldLabels, name: '' } },
    ])
      expect(() => parseCoreConsole(invalid)).toThrow();
  });
});
