import { z } from '../config/schema-runtime';
import { corePageKeys } from '../protocol';

const textKeys = [
  'title',
  'subtitle',
  'connect',
  'credential',
  'connectionHint',
  'disabled',
  'disconnect',
  'refresh',
  'booking',
  'confirm',
  'pending',
  'saved',
  'bookingConfirmed',
  'bookingRescheduled',
  'bookingCancelled',
  'cancel',
  'cancelPrompt',
  'reschedule',
  'revision',
  'reconcile',
  'retry',
  'empty',
  'save',
  'remove',
  'removePrompt',
  'evaluate',
  'acoustic',
  'query',
  'unavailable',
  'back',
  'startPlaceholder',
  'chooseService',
  'newStart',
  'attempts',
  'passed',
  'needsReview',
  'requestFailed',
  'connectionDisabled',
  'evaluationFixtures',
  'cleanup',
  'login',
  'logout',
] as const;
const fieldKeys = [
  'name',
  'email',
  'phone',
  'service',
  'start',
  'documentName',
  'approvedText',
  'greeting',
  'handoff',
  'voice_id',
] as const;
const text = z.string().min(1);
const labels = z.record(z.enum(textKeys), text);
const metadata = z
  .object({
    navigation: z
      .array(z.object({ id: z.enum(corePageKeys), label: text }).strict())
      .length(corePageKeys.length)
      .refine((entries) => new Set(entries.map((entry) => entry.id)).size === corePageKeys.length),
    fieldLabels: z.record(z.enum(fieldKeys), text),
  })
  .strict();

export function parseCoreConsole(value: unknown) {
  const object = z.record(z.string(), z.unknown()).parse(value);
  const { navigation, fieldLabels, ...copy } = object;
  return { ...labels.parse(copy), ...metadata.parse({ navigation, fieldLabels }) };
}
