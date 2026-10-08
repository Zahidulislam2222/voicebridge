import { afterEach, describe, expect, it, vi } from 'vitest';
import { agentDraft, bookingNotice, CoreClient } from './core-client';
import copy from '../data/core-console';
import { createSettings, settings } from '../config/settings';

afterEach(() => vi.unstubAllGlobals());
describe('core boundary regressions', () => {
  it('keeps pending calendar changes visibly unverified', () => {
    for (const action of ['create', 'reschedule', 'cancel'] as const) {
      expect(bookingNotice('pending', action)).toBe(copy.pending);
      expect(bookingNotice('reschedule_pending', action)).toBe(copy.pending);
      expect(bookingNotice('cancel_pending', action)).toBe(copy.pending);
    }
    expect(bookingNotice('cancelled', 'cancel')).toBe(copy.bookingCancelled);
    expect(bookingNotice('confirmed', 'reschedule')).toBe(copy.bookingRescheduled);
  });
  it('serializes the exact agent request without response-only revision', () => {
    const draft = agentDraft({
      name: 'Test agent',
      greeting: 'Hello',
      handoff: 'Ask the team',
      voice_id: 'test-voice',
      revision: 3,
    });
    expect(draft.expected_revision).toBe(3);
    expect(draft).not.toHaveProperty('revision');
  });
  it('rejects a non-loopback engine URL', () => {
    expect(() => createSettings({ VITE_CORE_API_URL: 'https://provider.invalid' })).toThrow();
    expect(() => createSettings({ VITE_CORE_REQUEST_TIMEOUT_MS: '0' })).toThrow();
  });
  it('requires the same-origin gateway for authenticated sessions', () => {
    expect(() =>
      createSettings({
        VITE_CORE_SESSION_AUTH: 'true',
        VITE_CORE_API_URL: 'http://localhost:18080',
      }),
    ).toThrow();
    expect(
      createSettings({ VITE_CORE_SESSION_AUTH: 'true', VITE_CORE_API_URL: '/engine-api' })
        .coreSessionAuth,
    ).toBe(true);
  });
  it('uses an abortable deadline and never persists the operator credential', async () => {
    if (!settings.coreApiUrl) return;
    const fetcher = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify({ ok: true }), { status: 200 }));
    vi.stubGlobal('fetch', fetcher);
    await new CoreClient('test-key').request('/api/state');
    const options = fetcher.mock.calls[0]?.[1] as RequestInit;
    expect(options.signal).toBeInstanceOf(AbortSignal);
    expect(options.credentials).toBe('omit');
    expect(options.redirect).toBe('error');
  });
});
