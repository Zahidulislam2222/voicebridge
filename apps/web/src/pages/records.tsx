import { useState, useRef } from 'react';
import { content, outcomes } from '../data';
import { settings } from '../config/settings';
import { useWorkspace } from '../workspace';
import { addDocument } from '../services/demo-service';
import { Badge, Button, Empty, Icon, Notice } from '../components/ui';
import { formatDate, outcomeTone } from '../utils/format';
import { CallsTable } from './overview';

export function Calls() {
  const { state, query, setQuery } = useWorkspace();
  const [outcome, setOutcome] = useState('');
  const filtered = state.calls.filter(
    (call) =>
      (!outcome || call.outcome === outcome) &&
      `${call.name} ${call.phone} ${call.service} ${call.summary}`
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  return (
    <section className="panel">
      <div className="filter-row">
        <span>
          {filtered.length} {content.usageUnits.conversation}
        </span>
        <label className="select-label">
          <span className="sr-only">{content.labels.filter}</span>
          <select value={outcome} onChange={(e) => setOutcome(e.target.value)}>
            <option value="">{content.labels.all}</option>
            {outcomes.map((x) => (
              <option key={x}>{x}</option>
            ))}
          </select>
        </label>
        {(query || outcome) && (
          <Button
            variant="ghost"
            onClick={() => {
              setQuery('');
              setOutcome('');
            }}
          >
            {content.labels.reset}
          </Button>
        )}
      </div>
      {filtered.length ? (
        <CallsTable calls={filtered} />
      ) : (
        <Empty
          action={
            <Button
              variant="secondary"
              onClick={() => {
                setQuery('');
                setOutcome('');
              }}
            >
              {content.labels.reset}
            </Button>
          }
        />
      )}
    </section>
  );
}
export function Appointments() {
  const { state, query, open } = useWorkspace();
  const [filter, setFilter] = useState('');
  const list = state.appointments
    .filter(
      (x) =>
        (!filter || x.status === filter) &&
        `${x.name} ${x.service}`.toLowerCase().includes(query.toLowerCase()),
    )
    .sort((a, b) => a.date.localeCompare(b.date));
  const dates = [...new Set(list.map((x) => x.date.slice(0, 10)))];
  return (
    <>
      <div className="page-toolbar">
        <div className="segmented" aria-label={content.labels.status}>
          {[
            ['', content.labels.allAppointments],
            ['Confirmed', content.labels.activeAppointments],
            ['Cancelled', content.labels.cancelledAppointments],
          ].map(([id, label]) => (
            <button
              key={id}
              aria-pressed={filter === id}
              className={filter === id ? 'active' : ''}
              onClick={() => setFilter(id ?? '')}
            >
              {label}
            </button>
          ))}
        </div>
        <span className="muted">{settings.timezone}</span>
      </div>
      {list.length ? (
        <div className="appointment-days">
          {dates.map((date) => (
            <section className="appointment-day" key={date}>
              <div className="day-heading">
                <span>{formatDate(date + 'T12:00')}</span>
                <small>{content.labels.sample}</small>
              </div>
              <div className="panel appointment-list">
                {list
                  .filter((x) => x.date.startsWith(date))
                  .map((apt) => (
                    <button
                      className="appointment-row"
                      key={apt.id}
                      onClick={() => open({ type: 'appointment', id: apt.id })}
                    >
                      <span className="appointment-time">
                        {apt.date.slice(11)}
                        <small>{settings.timezone.split('/')[1]?.replace('_', ' ')}</small>
                      </span>
                      <span className="appointment-main">
                        <strong>{apt.name}</strong>
                        <small>{apt.service}</small>
                      </span>
                      <Badge tone={outcomeTone(apt.status)}>{apt.status}</Badge>
                      <Icon name="chevron" size={18} />
                    </button>
                  ))}
              </div>
            </section>
          ))}
        </div>
      ) : (
        <section className="panel">
          <Empty title={content.labels.noAppointments} />
        </section>
      )}
    </>
  );
}
export function Contacts() {
  const { state, query, open } = useWorkspace();
  const list = state.contacts.filter((x) =>
    `${x.name} ${x.phone} ${x.email}`.toLowerCase().includes(query.toLowerCase()),
  );
  return (
    <section className="panel">
      {list.length ? (
        <div className="table-scroll">
          <table className="records-table">
            <thead>
              <tr>
                <th>{content.labels.contact}</th>
                <th>{content.labels.email}</th>
                <th>{content.labels.conversation}</th>
                <th>{content.labels.details}</th>
              </tr>
            </thead>
            <tbody>
              {list.map((contact) => (
                <tr key={contact.id}>
                  <td>
                    <button
                      className="person-link"
                      onClick={() => open({ type: 'contact', id: contact.id })}
                    >
                      <span className="avatar">{contact.initials}</span>
                      <span>
                        <strong>{contact.name}</strong>
                        <small>{contact.phone}</small>
                      </span>
                    </button>
                  </td>
                  <td>{contact.email}</td>
                  <td className="tabular">
                    {state.calls.filter((x) => x.contactId === contact.id).length}
                  </td>
                  <td>
                    <Button
                      variant="ghost"
                      onClick={() => open({ type: 'contact', id: contact.id })}
                      icon="arrow"
                    >
                      {content.labels.details}
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <Empty />
      )}
    </section>
  );
}
export function Automations() {
  const { state, query, open } = useWorkspace();
  const list = state.jobs.filter((x) =>
    `${x.name} ${x.status}`.toLowerCase().includes(query.toLowerCase()),
  );
  return (
    <>
      <div className="automation-flow">
        {content.timeline.map((step, i) => (
          <div key={step.title}>
            <span className="step-circle">{i + 1}</span>
            <strong>{step.title}</strong>
            <small>{step.text}</small>
            {i < content.timeline.length - 1 && <Icon name="arrow" size={18} />}
          </div>
        ))}
      </div>
      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>{content.labels.flowTitle}</h2>
            <p>{content.labels.flowSubtitle}</p>
          </div>
          <Badge>{content.labels.sample}</Badge>
        </div>
        {list.length ? (
          <div className="table-scroll">
            <table className="records-table">
              <thead>
                <tr>
                  <th>{content.labels.action}</th>
                  <th>{content.labels.booking}</th>
                  <th>{content.labels.status}</th>
                  <th>{content.labels.attempts}</th>
                  <th>{content.labels.details}</th>
                </tr>
              </thead>
              <tbody>
                {list.map((job) => (
                  <tr key={job.id}>
                    <td>
                      <span className="table-icon">
                        <Icon name="flow" size={19} />
                        {job.name}
                      </span>
                    </td>
                    <td>{state.appointments.find((x) => x.id === job.appointmentId)?.name}</td>
                    <td>
                      <Badge tone={outcomeTone(job.status)}>{job.status}</Badge>
                    </td>
                    <td className="tabular">{job.attempts}</td>
                    <td>
                      <Button
                        variant="ghost"
                        onClick={() => open({ type: 'job', id: job.id })}
                        icon="arrow"
                      >
                        {content.labels.review}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty />
        )}
      </section>
    </>
  );
}
export function Knowledge() {
  const { state, role, query, mutate, open } = useWorkspace();
  const ref = useRef<HTMLInputElement>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function upload(file: File | undefined) {
    if (!file) return;
    setError('');
    if (file.size > settings.maxUploadBytes) {
      setError(content.messages.tooLarge);
      return;
    }
    if (!/\.(txt|md)$/i.test(file.name)) {
      setError(content.messages.unsupported);
      return;
    }
    setBusy(true);
    try {
      const text = new TextDecoder('utf-8', { fatal: true }).decode(await file.arrayBuffer());
      const failure = mutate(
        (state, role) => addDocument(state, role, file.name, text, settings),
        content.messages.uploaded,
      );
      if (failure) setError(failure);
    } catch {
      setError(content.messages.invalidDocument);
    } finally {
      setBusy(false);
      if (ref.current) ref.current.value = '';
    }
  }
  const list = state.documents.filter((x) =>
    `${x.name} ${x.text}`.toLowerCase().includes(query.toLowerCase()),
  );
  return (
    <>
      <Notice>
        {content.labels.knowledgeNotice} · {Math.round(settings.maxUploadBytes / 1024)} KB
      </Notice>
      <div className="page-toolbar">
        <span>
          {state.documents.length} {content.usageUnits.document}
        </span>
        <Button
          icon="upload"
          disabled={role === 'viewer' || busy}
          onClick={() => ref.current?.click()}
        >
          {busy ? content.labels.loading : content.labels.upload}
        </Button>
        <input
          ref={ref}
          className="sr-only"
          type="file"
          disabled={role === 'viewer' || busy}
          accept=".txt,.md,text/plain,text/markdown"
          aria-label={content.labels.upload}
          onChange={(e) => void upload(e.target.files?.[0])}
        />
      </div>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      <div className="knowledge-grid">
        {list.map((doc) => (
          <button
            className="panel document-card"
            key={doc.id}
            onClick={() => open({ type: 'document', id: doc.id })}
          >
            <span className="document-icon">
              <Icon name="book" size={26} />
            </span>
            <div>
              <h2>{doc.name}</h2>
              <p>{doc.text}</p>
            </div>
            <footer>
              <span>{doc.updated}</span>
              <Icon name="arrow" size={18} />
            </footer>
          </button>
        ))}
      </div>
      {!list.length && (
        <section className="panel">
          <Empty />
        </section>
      )}
    </>
  );
}
export function Audit() {
  const { state, query } = useWorkspace();
  const list = state.audit.filter((x) =>
    `${x.action} ${x.detail}`.toLowerCase().includes(query.toLowerCase()),
  );
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h2>{content.labels.log}</h2>
          <p>{content.labels.sessionNotice}</p>
        </div>
        <Badge>{content.labels.sample}</Badge>
      </div>
      <div className="audit-timeline">
        {list.map((event) => (
          <article key={event.id}>
            <span className="audit-icon">
              <Icon name="clock" size={18} />
            </span>
            <div>
              <h3>{event.action}</h3>
              <p>{event.detail}</p>
            </div>
            <time dateTime={event.date}>{formatDate(event.date, true)}</time>
          </article>
        ))}
      </div>
      {!list.length && <Empty />}
    </section>
  );
}
