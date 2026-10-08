import { readFileSync, readdirSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { describe, expect, it } from 'vitest';
import { createSettings, settingsDefaults } from './settings';

function sources(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) =>
    entry.isDirectory()
      ? sources(join(directory, entry.name))
      : entry.name.match(/\.(ts|tsx)$/) && !/\.test\.tsx?$/.test(entry.name)
        ? [readFileSync(join(directory, entry.name), 'utf8')]
        : [],
  );
}
describe('configuration boundary', () => {
  it('owns defaults and rejects invalid public settings', () => {
    expect(createSettings()).toEqual(settingsDefaults);
    expect(() => createSettings({ VITE_SIMULATION_DELAY_MS: '-1' })).toThrow();
    expect(() => createSettings({ VITE_TIMEZONE: 'invalid' })).toThrow();
    expect(createSettings({ VITE_SIMULATION_DELAY_MS: '5' }).simulationDelayMs).toBe(5);
  });
  it('documents every consumed environment variable', () => {
    const config = readFileSync(resolve('src/config/settings.ts'), 'utf8');
    const tooling = readFileSync(resolve('../../tools/development-settings.mjs'), 'utf8');
    const example = readFileSync(resolve('../../.env.example'), 'utf8');
    const names = [...new Set((config + tooling).match(/VITE_[A-Z_]+/g))];
    for (const name of names) expect(example).toContain(name + '=');
  });
  it('keeps provider secrets and network endpoints out of application source', () => {
    const source = sources(resolve('src')).join('\n');
    expect(source).not.toMatch(/https?:\/\//);
    expect(source).not.toMatch(/-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/);
    expect(source).not.toMatch(/(?:sk-proj-|sk-or-v1-)[A-Za-z0-9_-]{12,}/);
    const business = sources(resolve('src'))
      .filter((text) => !text.includes('export class CoreClient'))
      .join('\n');
    expect(business).not.toMatch(/\b(?:fetch|XMLHttpRequest)\s*\(/);
    const client = readFileSync(resolve('src/services/core-client.ts'), 'utf8');
    expect(client).toContain('settings.coreApiUrl + path');
    expect(client).toContain("credentials: settings.coreSessionAuth ? 'same-origin' : 'omit'");
  });
  it('reads environment only at the typed boundary', () => {
    const files = sources(resolve('src')).filter(
      (text) => !text.includes('export const settings = createSettings'),
    );
    for (const text of files) expect(text).not.toContain('import.meta.env');
  });
  it('serves licensed typography locally without third-party style requests', () => {
    const css = readFileSync(resolve('src/styles.css'), 'utf8');
    expect(css).not.toMatch(/@import|https?:\/\//);
    const fonts = [...css.matchAll(/url\('\/fonts\/([^']+)'\)/g)];
    expect(fonts).toHaveLength(2);
    for (const font of fonts) {
      if (!font[1]) throw new Error('Missing font filename');
      const bytes = readFileSync(resolve('public/fonts', font[1]));
      expect(bytes.subarray(0, 4).toString()).toBe('wOF2');
    }
    for (const license of ['DM-Sans-OFL.txt', 'Manrope-OFL.txt']) {
      expect(readFileSync(resolve('public/fonts', license), 'utf8')).toContain(
        'SIL OPEN FONT LICENSE',
      );
    }
  });
});
