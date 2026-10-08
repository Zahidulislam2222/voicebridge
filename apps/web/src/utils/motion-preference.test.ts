import { afterEach, describe, expect, it, vi } from 'vitest';
import { getMotionPreference, subscribeMotionPreference } from './motion-preference';
afterEach(() => vi.unstubAllGlobals());
describe('live reduced motion browser preference', () => {
  it('reads both current browser preference values', () => {
    const media = { matches: true };
    vi.stubGlobal('window', { matchMedia: () => media });
    expect(getMotionPreference()).toBe(true);
    media.matches = false;
    expect(getMotionPreference()).toBe(false);
  });
  it('subscribes to preference changes and removes the exact listener on cleanup', () => {
    const media = { addEventListener: vi.fn(), removeEventListener: vi.fn() };
    vi.stubGlobal('window', { matchMedia: () => media });
    const changed = vi.fn();
    const unsubscribe = subscribeMotionPreference(changed);
    expect(media.addEventListener).toHaveBeenCalledWith('change', changed);
    unsubscribe();
    expect(media.removeEventListener).toHaveBeenCalledWith('change', changed);
  });
});
