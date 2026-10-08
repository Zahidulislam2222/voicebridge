// Stable route identities and demo record states; maintained labels live in content.json.
export const pageKeys = [
  'overview',
  'agents',
  'voices',
  'calls',
  'appointments',
  'contacts',
  'automations',
  'knowledge',
  'evaluations',
  'integrations',
  'usage',
  'audit',
] as const;
export const outcomeValues = ['Booked', 'Answered', 'Transferred', 'Needs review'] as const;
export const appointmentValues = ['Confirmed', 'Cancelled'] as const;
export const jobValues = ['Completed', 'Failed'] as const;
export const corePageKeys = [
  'overview',
  'appointments',
  'contacts',
  'calls',
  'automations',
  'knowledge',
  'agent',
  'integrations',
  'evaluations',
  'audit',
] as const;
export type CorePage = (typeof corePageKeys)[number];
export const evaluationValues = ['Passed', 'Needs review', 'Not run'] as const;

export const publicPageKeys = [
  'welcome',
  'features',
  'solutions',
  'pricing',
  'company',
  'resources',
  'contact',
  'get-started',
] as const;
export type PublicPage = (typeof publicPageKeys)[number];
export const editorialPageKeys = [
  'features',
  'solutions',
  'pricing',
  'company',
  'resources',
] as const;

export const isPublicPage = (value: string): value is PublicPage =>
  publicPageKeys.some((page) => page === value);
