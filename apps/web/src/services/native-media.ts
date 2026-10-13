/** Media-only joins. Account-level call creation and binding happen on the server. */
import Vapi from '@vapi-ai/web';
import { RetellWebClient } from 'retell-client-js-sdk';
import { z } from '../config/schema-runtime';
import { ownerSessionDenied } from './core-client';

const iceServer = z
  .object({
    urls: z.union([z.string(), z.array(z.string())]),
    username: z.string().optional(),
    credential: z.string().optional(),
  })
  .strict();
const retellGrant = z
  .object({
    provider: z.literal('retell'),
    callId: z.string().min(1),
    accessToken: z.string().min(16),
    transport: z.literal('gateway'),
    iceServers: z.array(iceServer),
    expiresAt: z.number().int().positive(),
  })
  .strict();
const vapiGrant = z
  .object({
    provider: z.literal('vapi'),
    callId: z.string().min(1),
    webCallUrl: z.url().refine((value) => new URL(value).protocol === 'https:'),
    callToken: z.string().optional(),
    expiresAt: z.number().int().positive(),
  })
  .strict();
const grantSchema = z.discriminatedUnion('provider', [retellGrant, vapiGrant]);
export type NativeGrant = z.infer<typeof grantSchema>;
export type NativeMedia = { stop: () => Promise<void> };

/** Owns a joined session across page cleanup and asynchronous media joins. */
export class NativeMediaLifecycle {
  private closed = false;
  private active: NativeMedia | null = null;
  private controller = new AbortController();

  get signal(): AbortSignal {
    return this.controller.signal;
  }

  isOpen(): boolean {
    return !this.closed;
  }

  hasActive(): boolean {
    return this.active !== null;
  }

  async activate(media: NativeMedia): Promise<boolean> {
    if (this.closed) {
      await media.stop();
      return false;
    }
    this.active = media;
    return true;
  }

  take(): NativeMedia | null {
    const active = this.active;
    this.active = null;
    return active;
  }

  close(): void {
    this.closed = true;
    this.controller.abort();
    const active = this.take();
    if (active) void active.stop().catch(() => undefined);
  }
}

/** A denied owner session aborts pending creation/join and stops joined media. */
export function revokeMediaOnOwnerDenial(
  lifecycle: NativeMediaLifecycle,
  reason: unknown,
): boolean {
  if (!ownerSessionDenied(reason)) return false;
  lifecycle.close();
  return true;
}

/** Never join a server-created call after its owning page or session closes. */
export async function attachOwnedMedia<T>(
  lifecycle: NativeMediaLifecycle,
  create: () => Promise<T>,
  join: (result: T) => Promise<NativeMedia | null>,
): Promise<boolean> {
  const result = await create();
  if (!lifecycle.isOpen()) return false;
  const media = await join(result);
  if (!media) return false;
  return lifecycle.activate(media);
}

export function parseNativeGrant(value: unknown): NativeGrant {
  const grant = grantSchema.parse(value);
  if (grant.expiresAt <= Date.now()) throw new Error('media_grant_expired');
  return grant;
}

export async function joinNativeMedia(
  grant: NativeGrant,
  onEnded: () => void,
  onError: () => void,
  signal: AbortSignal,
): Promise<NativeMedia> {
  if (grant.expiresAt <= Date.now()) throw new Error('media_grant_expired');
  if (signal.aborted) throw new Error('media_join_cancelled');
  if (grant.provider === 'retell') {
    const media = new RetellWebClient();
    media.on('call_ended', onEnded);
    media.on('error', onError);
    const cancel = () => media.stopCall();
    signal.addEventListener('abort', cancel, { once: true });
    try {
      if (signal.aborted) throw new Error('media_join_cancelled');
      await media.startCall({
        callId: grant.callId,
        accessToken: grant.accessToken,
        transport: grant.transport,
        iceServers: grant.iceServers,
      });
      if (signal.aborted) throw new Error('media_join_cancelled');
    } catch {
      media.stopCall();
      throw new Error('media_join_failed');
    } finally {
      signal.removeEventListener('abort', cancel);
    }
    return { stop: async () => media.stopCall() };
  }
  // reconnect joins an existing server-created call; start() would create another call.
  const media = new Vapi('media-only', window.location.origin + '/engine-api', {
    avoidEval: true,
  });
  media.on('call-end', onEnded);
  media.on('error', onError);
  const cancel = () => void media.stop().catch(() => undefined);
  signal.addEventListener('abort', cancel, { once: true });
  const existing = {
    id: grant.callId,
    webCallUrl: grant.webCallUrl,
    ...(grant.callToken ? { transport: { callToken: grant.callToken } } : {}),
  } as unknown as Parameters<typeof media.reconnect>[0];
  try {
    if (signal.aborted) throw new Error('media_join_cancelled');
    await media.reconnect(existing);
    if (signal.aborted) throw new Error('media_join_cancelled');
  } catch {
    await media.stop().catch(() => undefined);
    throw new Error('media_join_failed');
  } finally {
    signal.removeEventListener('abort', cancel);
  }
  return { stop: () => media.stop() };
}
