import { describe, expect, it } from 'vitest';
import { attachOwnedMedia, NativeMediaLifecycle, parseNativeGrant } from './native-media';

describe('owner media grants', () => {
  const future = Date.now() + 60000;

  it('accepts only a minimized Retell media grant', () => {
    const grant = {
      provider: 'retell',
      callId: 'test-call',
      accessToken: 'test-media-token-123456',
      transport: 'gateway',
      iceServers: [],
      expiresAt: future,
    };
    expect(parseNativeGrant(grant)).toEqual(grant);
    expect(() => parseNativeGrant({ ...grant, capability: 'test-business-capability' })).toThrow();
    expect(() => parseNativeGrant({ ...grant, expiresAt: Date.now() - 1 })).toThrow();
    expect(() => parseNativeGrant({ ...grant, transport: 'livekit' })).toThrow();
  });

  it('accepts only an HTTPS Vapi existing-call join URL', () => {
    const grant = {
      provider: 'vapi',
      callId: 'test-call',
      webCallUrl: 'https://test.daily.co/room',
      callToken: 'test-media-token',
      expiresAt: future,
    };
    expect(parseNativeGrant(grant)).toEqual(grant);
    expect(() => parseNativeGrant({ ...grant, webCallUrl: 'http://test.daily.co/room' })).toThrow();
    expect(() => parseNativeGrant({ ...grant, privateKey: 'test-account-key' })).toThrow();
  });
});

describe('owned media lifetime', () => {
  it('does not join when creation resolves after the owner page closes', async () => {
    let resolveCreate!: (value: string) => void;
    const create = new Promise<string>((resolve) => {
      resolveCreate = resolve;
    });
    const lifecycle = new NativeMediaLifecycle();
    let joins = 0;
    const pending = attachOwnedMedia(
      lifecycle,
      () => create,
      async () => {
        joins += 1;
        return { stop: async () => undefined };
      },
    );
    lifecycle.close();
    resolveCreate('test-bound-call');
    expect(await pending).toBe(false);
    expect(joins).toBe(0);
  });

  it('stops a join that resolves after the owner page closes', async () => {
    let resolveJoin!: (value: { stop: () => Promise<void> }) => void;
    const join = new Promise<{ stop: () => Promise<void> }>((resolve) => {
      resolveJoin = resolve;
    });
    const lifecycle = new NativeMediaLifecycle();
    let stops = 0;
    const pending = attachOwnedMedia(
      lifecycle,
      async () => 'test-bound-call',
      async () => join,
    );
    await Promise.resolve();
    lifecycle.close();
    resolveJoin({
      stop: async () => {
        stops += 1;
      },
    });
    expect(await pending).toBe(false);
    expect(stops).toBe(1);
  });
});
