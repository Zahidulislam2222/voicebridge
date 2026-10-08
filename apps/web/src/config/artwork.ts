import { artworkElementId, artworkDataPattern } from '../../../../tools/presentation-protocol.mjs';

export function artworkSource(
  fallback: string,
  embedded = typeof document === 'undefined'
    ? undefined
    : document.getElementById(artworkElementId)?.getAttribute('content'),
): string {
  return embedded && artworkDataPattern.test(embedded) ? embedded : fallback;
}
