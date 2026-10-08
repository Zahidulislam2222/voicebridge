export type Role = 'operator' | 'viewer';
export type Outcome = 'Booked' | 'Answered' | 'Transferred' | 'Needs review';
export type PageId =
  | 'overview'
  | 'agents'
  | 'voices'
  | 'calls'
  | 'appointments'
  | 'contacts'
  | 'automations'
  | 'knowledge'
  | 'evaluations'
  | 'integrations'
  | 'usage'
  | 'audit';
export interface CallRecord {
  id: string;
  name: string;
  initials: string;
  phone: string;
  date: string;
  duration: number;
  outcome: Outcome;
  summary: string;
  service: string;
  transcript: { speaker: string; text: string }[];
  appointmentId?: string;
  contactId: string;
}
export interface Appointment {
  id: string;
  name: string;
  service: string;
  date: string;
  status: 'Confirmed' | 'Cancelled';
  contactId: string;
  callId: string;
}
export interface Contact {
  id: string;
  name: string;
  initials: string;
  phone: string;
  email: string;
  notes: string;
}
export interface Job {
  id: string;
  name: string;
  status: 'Completed' | 'Failed';
  appointmentId: string;
  attempts: number;
  detail: string;
}
export interface KnowledgeDoc {
  id: string;
  name: string;
  text: string;
  updated: string;
}
export interface AuditEvent {
  id: string;
  date: string;
  action: string;
  detail: string;
}
export interface AgentDraft {
  name: string;
  greeting: string;
  voiceId: string;
  handoff: string;
}
export interface Integration {
  id: string;
  name: string;
  description: string;
  category: string;
  connected: boolean;
}
export interface Evaluation {
  id: string;
  name: string;
  expectation: string;
  result: 'Passed' | 'Needs review' | 'Not run';
}
export interface DemoState {
  calls: CallRecord[];
  appointments: Appointment[];
  contacts: Contact[];
  jobs: Job[];
  documents: KnowledgeDoc[];
  audit: AuditEvent[];
  agent: AgentDraft;
  integrations: Integration[];
  evaluations: Evaluation[];
  operationIds: string[];
}
export interface BookingInput {
  operationId: string;
  name: string;
  phone: string;
  email: string;
  service: string;
  date: string;
  confirmed: boolean;
}
