import type { Role } from '../types';

export interface PublicSettings {
  locale: string;
  timezone: string;
  role: Role;
  simulationDelayMs: number;
  notificationMs: number;
  maxUploadBytes: number;
  maxTextLength: number;
  animationSeconds: number;
  phoneMinDigits: number;
  phoneMaxDigits: number;
  phoneMaxLength: number;
  coreApiUrl: string;
  coreSessionAuth: boolean;
  corePollMs: number;
  coreRequestTimeoutMs: number;
}
export const settingsDefaults: PublicSettings = {
  locale: 'en-US',
  timezone: 'America/New_York',
  role: 'operator',
  simulationDelayMs: 900,
  notificationMs: 4500,
  maxUploadBytes: 65536,
  maxTextLength: 400,
  animationSeconds: 0.26,
  phoneMinDigits: 7,
  phoneMaxDigits: 15,
  phoneMaxLength: 25,
  coreApiUrl: '',
  coreSessionAuth: false,
  corePollMs: 2500,
  coreRequestTimeoutMs: 5000,
};
export function createSettings(
  env: Record<string, string | undefined> = {},
): Readonly<PublicSettings> {
  const number = (key: string, fallback: number, min: number, max: number) => {
    const value = env[key] === undefined ? fallback : Number(env[key]);
    if (!Number.isFinite(value) || value < min || value > max)
      throw new Error(`Invalid public setting ${key}`);
    return value;
  };
  const result: PublicSettings = {
    ...settingsDefaults,
    locale: env.VITE_LOCALE ?? settingsDefaults.locale,
    timezone: env.VITE_TIMEZONE ?? settingsDefaults.timezone,
    coreApiUrl: env.VITE_CORE_API_URL ?? settingsDefaults.coreApiUrl,
    coreSessionAuth: env.VITE_CORE_SESSION_AUTH === 'true',
    corePollMs: number('VITE_CORE_POLL_MS', settingsDefaults.corePollMs, 250, 60000),
    coreRequestTimeoutMs: number(
      'VITE_CORE_REQUEST_TIMEOUT_MS',
      settingsDefaults.coreRequestTimeoutMs,
      250,
      30000,
    ),
    simulationDelayMs: number(
      'VITE_SIMULATION_DELAY_MS',
      settingsDefaults.simulationDelayMs,
      0,
      5000,
    ),
    notificationMs: number('VITE_NOTIFICATION_MS', settingsDefaults.notificationMs, 1000, 10000),
    maxUploadBytes: number('VITE_MAX_UPLOAD_BYTES', settingsDefaults.maxUploadBytes, 1024, 1048576),
    maxTextLength: number('VITE_MAX_TEXT_LENGTH', settingsDefaults.maxTextLength, 100, 2000),
    animationSeconds: number('VITE_ANIMATION_SECONDS', settingsDefaults.animationSeconds, 0, 1),
  };
  new Intl.DateTimeFormat(result.locale, { timeZone: result.timezone }).format();
  if (result.coreSessionAuth && result.coreApiUrl !== '/engine-api')
    throw new Error('Session authentication requires the same-origin engine gateway');
  if (result.coreApiUrl && result.coreApiUrl !== '/engine-api') {
    const url = new URL(result.coreApiUrl);
    if (
      url.protocol !== 'http:' ||
      !['localhost', '127.0.0.1', '[::1]'].includes(url.hostname) ||
      url.username ||
      url.password ||
      url.search ||
      url.hash
    )
      throw new Error('Core API requires loopback or the authenticated same-origin gateway');
  }
  return Object.freeze(result);
}
export const settings = createSettings(import.meta.env);
