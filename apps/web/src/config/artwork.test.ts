import { describe, expect, it } from 'vitest';
import { content } from '../data';
import { artworkSource } from './artwork';

describe('presentation artwork transport', () => {
  it('keeps the validated product asset path intact', () => {
    expect(artworkSource(content.assets.hero)).toBe(content.assets.hero);
  });
  it('resolves separately embedded PNG data without modifying product data', () => {
    const embedded = 'data:image/png;base64,dGVzdA==';
    expect(artworkSource(content.assets.hero, embedded)).toBe(embedded);
    expect(content.assets.hero).toMatch(/^\.\/[a-z0-9-]+\.png$/);
  });
  it('rejects executable or malformed embedded values', () => {
    for (const embedded of [
      'javascript:alert(1)',
      'data:text/html;base64,dGVzdA==',
      'data:image/png;base64,<script>',
    ]) {
      expect(artworkSource(content.assets.hero, embedded)).toBe(content.assets.hero);
    }
  });
});
