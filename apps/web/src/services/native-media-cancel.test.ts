import { describe, expect, it, vi } from 'vitest';

const sdk = vi.hoisted(() => ({
  retellStart: vi.fn(),
  retellStop: vi.fn(),
  vapiReconnect: vi.fn(),
  vapiStop: vi.fn().mockResolvedValue(undefined),
}));

vi.mock('retell-client-js-sdk', () => ({
  RetellWebClient: class {
    on() {
      return this;
    }
    startCall = sdk.retellStart;
    stopCall = sdk.retellStop;
  },
}));

vi.mock('@vapi-ai/web', () => ({
  default: class {
    on() {
      return this;
    }
    reconnect = sdk.vapiReconnect;
    stop = sdk.vapiStop;
  },
}));

import {
  attachOwnedMedia,
  joinNativeMedia,
  NativeMediaLifecycle,
  parseNativeGrant,
  revokeMediaOnOwnerDenial,
} from './native-media';
import { CoreRequestError } from './core-client';

describe('in-flight SDK cancellation', () => {
  it.each(['authorization_required', 'session_expired', 'identity_not_allowed', 'role_denied'])(
    'stops Retell during join when the owner session fails with %s',
    async (code) => {
      let finish!: () => void;
      sdk.retellStart.mockImplementationOnce(
        () =>
          new Promise<void>((resolve) => {
            finish = resolve;
          }),
      );
      const owner = new NativeMediaLifecycle();
      const grant = parseNativeGrant({
        provider: 'retell',
        callId: 'test-call',
        accessToken: 'test-media-token-123456',
        transport: 'gateway',
        iceServers: [],
        expiresAt: Date.now() + 60000,
      });
      const pending = joinNativeMedia(grant, vi.fn(), vi.fn(), owner.signal);
      await vi.waitFor(() => expect(sdk.retellStart).toHaveBeenCalled());
      expect(revokeMediaOnOwnerDenial(owner, new CoreRequestError(code))).toBe(true);
      expect(sdk.retellStop).toHaveBeenCalled();
      finish();
      await expect(pending).rejects.toThrow('media_join_failed');
    },
  );

  it.each(['authorization_required', 'session_expired', 'identity_not_allowed', 'role_denied'])(
    'prevents a late create from joining after %s',
    async (code) => {
      let finish!: (value: string) => void;
      const create = new Promise<string>((resolve) => {
        finish = resolve;
      });
      const owner = new NativeMediaLifecycle();
      const join = vi.fn(async () => ({ stop: vi.fn(async () => {}) }));
      const pending = attachOwnedMedia(owner, () => create, join);
      expect(revokeMediaOnOwnerDenial(owner, new CoreRequestError(code))).toBe(true);
      finish('test-grant');
      await expect(pending).resolves.toBe(false);
      expect(join).not.toHaveBeenCalled();
    },
  );

  it.each(['authorization_required', 'session_expired', 'identity_not_allowed', 'role_denied'])(
    'stops active media after %s',
    async (code) => {
      const owner = new NativeMediaLifecycle();
      const stop = vi.fn(async () => {});
      await owner.activate({ stop });
      expect(revokeMediaOnOwnerDenial(owner, new CoreRequestError(code))).toBe(true);
      await vi.waitFor(() => expect(stop).toHaveBeenCalledOnce());
      expect(owner.isOpen()).toBe(false);
    },
  );

  it('stops Vapi immediately when the owning page closes during reconnect', async () => {
    vi.stubGlobal('window', { location: { origin: 'https://voicebridge.test' } });
    let finish!: () => void;
    sdk.vapiReconnect.mockImplementationOnce(
      () =>
        new Promise<void>((resolve) => {
          finish = resolve;
        }),
    );
    const owner = new NativeMediaLifecycle();
    const grant = parseNativeGrant({
      provider: 'vapi',
      callId: 'test-call',
      webCallUrl: 'https://test.daily.co/room',
      expiresAt: Date.now() + 60000,
    });
    const pending = joinNativeMedia(grant, vi.fn(), vi.fn(), owner.signal);
    await vi.waitFor(() => expect(sdk.vapiReconnect).toHaveBeenCalled());
    owner.close();
    expect(sdk.vapiStop).toHaveBeenCalled();
    finish();
    await expect(pending).rejects.toThrow('media_join_failed');
    vi.unstubAllGlobals();
  });
});
