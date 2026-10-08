import { afterEach, describe, expect, it, vi } from 'vitest';
import { z } from './schema-runtime';

afterEach(() => vi.restoreAllMocks());
describe('CSP-compatible schema initialization', () => {
  it('disables runtime compilation before consumer schemas are constructed', () => {
    expect(z.config().jitless).toBe(true);
  });
  it('validates and rejects input without attempting dynamic Function construction', () => {
    const dynamicCode = vi.spyOn(globalThis, 'Function').mockImplementation(() => {
      throw new Error('Dynamic compilation is forbidden');
    });
    const schema = z.object({ name: z.string().min(1), enabled: z.boolean() });
    expect(schema.parse({ name: 'Northline', enabled: true })).toEqual({
      name: 'Northline',
      enabled: true,
    });
    expect(() => schema.parse({ name: '', enabled: true })).toThrow();
    expect(dynamicCode).not.toHaveBeenCalled();
  });
});
