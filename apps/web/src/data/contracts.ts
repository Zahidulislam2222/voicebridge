import { z } from '../config/schema-runtime';
import {
  pageKeys,
  outcomeValues,
  appointmentValues,
  jobValues,
  evaluationValues,
} from '../protocol';
import { isWallTime } from '../utils/wall-time';
import type { DemoState } from '../types';
import { copyKeys } from './copy-contract';

const text = z.string().min(1);
const wallTime = text.refine(isWallTime);
const instant = z.iso.datetime({ offset: true });
const transcript = z.array(z.object({ speaker: text, text })).min(1);
const contentSchema = z.object({
  brand: text,
  business: text,
  workspace: text,
  subtitle: text,
  assets: z.object({ hero: text.regex(/^\.\/[a-z0-9-]+\.(png|webp)$/) }),
  chartHours: z.array(z.number().int().min(0).max(23)).min(1),
  evaluationResults: z.record(text, z.enum(['Passed', 'Needs review'])),
  fixedLabels: z.record(z.enum(copyKeys.fixedLabels), text),
  hero: z.object({
    eyebrow: text,
    title: text,
    description: text,
    cta: text,
    secondary: text,
    caption: text,
    footer: text,
    points: z.array(z.object({ title: text, text })).min(1),
  }),
  nav: z.array(
    z.object({
      id: z.enum(pageKeys),
      label: text,
      icon: text,
      group: z.enum(['workspace', 'manage']),
    }),
  ),
  pageDescriptions: z.record(z.enum(pageKeys), text),
  labels: z.record(z.enum(copyKeys.labels), text),
  messages: z.record(z.enum(copyKeys.messages), text),
  timeline: z.array(z.object({ title: text, text })).min(1),
  voiceProfiles: z
    .array(
      z.object({
        id: text,
        name: text,
        style: text,
        description: text,
        accent: text,
        tone: text,
        bars: z.array(z.number().min(0).max(100)).min(1),
      }),
    )
    .min(1),
  services: z.array(text).min(1),
  scenario: z.object({
    name: text,
    phone: text,
    email: z.email().refine((x) => x.endsWith('.test')),
    service: text,
    date: wallTime,
    confirmed: z.boolean(),
  }),
  simulationTranscript: transcript,
  flowSteps: z.array(text).min(1),
  usageUnits: z.record(z.enum(copyKeys.usageUnits), text),
  outcomes: z.array(z.enum(outcomeValues)),
  auditActions: z.record(z.enum(copyKeys.auditActions), text),
});
const fixtureSchema = z.object({
  sampleNow: instant,
  contacts: z.array(
    z.object({
      id: text,
      name: text,
      initials: text,
      phone: text,
      email: z.email().refine((x) => x.endsWith('.test')),
      notes: z.string(),
    }),
  ),
  calls: z.array(
    z.object({
      id: text,
      name: text,
      initials: text,
      phone: text,
      date: instant,
      duration: z.number().int().nonnegative(),
      outcome: z.enum(outcomeValues),
      summary: text,
      service: text,
      transcript,
      appointmentId: text.optional(),
      contactId: text,
    }),
  ),
  appointments: z.array(
    z.object({
      id: text,
      name: text,
      service: text,
      date: wallTime,
      status: z.enum(appointmentValues),
      contactId: text,
      callId: text,
    }),
  ),
  jobs: z.array(
    z.object({
      id: text,
      name: text,
      status: z.enum(jobValues),
      appointmentId: text,
      attempts: z.number().int().positive(),
      detail: text,
    }),
  ),
  documents: z.array(z.object({ id: text, name: text.regex(/\.(txt|md)$/i), text, updated: text })),
  audit: z.array(z.object({ id: text, date: instant, action: text, detail: text })),
  agent: z.object({ name: text, greeting: text, voiceId: text, handoff: text }),
  integrations: z.array(
    z.object({
      id: text,
      name: text,
      description: text,
      category: text,
      connected: z.literal(false),
    }),
  ),
  evaluations: z.array(
    z.object({ id: text, name: text, expectation: text, result: z.enum(evaluationValues) }),
  ),
  operationIds: z.array(text),
});
function unique(values: string[], label: string) {
  if (new Set(values).size !== values.length) throw new Error(`Duplicate ${label}`);
}
export function validateContent<T>(input: T): T {
  const data = contentSchema.parse(input);
  unique(
    data.nav.map((x) => x.id),
    'navigation routes',
  );
  if (data.nav.length !== pageKeys.length) throw new Error('Incomplete navigation');
  unique(
    data.voiceProfiles.map((x) => x.id),
    'voice IDs',
  );
  unique(data.services, 'services');
  unique(data.chartHours.map(String), 'chart hours');
  unique(data.outcomes, 'outcomes');
  if (
    data.outcomes.length !== outcomeValues.length ||
    !data.services.includes(data.scenario.service)
  )
    throw new Error('Incomplete product catalogue');
  return input;
}
export function validateFixture(input: unknown, inputContent: unknown): DemoState {
  const content = contentSchema.parse(validateContent(inputContent));
  const data = fixtureSchema.parse(input);
  for (const [kind, records] of Object.entries({
    contacts: data.contacts,
    calls: data.calls,
    appointments: data.appointments,
    jobs: data.jobs,
    documents: data.documents,
    audit: data.audit,
    integrations: data.integrations,
    evaluations: data.evaluations,
  }))
    unique(
      records.map((x) => x.id),
      `${kind} IDs`,
    );
  unique(
    data.contacts.map((x) => x.email.toLowerCase()),
    'contact emails',
  );
  unique(data.operationIds, 'operation IDs');
  const contacts = new Map(data.contacts.map((x) => [x.id, x]));
  const calls = new Map(data.calls.map((x) => [x.id, x]));
  const appointments = new Map(data.appointments.map((x) => [x.id, x]));
  if (!content.voiceProfiles.some((x) => x.id === data.agent.voiceId))
    throw new Error('Unknown agent voice');
  for (const call of data.calls) {
    if (!contacts.has(call.contactId) || !content.services.includes(call.service))
      throw new Error('Invalid call reference');
    if (call.outcome === 'Booked' && !call.appointmentId)
      throw new Error('Booked call without appointment');
    if (call.appointmentId) {
      const appointment = appointments.get(call.appointmentId);
      if (
        !appointment ||
        appointment.callId !== call.id ||
        appointment.contactId !== call.contactId
      )
        throw new Error('Invalid call/appointment link');
    }
  }
  for (const appointment of data.appointments) {
    const call = calls.get(appointment.callId);
    if (
      !contacts.has(appointment.contactId) ||
      !call ||
      call.appointmentId !== appointment.id ||
      call.contactId !== appointment.contactId ||
      !content.services.includes(appointment.service)
    )
      throw new Error('Invalid appointment reference');
  }
  for (const job of data.jobs)
    if (!appointments.has(job.appointmentId)) throw new Error('Invalid job reference');
  unique(
    data.appointments.filter((x) => x.status === 'Confirmed').map((x) => x.date),
    'active appointment slots',
  );
  for (const evaluation of data.evaluations)
    if (!content.evaluationResults[evaluation.id])
      throw new Error('Missing evaluation result mapping');
  if (
    Object.keys(content.evaluationResults).some((id) => !data.evaluations.some((x) => x.id === id))
  )
    throw new Error('Unknown evaluation mapping');
  return data;
}
