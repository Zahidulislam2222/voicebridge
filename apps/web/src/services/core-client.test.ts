import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  agentDraft,
  bookingNotice,
  CoreClient,
  CoreRequestError,
  followupDeliveryNotice,
  ownerSessionDenied,
} from './core-client';
import copy from '../data/core-console';
import { createSettings, settings } from '../config/settings';

vi.mock(import('../config/settings'), async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    settings: actual.createSettings({ VITE_CORE_API_URL: 'http://127.0.0.1:18082' }),
  };
});

afterEach(() => vi.unstubAllGlobals());
describe('core boundary regressions', () => {
  it('rejects a non-JSON response even with a safe filename', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response('<html>private</html>', {
          headers: {
            'Content-Type': 'text/html',
            'Content-Disposition': 'attachment; filename="test.json"',
          },
        }),
      ),
    );
    await expect(
      new CoreClient('test-key').download('/api/exports/snapshot', new AbortController().signal),
    ).rejects.toThrow('invalid export response');
  });
  it('uses the authenticated JSON POST boundary for a safe attachment', async () => {
    if (!settings.coreApiUrl) throw new Error('Test API URL required');
    const fetcher = vi.fn().mockResolvedValue(
      new Response('{"schema_version":1}', {
        headers: {
          'Content-Type': 'application/json',
          'Content-Disposition': 'attachment; filename="test-export.json"',
        },
      }),
    );
    vi.stubGlobal('fetch', fetcher);
    const result = await new CoreClient('test-key', 'test-csrf').download(
      '/api/exports/snapshot',
      new AbortController().signal,
    );
    expect(await result.blob.text()).toBe('{"schema_version":1}');
    expect(result.filename).toBe('test-export.json');
    expect(fetcher.mock.calls[0]?.[1]).toMatchObject({
      method: 'POST',
      body: '{"format":"json"}',
      cache: 'no-store',
      redirect: 'error',
    });
  });
  it.each([
    'attachment; filename="../test.json"',
    'inline; filename="test.json"',
    'attachment; filename="test.html"',
  ])('rejects unsafe download metadata %s', async (disposition) => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response('{}', {
          headers: { 'Content-Type': 'application/json', 'Content-Disposition': disposition },
        }),
      ),
    );
    await expect(
      new CoreClient('test-key').download('/api/exports/snapshot', new AbortController().signal),
    ).rejects.toThrow('invalid export response');
  });
  it('keeps pending calendar changes visibly unverified', () => {
    for (const action of ['create', 'reschedule', 'cancel'] as const) {
      expect(bookingNotice('pending', action)).toBe(copy.pending);
      expect(bookingNotice('reschedule_pending', action)).toBe(copy.pending);
      expect(bookingNotice('cancel_pending', action)).toBe(copy.pending);
    }
    expect(bookingNotice('cancelled', 'cancel')).toBe(copy.bookingCancelled);
    expect(bookingNotice('confirmed', 'reschedule')).toBe(copy.bookingRescheduled);
  });
  it('uses the historical receipt mode, never the current transport setting', () => {
    expect(followupDeliveryNotice('capture')).toBe(copy.captureDelivery);
    expect(followupDeliveryNotice('smtp')).toBe(copy.externalDelivery);
    expect(followupDeliveryNotice(null)).toBe(copy.unknownDelivery);
  });
  it('distinguishes owner-session denial from a transient provider failure', () => {
    for (const code of [
      'authorization_required',
      'session_expired',
      'invalid_session',
      'identity_not_allowed',
      'role_denied',
      'csrf_required',
      'untrusted_origin',
      'native_owner_required',
    ]) {
      expect(ownerSessionDenied(new CoreRequestError(code))).toBe(true);
    }
    expect(ownerSessionDenied(new CoreRequestError('native_profile_drift'))).toBe(false);
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
