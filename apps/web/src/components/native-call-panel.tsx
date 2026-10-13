import { useEffect, useRef, useState } from 'react';
import data from '../data/native-call.json';
import { z } from '../config/schema-runtime';
import { settings } from '../config/settings';
import { CoreClient, CoreRequestError } from '../services/core-client';
import {
  attachOwnedMedia,
  joinNativeMedia,
  NativeMediaLifecycle,
  parseNativeGrant,
  revokeMediaOnOwnerDenial,
} from '../services/native-media';
import { Button } from './ui';

const copy = z
  .object({
    title: z.string(),
    intro: z.string(),
    retell: z.string(),
    provider: z.string(),
    vapi: z.string(),
    start: z.string(),
    stop: z.string(),
    idle: z.string(),
    starting: z.string(),
    connected: z.string(),
    ended: z.string(),
    permission: z.string(),
    joinError: z.string(),
    unavailable: z.string(),
    ownerOnly: z.string(),
    statusUnavailable: z.string(),
    manualRecovery: z.string(),
    resumeExisting: z.string(),
    operation: z.string(),
    limits: z.string(),
    entitlement: z.string(),
    verifiedAt: z.string(),
    unverified: z.string(),
    availability: z.string(),
    failures: z.record(z.string(), z.string()),
  })
  .strict()
  .parse(data);

type Provider = 'retell' | 'vapi';
type State = 'idle' | 'starting' | 'connected' | 'ended' | 'error';
type NativeStatus = {
  operations: {
    operation_id: string;
    provider: Provider;
    state: string;
    created_at: string;
    recovery: string;
  }[];
  limits: { max_seconds: number; max_concurrent: number };
  entitlements: Record<Provider, { state: string; verified_at: string | null }>;
};

export function NativeCallPanel({
  client,
  available,
  owner,
}: {
  client: CoreClient;
  available: boolean;
  owner: boolean;
}) {
  const [provider, setProvider] = useState<Provider>('retell');
  const [state, setState] = useState<State>('idle');
  const [message, setMessage] = useState(copy.idle);
  const [status, setStatus] = useState<NativeStatus | null>(null);
  const [sessionLost, setSessionLost] = useState(false);
  const operation = useRef<string>(crypto.randomUUID());
  const media = useRef(new NativeMediaLifecycle());
  const starting = useRef(false);

  useEffect(() => {
    if (!media.current.isOpen()) media.current = new NativeMediaLifecycle();
    const current = media.current;
    return () => {
      current.close();
    };
  }, []);

  useEffect(() => {
    if (!available || !owner) media.current.close();
  }, [available, owner]);

  useEffect(() => {
    if (!owner || sessionLost) return;
    let alive = true;
    let timer: ReturnType<typeof setTimeout>;
    const controller = new AbortController();
    async function poll() {
      try {
        const result = await client.request<NativeStatus>(
          '/api/calls/native/status',
          'GET',
          undefined,
          controller.signal,
        );
        if (alive) setStatus(result);
      } catch (reason) {
        if (alive) {
          setStatus(null);
          if (revokeMediaOnOwnerDenial(media.current, reason)) {
            setSessionLost(true);
          }
        }
      } finally {
        if (alive) timer = setTimeout(() => void poll(), settings.corePollMs);
      }
    }
    void poll();
    return () => {
      alive = false;
      controller.abort();
      clearTimeout(timer);
    };
  }, [client, owner, sessionLost]);

  const unfinished = status?.operations.find((item) => item.state !== 'DONE');
  const manualRecovery = unfinished?.recovery === 'manual_reconciliation_required';

  async function start() {
    const lifecycle = media.current;
    if (
      !available ||
      !owner ||
      sessionLost ||
      !status ||
      manualRecovery ||
      !lifecycle.isOpen() ||
      starting.current ||
      lifecycle.hasActive()
    )
      return;
    const callProvider = unfinished?.provider ?? provider;
    if (unfinished) operation.current = unfinished.operation_id;
    starting.current = true;
    setState('starting');
    setMessage(copy.starting);
    let microphone: MediaStream;
    try {
      microphone = await navigator.mediaDevices.getUserMedia({ audio: true });
      microphone.getTracks().forEach((track) => track.stop());
    } catch {
      if (lifecycle.isOpen()) {
        setState('error');
        setMessage(copy.permission);
      }
      starting.current = false;
      return;
    }
    if (!lifecycle.isOpen()) {
      starting.current = false;
      return;
    }
    try {
      const attached = await attachOwnedMedia(
        lifecycle,
        () =>
          client.request<unknown>(
            '/api/calls/native/create',
            'POST',
            { provider: callProvider, operation_id: operation.current },
            undefined,
            settings.nativeCreateTimeoutMs,
          ),
        async (response) => {
          const grant = parseNativeGrant(response);
          let endedEarly = false;
          const joined = await joinNativeMedia(
            grant,
            () => {
              if (!lifecycle.isOpen()) return;
              endedEarly = true;
              lifecycle.take();
              setState('ended');
              setMessage(copy.ended);
              operation.current = crypto.randomUUID();
            },
            () => {
              if (!lifecycle.isOpen()) return;
              endedEarly = true;
              const active = lifecycle.take();
              if (active) void active.stop();
              setState('error');
              setMessage(copy.joinError);
            },
            lifecycle.signal,
          );
          if (endedEarly) {
            await joined.stop();
            return null;
          }
          return joined;
        },
      );
      if (!attached) return;
      setState('connected');
      setMessage(copy.connected);
    } catch (reason) {
      if (lifecycle.isOpen()) {
        if (revokeMediaOnOwnerDenial(lifecycle, reason)) {
          setSessionLost(true);
        }
        setState('error');
        setMessage(
          reason instanceof CoreRequestError
            ? (copy.failures[reason.code] ?? copy.joinError)
            : copy.joinError,
        );
      }
      setStatus(null);
    } finally {
      starting.current = false;
    }
  }

  async function stop() {
    const active = media.current.take();
    if (active) {
      try {
        await active.stop();
      } catch {
        setState('error');
        setMessage(copy.joinError);
        return;
      }
    }
    setState('ended');
    setMessage(copy.ended);
    operation.current = crypto.randomUUID();
  }

  return (
    <section className="panel core-record" aria-label={copy.title}>
      <h3>{copy.title}</h3>
      <p>{copy.intro}</p>
      <p role="status">
        {available ? (owner && !sessionLost ? message : copy.ownerOnly) : copy.unavailable}
      </p>
      {owner && (
        <>
          {!status && <p role="alert">{copy.statusUnavailable}</p>}
          {status && (
            <>
              <p>
                {copy.limits}: {status.limits.max_seconds}s · {status.limits.max_concurrent} call
              </p>
              <p>{copy.entitlement}</p>
              {(['retell', 'vapi'] as const).map((name) => (
                <p key={name}>
                  {name}: {status.entitlements[name].state} · {copy.verifiedAt}:{' '}
                  {status.entitlements[name].verified_at ?? copy.unverified}
                </p>
              ))}
              {unfinished && (
                <p role="alert">
                  {copy.operation} {unfinished.operation_id} · {unfinished.provider} ·{' '}
                  {unfinished.state}. {manualRecovery ? copy.manualRecovery : copy.resumeExisting}
                </p>
              )}
              {status.operations
                .filter((item) => item.state === 'DONE')
                .map((item) => (
                  <p key={item.operation_id}>
                    {copy.operation} {item.operation_id} · {item.provider} · {item.state} ·{' '}
                    {item.created_at}
                  </p>
                ))}
            </>
          )}
          {!available && <p>{copy.availability}</p>}
        </>
      )}
      {available && owner && !sessionLost && (
        <>
          <label>
            <span>{copy.provider}</span>
            <select
              value={provider}
              disabled={state === 'starting' || state === 'connected' || Boolean(unfinished)}
              onChange={(event) => {
                setProvider(event.target.value as Provider);
                operation.current = crypto.randomUUID();
              }}
            >
              <option value="retell">{copy.retell}</option>
              <option value="vapi">{copy.vapi}</option>
            </select>
          </label>
          <div className="core-toolbar">
            <Button
              disabled={
                !status || Boolean(manualRecovery) || state === 'starting' || state === 'connected'
              }
              onClick={() => void start()}
            >
              {copy.start}
            </Button>
            <Button disabled={state !== 'connected'} onClick={() => void stop()}>
              {copy.stop}
            </Button>
          </div>
        </>
      )}
    </section>
  );
}
