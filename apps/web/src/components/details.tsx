import { useState } from 'react';
import { content } from '../data';
import { settings } from '../config/settings';
import { useWorkspace } from '../workspace';
import type { ModalState } from '../workspace';
import { removeDocument, retryJob, updateAppointment } from '../services/demo-service';
import { Badge, Button, Empty, Field, Icon, Notice } from './ui';
import { duration, formatDate, outcomeTone } from '../utils/format';

export function RecordDetails({
  modal,
}: {
  modal: Exclude<ModalState, null | { type: 'simulation' }>;
}) {
  const { state, role, open, mutate } = useWorkspace();
  const [confirm, setConfirm] = useState(false);
  const [date, setDate] = useState('');
  const [reschedule, setReschedule] = useState(false);
  const [error, setError] = useState('');
  if (modal.type === 'call') {
    const call = state.calls.find((x) => x.id === modal.id);
    if (!call) return <Empty />;
    return (
      <>
        <div className="detail-person">
          <span className="avatar avatar-large">{call.initials}</span>
          <div>
            <h3>{call.name}</h3>
            <p>{call.phone}</p>
          </div>
          <Badge tone={outcomeTone(call.outcome)}>{call.outcome}</Badge>
        </div>
        <div className="detail-stats">
          <span>
            <small>{content.labels.duration}</small>
            <strong>{duration(call.duration)}</strong>
          </span>
          <span>
            <small>{content.labels.service}</small>
            <strong>{call.service}</strong>
          </span>
          <span>
            <small>{content.labels.sample}</small>
            <strong>{formatDate(call.date, true)}</strong>
          </span>
        </div>
        <p className="detail-summary">{call.summary}</p>
        <h3 className="section-label">{content.labels.conversation}</h3>
        <div className="detail-transcript">
          {call.transcript.map((line, i) => (
            <div key={i} className="transcript-line">
              <span>{line.speaker}</span>
              <p>{line.text}</p>
            </div>
          ))}
        </div>
        <div className="detail-actions">
          <Button
            variant="secondary"
            onClick={() => open({ type: 'contact', id: call.contactId })}
            icon="users"
          >
            {content.labels.viewContact}
          </Button>
          {call.appointmentId && (
            <Button
              onClick={() => open({ type: 'appointment', id: call.appointmentId ?? '' })}
              icon="calendar"
            >
              {content.labels.viewBooking}
            </Button>
          )}
        </div>
      </>
    );
  }
  if (modal.type === 'contact') {
    const contact = state.contacts.find((x) => x.id === modal.id);
    if (!contact) return <Empty />;
    const calls = state.calls.filter((x) => x.contactId === contact.id);
    return (
      <>
        <div className="detail-person">
          <span className="avatar avatar-large">{contact.initials}</span>
          <div>
            <h3>{contact.name}</h3>
            <p>{contact.email}</p>
          </div>
        </div>
        <dl className="detail-list">
          <dt>{content.labels.phone}</dt>
          <dd>{contact.phone}</dd>
          <dt>{content.labels.details}</dt>
          <dd>{contact.notes}</dd>
        </dl>
        <h3 className="section-label">{content.labels.conversation}</h3>
        <div className="linked-calls">
          {calls.map((call) => (
            <button key={call.id} onClick={() => open({ type: 'call', id: call.id })}>
              <span>
                <strong>{call.service}</strong>
                <small>{formatDate(call.date, true)}</small>
              </span>
              <Badge tone={outcomeTone(call.outcome)}>{call.outcome}</Badge>
              <Icon name="chevron" size={17} />
            </button>
          ))}
        </div>
        {!calls.length && <Empty title={content.labels.noContactCalls} />}
      </>
    );
  }
  if (modal.type === 'appointment') {
    const apt = state.appointments.find((x) => x.id === modal.id);
    if (!apt) return <Empty />;
    function update(newDate?: string) {
      const failure = mutate(
        (state, role) => updateAppointment(state, role, modal.id, newDate),
        newDate ? content.messages.rescheduled : content.messages.cancelled,
      );
      setError(failure ?? '');
      if (!failure) {
        setConfirm(false);
        setReschedule(false);
      }
    }
    return (
      <>
        <div className="detail-person">
          <span className="detail-icon">
            <Icon name="calendar" size={26} />
          </span>
          <div>
            <h3>{apt.name}</h3>
            <p>{apt.service}</p>
          </div>
          <Badge tone={outcomeTone(apt.status)}>{apt.status}</Badge>
        </div>
        <div className="appointment-feature">
          <span>{content.labels.date}</span>
          <strong>{formatDate(apt.date, true)}</strong>
          <small>{settings.timezone}</small>
        </div>
        <Notice>{content.labels.demoNotice}</Notice>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        {confirm ? (
          <div className="confirmation-box">
            <h3>{content.labels.confirmCancel}</h3>
            <p>{content.labels.confirmCancelDetail}</p>
            <div className="detail-actions">
              <Button variant="secondary" onClick={() => setConfirm(false)}>
                {content.labels.back}
              </Button>
              <Button variant="danger" disabled={role === 'viewer'} onClick={() => update()}>
                {content.labels.cancelBooking}
              </Button>
            </div>
          </div>
        ) : reschedule ? (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              update(date);
            }}
            className="reschedule-form"
          >
            <Field label={content.labels.date}>
              <input
                type="datetime-local"
                required
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />
            </Field>
            <label className="check-field">
              <input type="checkbox" required />
              <span>{content.labels.confirm}</span>
            </label>
            <div className="detail-actions">
              <Button variant="secondary" type="button" onClick={() => setReschedule(false)}>
                {content.labels.back}
              </Button>
              <Button type="submit" disabled={role === 'viewer'}>
                {content.labels.reschedule}
              </Button>
            </div>
          </form>
        ) : (
          <div className="detail-actions">
            <Button
              variant="secondary"
              icon="users"
              onClick={() => open({ type: 'contact', id: apt.contactId })}
            >
              {content.labels.viewContact}
            </Button>
            {apt.status === 'Confirmed' && (
              <>
                <Button
                  disabled={role === 'viewer'}
                  onClick={() => {
                    setDate(apt.date);
                    setReschedule(true);
                  }}
                >
                  {content.labels.reschedule}
                </Button>
                <Button
                  variant="ghost"
                  disabled={role === 'viewer'}
                  onClick={() => setConfirm(true)}
                >
                  {content.labels.cancelBooking}
                </Button>
              </>
            )}
          </div>
        )}
      </>
    );
  }
  if (modal.type === 'job') {
    const job = state.jobs.find((x) => x.id === modal.id);
    if (!job) return <Empty />;
    return (
      <>
        <div className="detail-person">
          <span className="detail-icon">
            <Icon name="flow" size={26} />
          </span>
          <div>
            <h3>{job.name}</h3>
            <p>
              {content.labels.attempts}: {job.attempts}
            </p>
          </div>
          <Badge tone={outcomeTone(job.status)}>{job.status}</Badge>
        </div>
        <Notice warning={job.status === 'Failed'}>{job.detail}</Notice>
        <div className="detail-actions">
          <Button
            variant="secondary"
            icon="calendar"
            onClick={() => open({ type: 'appointment', id: job.appointmentId })}
          >
            {content.labels.viewBooking}
          </Button>
          {job.status === 'Failed' && (
            <Button
              disabled={role === 'viewer'}
              icon="flow"
              onClick={() =>
                mutate((state, role) => retryJob(state, role, job.id), content.messages.retried)
              }
            >
              {content.labels.retry}
            </Button>
          )}
        </div>
      </>
    );
  }
  const doc = state.documents.find((x) => x.id === modal.id);
  if (!doc) return <Empty />;
  return (
    <>
      <div className="document-detail">
        <h3>{doc.name}</h3>
        <p>{doc.updated}</p>
        <pre>{doc.text}</pre>
      </div>
      {confirm ? (
        <div className="confirmation-box">
          <h3>{content.labels.confirmRemove}</h3>
          <div className="detail-actions">
            <Button variant="secondary" onClick={() => setConfirm(false)}>
              {content.labels.cancel}
            </Button>
            <Button
              variant="danger"
              disabled={role === 'viewer'}
              onClick={() => {
                const failure = mutate(
                  (state, role) => removeDocument(state, role, doc.id),
                  content.messages.removed,
                );
                if (!failure) open(null);
              }}
            >
              {content.labels.remove}
            </Button>
          </div>
        </div>
      ) : (
        <Button variant="ghost" disabled={role === 'viewer'} onClick={() => setConfirm(true)}>
          {content.labels.remove}
        </Button>
      )}
    </>
  );
}
