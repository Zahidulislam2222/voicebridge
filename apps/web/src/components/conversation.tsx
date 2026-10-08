import { useReducedMotion } from '../utils/motion-preference';
import { useState } from 'react';
import { motion } from 'motion/react';
import { content } from '../data';
import { settings } from '../config/settings';
import type { BookingInput, Role } from '../types';
import { Button, Field, Icon, Notice } from './ui';

export function Conversation({
  role,
  onConfirm,
}: {
  role: Role;
  onConfirm: (input: BookingInput) => string | undefined;
}) {
  const [input, setInput] = useState<BookingInput>(() => ({
    ...content.scenario,
    operationId: crypto.randomUUID(),
  }));
  const [pending, setPending] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  const reduced = useReducedMotion();
  const update = (key: keyof BookingInput, value: string | boolean) =>
    setInput((prev) => ({ ...prev, [key]: value }));
  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (pending) return;
    setPending(true);
    setError('');
    await new Promise((resolve) => setTimeout(resolve, settings.simulationDelayMs));
    const failure = onConfirm(input);
    setPending(false);
    if (failure) setError(failure);
    else setSuccess(true);
  }
  if (success)
    return (
      <div className="simulation-success">
        <span className="success-orbit">
          <Icon name="check" size={42} />
        </span>
        <h3>{content.messages.bookingCreated}</h3>
        <div className="flow-progress">
          {content.flowSteps.map((step) => (
            <div key={step}>
              <Icon name="check" size={17} />
              <span>{step}</span>
            </div>
          ))}
        </div>
        <a className="button button-primary" href="#/appointments">
          {content.labels.viewBooking}
          <Icon name="arrow" size={17} />
        </a>
        <p>{content.labels.sessionNotice}</p>
      </div>
    );
  return (
    <div className="conversation-layout">
      <div className="conversation-demo">
        <div className="voice-presence">
          <Icon name="wave" size={38} />
        </div>
        <p className="eyebrow">{content.brand}</p>
        <h3>{content.labels.bookingReady}</h3>
        <div className="transcript">
          {content.simulationTranscript.map((line, i) => (
            <motion.div
              className={`transcript-line ${line.speaker === 'Caller' ? 'caller' : ''}`}
              key={line.text}
              initial={reduced ? false : { opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{
                delay: reduced ? 0 : i * settings.animationSeconds,
                duration: settings.animationSeconds,
              }}
            >
              <span>{line.speaker}</span>
              <p>{line.text}</p>
            </motion.div>
          ))}
        </div>
        <Notice>{content.labels.simulationNotice}</Notice>
      </div>
      <form className="booking-form" onSubmit={submit}>
        <p>{content.labels.bookingReadyDetail}</p>
        <Field label={content.labels.name}>
          <input
            required
            maxLength={settings.maxTextLength}
            value={input.name}
            onChange={(e) => update('name', e.target.value)}
          />
        </Field>
        <div className="form-pair">
          <Field label={content.labels.phone}>
            <input
              type="tel"
              required
              value={input.phone}
              maxLength={settings.phoneMaxLength}
              onChange={(e) => update('phone', e.target.value)}
            />
          </Field>
          <Field label={content.labels.email}>
            <input
              type="email"
              required
              value={input.email}
              maxLength={settings.maxTextLength}
              onChange={(e) => update('email', e.target.value)}
            />
          </Field>
        </div>
        <Field label={content.labels.service}>
          <select value={input.service} onChange={(e) => update('service', e.target.value)}>
            {content.services.map((x) => (
              <option key={x}>{x}</option>
            ))}
          </select>
        </Field>
        <Field label={content.labels.date} hint={settings.timezone}>
          <input
            type="datetime-local"
            required
            value={input.date}
            onChange={(e) => update('date', e.target.value)}
          />
        </Field>
        <label className="check-field">
          <input
            type="checkbox"
            checked={input.confirmed}
            onChange={(e) => update('confirmed', e.target.checked)}
            required
          />
          <span>{content.labels.confirm}</span>
        </label>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <Button
          type="submit"
          disabled={pending || role === 'viewer'}
          icon={pending ? 'clock' : 'check'}
        >
          {pending ? content.labels.loading : content.labels.confirm}
        </Button>
        {role === 'viewer' && <p className="form-error">{content.labels.viewerNotice}</p>}
      </form>
    </div>
  );
}
