import { useSyncExternalStore } from 'react';

// Stable CSS media-query protocol syntax; shared by every animated component.
const motionQuery = '(prefers-reduced-motion: reduce)';

export function getMotionPreference(): boolean {
  return window.matchMedia(motionQuery).matches;
}
export function subscribeMotionPreference(changed: () => void): () => void {
  const media = window.matchMedia(motionQuery);
  media.addEventListener('change', changed);
  return () => media.removeEventListener('change', changed);
}
export function useReducedMotion(): boolean {
  return useSyncExternalStore(subscribeMotionPreference, getMotionPreference, () => true);
}
