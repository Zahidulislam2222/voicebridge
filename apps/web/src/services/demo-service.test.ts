import { describe, expect, it } from 'vitest';
import { initialState, content } from '../data';
import { settingsDefaults } from '../config/settings';
import {
  addDocument,
  confirmBooking,
  removeDocument,
  retryJob,
  runEvaluations,
  saveAgent,
  selectVoice,
  toggleIntegration,
  updateAppointment,
} from './demo-service';
import type { BookingInput } from '../types';

const config = settingsDefaults;
const booking = (): BookingInput => ({
  ...content.scenario,
  confirmed: true,
  operationId: crypto.randomUUID(),
});
describe('synthetic booking journey', () => {
  it('creates linked records only after confirmation', () => {
    const before = initialState();
    const input = booking();
    const after = confirmBooking(before, 'operator', input, config);
    expect(after.calls).toHaveLength(before.calls.length + 1);
    expect(after.contacts).toHaveLength(before.contacts.length + 1);
    expect(after.appointments).toHaveLength(before.appointments.length + 1);
    expect(after.jobs).toHaveLength(before.jobs.length + 1);
    const call = after.calls[0];
    const appointment = after.appointments[0];
    expect(call?.appointmentId).toBe(appointment?.id);
    expect(call?.contactId).toBe(appointment?.contactId);
    expect(after.jobs[0]?.appointmentId).toBe(appointment?.id);
    expect(before.operationIds).toHaveLength(0);
  });
  it('rejects unconfirmed details without changing records', () => {
    const state = initialState();
    expect(() =>
      confirmBooking(state, 'operator', { ...booking(), confirmed: false }, config),
    ).toThrow(content.messages.unconfirmed);
    expect(state.calls).toHaveLength(7);
  });
  it('repeating a confirmed operation cannot add another booking', () => {
    const input = booking();
    const first = confirmBooking(initialState(), 'operator', input, config);
    expect(confirmBooking(first, 'operator', input, config)).toBe(first);
  });
  it('rejects a stale occupied appointment time', () => {
    const state = initialState();
    expect(() =>
      confirmBooking(
        state,
        'operator',
        { ...booking(), date: state.appointments[0]?.date ?? '' },
        config,
      ),
    ).toThrow(content.messages.slotTaken);
  });
  it('rejects malformed and past dates', () => {
    for (const date of [
      'invalid',
      '2026-10-06T10:00',
      '2026-10-08T10:00<script>',
      '2026-11-31T10:00',
      '2027-02-29T10:00',
      '2026-11-10T24:00',
    ])
      expect(() =>
        confirmBooking(initialState(), 'operator', { ...booking(), date }, config),
      ).toThrow(content.messages.dateInvalid);
  });
  it('reuses an existing contact for the same email', () => {
    const state = initialState();
    const email = state.contacts[0]?.email ?? '';
    const after = confirmBooking(state, 'operator', { ...booking(), email }, config);
    expect(after.contacts).toHaveLength(state.contacts.length);
    expect(after.calls[0]?.contactId).toBe(state.contacts[0]?.id);
  });
  it('rejects invalid email, phone, name and unknown service', () => {
    for (const patch of [
      { email: 'bad' },
      { phone: 'bad' },
      { phone: '-------' },
      { name: '' },
      { service: 'unsupported' },
    ])
      expect(() =>
        confirmBooking(initialState(), 'operator', { ...booking(), ...patch }, config),
      ).toThrow(content.messages.invalid);
  });
});
describe('appointment and automation changes', () => {
  it('rejects impossible reschedule dates', () => {
    for (const date of ['2026-11-31T10:00', '2027-02-29T10:00', '2026-11-10T24:00'])
      expect(() => updateAppointment(initialState(), 'operator', 'apt-1', date)).toThrow(
        content.messages.dateInvalid,
      );
  });
  it('reschedules the existing record and creates an audit event', () => {
    const before = initialState();
    const after = updateAppointment(before, 'operator', 'apt-1', '2026-10-10T09:30');
    expect(after.appointments).toHaveLength(before.appointments.length);
    expect(after.appointments.find((x) => x.id === 'apt-1')?.date).toBe('2026-10-10T09:30');
    expect(after.audit[0]?.action).toBe(content.auditActions.reschedule);
  });
  it('cancellation changes status and prevents subsequent rescheduling', () => {
    const state = updateAppointment(initialState(), 'operator', 'apt-1');
    expect(state.appointments.find((x) => x.id === 'apt-1')?.status).toBe('Cancelled');
    expect(() => updateAppointment(state, 'operator', 'apt-1', '2026-10-10T12:00')).toThrow();
  });
  it('retry is idempotent and preserves the original appointment', () => {
    const before = initialState();
    const after = retryJob(before, 'operator', 'job-2');
    expect(after.appointments).toEqual(before.appointments);
    expect(after.jobs.find((x) => x.id === 'job-2')?.attempts).toBe(2);
    expect(retryJob(after, 'operator', 'job-2')).toBe(after);
  });
});
describe('role denial at the demo service boundary', () => {
  it('denies every mutating operation to Viewer', () => {
    const state = initialState();
    const operations = [
      () => confirmBooking(state, 'viewer', booking(), config),
      () => saveAgent(state, 'viewer', state.agent, config),
      () => selectVoice(state, 'viewer', 'james'),
      () => updateAppointment(state, 'viewer', 'apt-1'),
      () => retryJob(state, 'viewer', 'job-2'),
      () => addDocument(state, 'viewer', 'test.txt', 'content', config),
      () => removeDocument(state, 'viewer', 'doc-1'),
      () => toggleIntegration(state, 'viewer', 'retell'),
      () => runEvaluations(state, 'viewer'),
    ];
    for (const operation of operations) expect(operation).toThrow(content.messages.denied);
    expect(state).toEqual(initialState());
  });
});
describe('knowledge and agent validation', () => {
  it('bounds and validates plain text uploads', () => {
    const state = initialState();
    expect(() => addDocument(initialState(), 'operator', 'test.html', '<script>', config)).toThrow(
      content.messages.unsupported,
    );
    expect(() =>
      addDocument(state, 'operator', 'test.txt', 'x'.repeat(config.maxUploadBytes + 1), config),
    ).toThrow(content.messages.tooLarge);
    expect(() => addDocument(state, 'operator', 'test.txt', '\0', config)).toThrow(
      content.messages.invalidDocument,
    );
  });
  it('keeps markup as text, without evaluating it', () => {
    const text = '<script>alert(1)</script>';
    const after = addDocument(initialState(), 'operator', 'test.md', text, config);
    expect(after.documents[0]?.text).toBe(text);
  });
  it('rejects empty agent fields and invalid voice profiles', () => {
    const state = initialState();
    expect(() => saveAgent(state, 'operator', { ...state.agent, greeting: '' }, config)).toThrow();
    expect(() =>
      saveAgent(state, 'operator', { ...state.agent, voiceId: 'unknown' }, config),
    ).toThrow();
  });
  it('edits a draft without any provider operation', () => {
    const state = initialState();
    const next = saveAgent(state, 'operator', { ...state.agent, name: 'New draft' }, config);
    expect(next.agent.name).toBe('New draft');
    expect(next.integrations.every((x) => !x.connected)).toBe(true);
  });
});
