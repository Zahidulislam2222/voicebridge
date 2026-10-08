import { content, sampleNow } from '../data';
import type { PublicSettings } from '../config/settings';
import type { AgentDraft, BookingInput, DemoState, Role } from '../types';
import { containsInvalidPlainText } from '../utils/text';
import { isWallTime } from '../utils/wall-time';

export class DemoError extends Error {}
const trim = (value: string, max: number) => value.trim().slice(0, max);
export function authorize(role: Role): void {
  if (role !== 'operator') throw new DemoError(content.messages.denied);
}
function audit(state: DemoState, action: string, detail: string): void {
  state.audit.unshift({ id: crypto.randomUUID(), date: new Date().toISOString(), action, detail });
}
function draftTimeValid(value: string): boolean {
  // Sample appointments are local wall times in the configured business timezone.
  return isWallTime(value) && value > sampleNow.slice(0, 16);
}
function requireSlot(state: DemoState, date: string, exceptId?: string): void {
  if (!draftTimeValid(date)) throw new DemoError(content.messages.dateInvalid);
  if (
    state.appointments.some((x) => x.id !== exceptId && x.status === 'Confirmed' && x.date === date)
  )
    throw new DemoError(content.messages.slotTaken);
}
export function saveAgent(
  state: DemoState,
  role: Role,
  draft: AgentDraft,
  config: PublicSettings,
): DemoState {
  authorize(role);
  if (
    ![draft.name, draft.greeting, draft.handoff].every(
      (x) => x.trim() && x.length <= config.maxTextLength,
    ) ||
    !content.voiceProfiles.some((x) => x.id === draft.voiceId)
  )
    throw new DemoError(content.messages.invalid);
  const next = structuredClone(state);
  next.agent = {
    ...draft,
    name: draft.name.trim(),
    greeting: draft.greeting.trim(),
    handoff: draft.handoff.trim(),
  };
  audit(next, content.auditActions.agent, next.agent.name);
  return next;
}
export function selectVoice(state: DemoState, role: Role, voiceId: string): DemoState {
  authorize(role);
  if (!content.voiceProfiles.some((x) => x.id === voiceId))
    throw new DemoError(content.messages.invalid);
  const next = structuredClone(state);
  next.agent.voiceId = voiceId;
  audit(
    next,
    content.auditActions.voice,
    content.voiceProfiles.find((x) => x.id === voiceId)?.name ?? voiceId,
  );
  return next;
}
export function confirmBooking(
  state: DemoState,
  role: Role,
  input: BookingInput,
  config: PublicSettings,
): DemoState {
  authorize(role);
  if (state.operationIds.includes(input.operationId)) return state;
  if (!input.confirmed) throw new DemoError(content.messages.unconfirmed);
  const digits = input.phone.replace(/\D/g, '').length;
  if (
    !input.operationId ||
    !input.name.trim() ||
    input.name.length > config.maxTextLength ||
    !/^\+?[\d ()-]+$/.test(input.phone) ||
    input.phone.length > config.phoneMaxLength ||
    digits < config.phoneMinDigits ||
    digits > config.phoneMaxDigits ||
    !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.email) ||
    input.email.length > config.maxTextLength ||
    !content.services.includes(input.service)
  )
    throw new DemoError(content.messages.invalid);
  requireSlot(state, input.date);
  const next = structuredClone(state);
  const existing = next.contacts.find(
    (x) => x.email.toLowerCase() === input.email.trim().toLowerCase(),
  );
  const contactId = existing?.id ?? crypto.randomUUID();
  const callId = crypto.randomUUID();
  const appointmentId = crypto.randomUUID();
  const name = trim(input.name, config.maxTextLength);
  const initials = name
    .split(/\s+/)
    .slice(0, 2)
    .map((x) => x[0])
    .join('')
    .toUpperCase();
  if (!existing)
    next.contacts.unshift({
      id: contactId,
      name,
      initials,
      phone: input.phone.trim(),
      email: input.email.trim(),
      notes: input.service,
    });
  next.calls.unshift({
    id: callId,
    name,
    initials,
    phone: input.phone.trim(),
    date: new Date().toISOString(),
    duration: 0,
    outcome: 'Booked',
    service: input.service,
    summary: content.messages.bookingCreated,
    contactId,
    appointmentId,
    transcript: [
      ...content.simulationTranscript,
      { speaker: name, text: `${input.service} · ${input.date}` },
      {
        speaker:
          content.voiceProfiles.find((v) => v.id === state.agent.voiceId)?.name ?? state.agent.name,
        text: content.messages.bookingCreated,
      },
    ],
  });
  next.appointments.unshift({
    id: appointmentId,
    name,
    service: input.service,
    date: input.date,
    status: 'Confirmed',
    contactId,
    callId,
  });
  next.jobs.unshift({
    id: crypto.randomUUID(),
    name: content.fixedLabels.followup,
    status: 'Completed',
    appointmentId,
    attempts: 1,
    detail: content.labels.demoNotice,
  });
  next.operationIds.push(input.operationId);
  audit(next, content.auditActions.booking, `${name} · ${input.service} · ${input.date}`);
  return next;
}
export function updateAppointment(
  state: DemoState,
  role: Role,
  id: string,
  date?: string,
): DemoState {
  authorize(role);
  const current = state.appointments.find((x) => x.id === id);
  if (!current || current.status === 'Cancelled') throw new DemoError(content.messages.unknown);
  if (date !== undefined) requireSlot(state, date, id);
  const next = structuredClone(state);
  const record = next.appointments.find((x) => x.id === id);
  if (!record) throw new DemoError(content.messages.unknown);
  if (date === undefined) record.status = 'Cancelled';
  else record.date = date;
  audit(
    next,
    date === undefined ? content.auditActions.cancel : content.auditActions.reschedule,
    `${record.name} · ${record.date}`,
  );
  return next;
}
export function retryJob(state: DemoState, role: Role, id: string): DemoState {
  authorize(role);
  const current = state.jobs.find((x) => x.id === id);
  if (!current) throw new DemoError(content.messages.unknown);
  if (current.status === 'Completed') return state;
  const next = structuredClone(state);
  const job = next.jobs.find((x) => x.id === id);
  if (!job) throw new DemoError(content.messages.unknown);
  job.status = 'Completed';
  job.attempts += 1;
  job.detail = content.messages.retried;
  audit(next, content.auditActions.retry, job.name);
  return next;
}
export function addDocument(
  state: DemoState,
  role: Role,
  name: string,
  text: string,
  config: PublicSettings,
): DemoState {
  authorize(role);
  if (!/\.(txt|md)$/i.test(name)) throw new DemoError(content.messages.unsupported);
  if (new TextEncoder().encode(text).byteLength > config.maxUploadBytes)
    throw new DemoError(content.messages.tooLarge);
  if (!text.trim() || containsInvalidPlainText(text))
    throw new DemoError(content.messages.invalidDocument);
  const next = structuredClone(state);
  next.documents.unshift({
    id: crypto.randomUUID(),
    name: trim(name, config.maxTextLength),
    text,
    updated: new Date().toLocaleDateString(config.locale),
  });
  audit(next, content.auditActions.upload, name);
  return next;
}
export function removeDocument(state: DemoState, role: Role, id: string): DemoState {
  authorize(role);
  if (!state.documents.some((x) => x.id === id)) throw new DemoError(content.messages.unknown);
  const next = structuredClone(state);
  next.documents = next.documents.filter((x) => x.id !== id);
  audit(next, content.auditActions.remove, id);
  return next;
}
export function toggleIntegration(state: DemoState, role: Role, id: string): DemoState {
  authorize(role);
  const next = structuredClone(state);
  const record = next.integrations.find((x) => x.id === id);
  if (!record) throw new DemoError(content.messages.unknown);
  record.connected = !record.connected;
  audit(next, content.auditActions.integration, record.name);
  return next;
}
export function runEvaluations(state: DemoState, role: Role): DemoState {
  authorize(role);
  const next = structuredClone(state);
  next.evaluations = next.evaluations.map((x) => ({
    ...x,
    result:
      content.evaluationResults[x.id as keyof typeof content.evaluationResults] === 'Passed'
        ? 'Passed'
        : 'Needs review',
  }));
  audit(next, content.auditActions.evaluate, content.messages.evaluation);
  return next;
}
