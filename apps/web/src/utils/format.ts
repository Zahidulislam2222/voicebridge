import { settings } from '../config/settings';

export function formatDate(value: string, withTime = false): string {
  // Wall-time appointment records are intentionally distinct from call instants.
  const wall = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(value);
  const date = new Date(wall ? `${value}:00Z` : value);
  return new Intl.DateTimeFormat(settings.locale, {
    month: 'short',
    day: 'numeric',
    ...(withTime ? { hour: 'numeric', minute: '2-digit' } : {}),
    timeZone: wall ? 'UTC' : settings.timezone,
  }).format(date);
}
export function duration(seconds: number): string {
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
}
export function outcomeTone(value: string): string {
  return value === 'Booked' || value === 'Confirmed' || value === 'Completed' || value === 'Passed'
    ? 'success'
    : value === 'Failed' || value === 'Needs review'
      ? 'warning'
      : value === 'Cancelled'
        ? 'muted'
        : value === 'Answered'
          ? 'blue'
          : 'neutral';
}
