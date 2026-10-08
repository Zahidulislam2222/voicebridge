import { z } from '../config/schema-runtime';
import { containsInvalidPlainText } from '../utils/text';

export interface IntakeDetails {
  name: string;
  email: string;
  company: string;
  industry: string;
  voice: string;
  message: string;
  team: string;
}
export interface IntakeRules {
  maxTextLength: number;
  onboarding: boolean;
  industryIds: string[];
  voiceIds: string[];
  teamChoices: string[];
}
export function normalizeIntake(value: IntakeDetails, rules: IntakeRules): IntakeDetails {
  const text = z
    .string()
    .trim()
    .min(1)
    .max(rules.maxTextLength)
    .refine((value) => !containsInvalidPlainText(value));
  return z
    .object({
      name: text,
      email: z.string().trim().max(rules.maxTextLength).pipe(z.email()),
      company: text,
      industry: text.refine((value) => rules.industryIds.includes(value)),
      voice: text.refine((value) => rules.voiceIds.includes(value)),
      team: text.refine((value) => rules.teamChoices.includes(value)),
      message: rules.onboarding ? z.string().trim().max(rules.maxTextLength) : text,
    })
    .parse(value);
}
