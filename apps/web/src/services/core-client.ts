import copy from '../data/core-console';
import { settings } from '../config/settings';
import type { paths } from '../generated/core-api';

export type Booking = paths['/api/bookings']['post']['requestBody']['content']['application/json'];
export type BookingRecord =
  paths['/api/bookings']['post']['responses'][200]['content']['application/json'];
export function bookingNotice(status: string, action: 'create' | 'reschedule' | 'cancel'): string {
  const expected = action === 'cancel' ? 'cancelled' : 'confirmed';
  if (status !== expected) return copy.pending;
  return {
    create: copy.bookingConfirmed,
    reschedule: copy.bookingRescheduled,
    cancel: copy.bookingCancelled,
  }[action];
}
export type Agent = paths['/api/agent']['put']['requestBody']['content']['application/json'];
export type AgentRecord =
  paths['/api/agent']['put']['responses'][200]['content']['application/json'];
export function agentDraft(value: Omit<Agent, 'expected_revision'> & { revision: number }): Agent {
  return {
    name: value.name,
    greeting: value.greeting,
    handoff: value.handoff,
    voice_id: value.voice_id,
    expected_revision: value.revision,
  };
}
export type CoreSnapshot =
  paths['/api/state']['get']['responses'][200]['content']['application/json'];
export class CoreClient {
  constructor(
    private readonly credential: string,
    private readonly csrf?: string,
  ) {}
  async request<T>(path: string, method = 'GET', body?: unknown, signal?: AbortSignal): Promise<T> {
    if (!settings.coreApiUrl) throw new Error(copy.connectionDisabled);
    const response = await fetch(settings.coreApiUrl + path, {
      method,
      headers: {
        ...(settings.coreSessionAuth
          ? { 'X-CSRF-Token': this.csrf ?? '' }
          : { Authorization: `Bearer ${this.credential}` }),
        'Content-Type': 'application/json',
      },
      body: body === undefined ? undefined : JSON.stringify(body),
      credentials: settings.coreSessionAuth ? 'same-origin' : 'omit',
      cache: 'no-store',
      redirect: 'error',
      signal: signal
        ? AbortSignal.any([signal, AbortSignal.timeout(settings.coreRequestTimeoutMs)])
        : AbortSignal.timeout(settings.coreRequestTimeoutMs),
    });
    if (!response.ok) {
      const error: unknown = await response.json().catch(() => ({}));
      const code =
        error && typeof error === 'object' && 'error' in error
          ? String(error.error)
          : copy.requestFailed;
      throw new Error(code.replaceAll('_', ' '));
    }
    return (response.status === 204 ? undefined : await response.json()) as T;
  }
  state(signal?: AbortSignal) {
    return this.request<CoreSnapshot>('/api/state', 'GET', undefined, signal);
  }
}
