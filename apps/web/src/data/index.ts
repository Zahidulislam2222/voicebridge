import contentData from './content.json';
import demoData from './demo.json';
import type { DemoState, PageId, Outcome } from '../types';
import { validateContent, validateFixture } from './contracts';

export const content = validateContent(contentData);
export const pageIds = content.nav.map((item) => item.id as PageId);
export const sampleNow = demoData.sampleNow;
export function initialState(): DemoState {
  return validateFixture(demoData, content);
}
export const outcomes = content.outcomes as Outcome[];
