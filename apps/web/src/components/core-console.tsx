import { useEffect, useState } from 'react';
import { agentDraft, bookingNotice, CoreClient } from '../services/core-client';
import type {
  Agent,
  AgentRecord,
  Booking,
  BookingRecord,
  CoreSnapshot,
} from '../services/core-client';
import { settings } from '../config/settings';
import copy from '../data/core-console';
import type { CorePage } from '../protocol';
import { Brand, Button, Field, Notice } from './ui';
import './core-console.css';

export function CoreConsole() {
  const [credential, setCredential] = useState('');
  const [client, setClient] = useState<CoreClient | null>(null);
  const [state, setState] = useState<CoreSnapshot | null>(null);
  const [page, setPage] = useState<CorePage>('overview');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [pending, setPending] = useState(false);
  const [bootstrap, setBootstrap] = useState<{
    services: Record<string, number>;
    timezone: string;
  } | null>(null);
  const [booking, setBooking] = useState<Partial<Booking>>({ confirmed: false });
  const [operation, setOperation] = useState(() => crypto.randomUUID());
  const [document, setDocument] = useState({ name: '', text: '' });
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState<{
    answer: string;
    sources: { name: string; revision: number }[];
  } | null>(null);
  const [evaluation, setEvaluation] = useState<{ cases: { id: string; passed: boolean }[] } | null>(
    null,
  );
  const [agent, setAgent] = useState<Agent | null>(null);
  useEffect(() => {
    if (!settings.coreSessionAuth) return;
    let alive = true;
    const probe = new CoreClient('');
    void probe
      .request<{ csrf: string }>('/auth/session')
      .then(async (session) => {
        const next = new CoreClient('', session.csrf);
        const boot = await next.request<{ services: Record<string, number>; timezone: string }>(
          '/api/bootstrap',
        );
        const snapshot = await next.state();
        if (alive) {
          setBootstrap(boot);
          setState(snapshot);
          setClient(next);
        }
      })
      .catch(() => {
        if (alive) setClient(null);
      });
    return () => {
      alive = false;
    };
  }, []);
  async function refresh(active = client) {
    if (!active) return;
    const next = await active.state();
    setState(next);
  }
  useEffect(() => {
    if (!client) return;
    let alive = true;
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      try {
        const next = await client!.state(controller.signal);
        if (alive) setState(next);
      } catch {
        if (alive) setError(copy.unavailable);
      } finally {
        if (alive)
          timer = setTimeout(() => {
            void poll();
          }, settings.corePollMs);
      }
    }
    timer = setTimeout(() => {
      void poll();
    }, settings.corePollMs);
    return () => {
      alive = false;
      controller.abort();
      clearTimeout(timer);
    };
  }, [client]);
  async function action(run: () => Promise<unknown>, message = copy.saved, refreshAfter = true) {
    if (pending) return;
    setPending(true);
    setError('');
    setNotice('');
    try {
      const result = await run();
      if (refreshAfter) await refresh();
      setNotice(typeof result === 'string' ? result : message);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : copy.unavailable);
    } finally {
      setPending(false);
    }
  }
  async function connect(event: React.FormEvent) {
    event.preventDefault();
    const next = new CoreClient(credential);
    await action(async () => {
      const boot = await next.request<{ services: Record<string, number>; timezone: string }>(
        '/api/bootstrap',
      );
      setBootstrap(boot);
      await refresh(next);
      setClient(next);
      setCredential('');
    });
  }
  const update = (key: keyof Booking, value: string | boolean) => {
    setBooking((prev) => ({ ...prev, [key]: value }));
    setOperation(crypto.randomUUID());
  };
  return (
    <main className="core-console">
      <header className="core-header">
        <Brand />
        <a href="#/welcome">{copy.back}</a>
      </header>
      <h1>{copy.title}</h1>
      <Notice>{copy.subtitle}</Notice>
      {error && (
        <p role="alert" className="form-error">
          {error}
        </p>
      )}
      {notice && <p role="status">{notice}</p>}
      {!client && settings.coreSessionAuth ? (
        <a className="button button-primary" href={settings.coreApiUrl + '/auth/login'}>
          {copy.login}
        </a>
      ) : !client ? (
        <form onSubmit={connect} className="core-form">
          <Field label={copy.credential}>
            <input
              autoComplete="off"
              type="password"
              required
              value={credential}
              onChange={(e) => setCredential(e.target.value)}
            />
          </Field>
          <p>{settings.coreApiUrl ? copy.connectionHint : copy.disabled}</p>
          <Button disabled={pending || !settings.coreApiUrl} type="submit">
            {copy.connect}
          </Button>
        </form>
      ) : (
        <>
          <div className="core-toolbar">
            <Button
              disabled={pending}
              onClick={() => {
                void action(() => refresh());
              }}
            >
              {copy.refresh}
            </Button>
            <Button
              disabled={pending}
              onClick={() => {
                if (settings.coreSessionAuth && client) {
                  void action(
                    async () => {
                      await client.request('/auth/logout', 'POST');
                      setClient(null);
                      setState(null);
                      setBootstrap(null);
                      setAgent(null);
                    },
                    copy.logout,
                    false,
                  );
                  return;
                }
                setClient(null);
                setState(null);
                setCredential('');
                setAgent(null);
              }}
            >
              {settings.coreSessionAuth ? copy.logout : copy.disconnect}
            </Button>
          </div>
          <nav aria-label={copy.title} className="core-navigation">
            {copy.navigation.map((item) => (
              <button
                className={page === item.id ? 'active' : ''}
                onClick={() => {
                  setPage(item.id);
                  if (item.id === 'agent' && state?.agent) setAgent(agentDraft(state.agent));
                }}
                key={item.id}
              >
                {item.label}
              </button>
            ))}
          </nav>
          {state && (
            <section>
              <h2>{copy.navigation.find((item) => item.id === page)?.label}</h2>
              {page === 'overview' && (
                <div className="core-metrics">
                  {[
                    ['Appointments', state.counts.appointments],
                    ['Contacts', state.counts.contacts],
                    ['Calls', state.counts.calls],
                    ['Jobs', state.counts.jobs],
                  ].map(([label, count]) => (
                    <div className="panel" key={label}>
                      <strong>{count}</strong>
                      <p>{label}</p>
                    </div>
                  ))}
                </div>
              )}
              {(page === 'overview' || page === 'appointments') && (
                <>
                  <form
                    className="core-form"
                    onSubmit={(e) => {
                      e.preventDefault();
                      void action(async () => {
                        const result = await client.request<{ status: string }>(
                          '/api/bookings',
                          'POST',
                          {
                            ...booking,
                            operation_id: operation,
                          },
                        );
                        return bookingNotice(result.status, 'create');
                      }, copy.pending);
                    }}
                  >
                    <h3>{copy.booking}</h3>
                    <Field label={copy.fieldLabels.name}>
                      <input
                        required
                        value={booking.name ?? ''}
                        onChange={(e) => update('name', e.target.value)}
                      />
                    </Field>
                    <Field label={copy.fieldLabels.email}>
                      <input
                        required
                        type="email"
                        value={booking.email ?? ''}
                        onChange={(e) => update('email', e.target.value)}
                      />
                    </Field>
                    <Field label={copy.fieldLabels.phone}>
                      <input
                        required
                        type="tel"
                        value={booking.phone ?? ''}
                        onChange={(e) => update('phone', e.target.value)}
                      />
                    </Field>
                    <Field label={copy.fieldLabels.service}>
                      <select
                        required
                        value={booking.service ?? ''}
                        onChange={(e) => update('service', e.target.value)}
                      >
                        <option value="">{copy.chooseService}</option>
                        {Object.keys(bootstrap?.services ?? {}).map((service) => (
                          <option key={service}>{service}</option>
                        ))}
                      </select>
                    </Field>
                    <Field label={copy.fieldLabels.start} hint={bootstrap?.timezone}>
                      <input
                        required
                        placeholder={copy.startPlaceholder}
                        value={booking.start ?? ''}
                        onChange={(e) => update('start', e.target.value)}
                      />
                    </Field>
                    <label className="core-confirm">
                      <input
                        type="checkbox"
                        required
                        checked={booking.confirmed ?? false}
                        onChange={(e) => update('confirmed', e.target.checked)}
                      />
                      {copy.confirm}
                    </label>
                    <Button disabled={pending} type="submit">
                      {copy.booking}
                    </Button>
                  </form>
                  {state.appointments.map((row) => (
                    <article className="panel core-record" key={row.id}>
                      <h3>{row.service}</h3>
                      <p>
                        {row.start} · {row.status} · {copy.revision} {row.revision}
                      </p>
                      <code>{row.id}</code>
                      {row.status === 'confirmed' && (
                        <form
                          onSubmit={(e) => {
                            e.preventDefault();
                            const form = new FormData(e.currentTarget);
                            void action(async () => {
                              const result = await client.request<BookingRecord>(
                                `/api/bookings/${row.id}`,
                                'POST',
                                {
                                  operation_id: crypto.randomUUID(),
                                  action: 'reschedule',
                                  start: String(form.get('start')),
                                  confirmed: true,
                                  expected_revision: row.revision,
                                },
                              );
                              return bookingNotice(result.status, 'reschedule');
                            });
                          }}
                        >
                          <input
                            name="start"
                            aria-label={copy.newStart}
                            required
                            placeholder={copy.startPlaceholder}
                          />
                          <Button disabled={pending} type="submit">
                            {copy.reschedule}
                          </Button>
                          <Button
                            disabled={pending}
                            onClick={() => {
                              if (window.confirm(copy.cancelPrompt))
                                void action(async () => {
                                  const result = await client.request<BookingRecord>(
                                    `/api/bookings/${row.id}`,
                                    'POST',
                                    {
                                      operation_id: crypto.randomUUID(),
                                      action: 'cancel',
                                      confirmed: true,
                                      expected_revision: row.revision,
                                    },
                                  );
                                  return bookingNotice(result.status, 'cancel');
                                });
                            }}
                          >
                            {copy.cancel}
                          </Button>
                        </form>
                      )}
                    </article>
                  ))}
                </>
              )}
              {page === 'knowledge' && (
                <>
                  <form
                    className="core-form"
                    onSubmit={(e) => {
                      e.preventDefault();
                      void action(() => client.request('/api/knowledge', 'POST', document));
                    }}
                  >
                    <Field label={copy.fieldLabels.documentName}>
                      <input
                        required
                        value={document.name}
                        onChange={(e) => setDocument({ ...document, name: e.target.value })}
                      />
                    </Field>
                    <Field label={copy.fieldLabels.approvedText}>
                      <textarea
                        required
                        value={document.text}
                        onChange={(e) => setDocument({ ...document, text: e.target.value })}
                      />
                    </Field>
                    <Button type="submit" disabled={pending}>
                      {copy.save}
                    </Button>
                  </form>
                  <form
                    className="core-form"
                    onSubmit={(e) => {
                      e.preventDefault();
                      void action(async () =>
                        setAnswer(
                          await client.request(
                            `/api/knowledge/answer?query=${encodeURIComponent(query)}`,
                          ),
                        ),
                      );
                    }}
                  >
                    <Field label={copy.query}>
                      <input required value={query} onChange={(e) => setQuery(e.target.value)} />
                    </Field>
                    <Button type="submit" disabled={pending}>
                      {copy.query}
                    </Button>
                  </form>
                  {answer && (
                    <article className="panel">
                      <p>{answer.answer}</p>
                      {answer.sources.map((source) => (
                        <p key={source.name}>
                          {source.name} · {source.revision}
                        </p>
                      ))}
                    </article>
                  )}
                  {state.documents.map((row) => (
                    <article className="panel core-record" key={row.id}>
                      <h3>{row.name}</h3>
                      <p>{row.text}</p>
                      <p>
                        {copy.revision} {row.revision}
                      </p>
                      <Button
                        disabled={pending}
                        onClick={() => {
                          if (window.confirm(copy.removePrompt))
                            void action(() => client.request(`/api/knowledge/${row.id}`, 'DELETE'));
                        }}
                      >
                        {copy.remove}
                      </Button>
                    </article>
                  ))}
                </>
              )}
              {page === 'agent' && agent && (
                <form
                  className="core-form"
                  onSubmit={(e) => {
                    e.preventDefault();
                    void action(async () => {
                      const result = await client.request<AgentRecord>('/api/agent', 'PUT', agent);
                      setAgent(agentDraft(result));
                    });
                  }}
                >
                  {(['name', 'greeting', 'handoff', 'voice_id'] as const).map((field) => (
                    <Field key={field} label={copy.fieldLabels[field]}>
                      <input
                        required
                        value={agent[field]}
                        onChange={(e) => setAgent({ ...agent, [field]: e.target.value })}
                      />
                    </Field>
                  ))}
                  <Button type="submit" disabled={pending}>
                    {copy.save}
                  </Button>
                </form>
              )}
              {page === 'automations' &&
                state.jobs.map((row) => (
                  <article className="panel core-record" key={row.id}>
                    <h3>
                      {row.kind} · {row.status}
                    </h3>
                    <p>
                      {row.detail} · {copy.attempts} {row.attempts}
                    </p>
                    <p>{row.receipt}</p>
                    {['dead', 'failed'].includes(row.status) && (
                      <Button
                        disabled={pending}
                        onClick={() => {
                          void action(() => client.request(`/api/jobs/${row.id}/replay`, 'POST'));
                        }}
                      >
                        {copy.retry}
                      </Button>
                    )}
                    {row.kind === 'calendar' && ['reconcile', 'unknown'].includes(row.status) && (
                      <Button
                        disabled={pending}
                        onClick={() => {
                          void action(() =>
                            client.request(`/api/jobs/${row.id}/reconcile`, 'POST'),
                          );
                        }}
                      >
                        {copy.reconcile}
                      </Button>
                    )}
                  </article>
                ))}
              {page === 'contacts' &&
                state.contacts.map((row) => (
                  <article className="panel core-record" key={row.id}>
                    <h3>{row.name}</h3>
                    <p>
                      {row.email} · {row.phone}
                    </p>
                    <p>{row.notes}</p>
                  </article>
                ))}
              {page === 'calls' &&
                state.calls.map((row) => (
                  <article className="panel core-record" key={row.id}>
                    <h3>
                      {row.provider} · {row.state}
                    </h3>
                    <p>{row.date}</p>
                    {row.transcript.map((line, i) => (
                      <p key={i}>
                        {line.speaker}: {line.text}
                      </p>
                    ))}
                  </article>
                ))}
              {page === 'integrations' &&
                Object.entries(state.integrations).map(([name, status]) => (
                  <article className="panel core-record" key={name}>
                    <h3>{name}</h3>
                    <p>{status}</p>
                  </article>
                ))}
              {page === 'evaluations' && (
                <>
                  <Button
                    disabled={pending}
                    onClick={() => {
                      void action(async () =>
                        setEvaluation(await client.request('/api/evaluations', 'POST')),
                      );
                    }}
                  >
                    {copy.evaluate}
                  </Button>
                  <p>{copy.acoustic}</p>
                  <h3>{copy.evaluationFixtures}</h3>
                  {state.evaluation_fixtures.map((fixture) => (
                    <article className="panel core-record" key={fixture.id}>
                      <code>{fixture.id}</code>
                      <p>
                        {fixture.status} · {fixture.detail}
                      </p>
                      {fixture.status !== 'completed' && (
                        <Button
                          disabled={pending}
                          onClick={() => {
                            void action(async () => {
                              const result = await client.request<{ status: string }>(
                                `/api/evaluations/${fixture.id}/cleanup`,
                                'POST',
                              );
                              return result.status === 'completed' ? copy.saved : copy.pending;
                            });
                          }}
                        >
                          {copy.cleanup}
                        </Button>
                      )}
                    </article>
                  ))}
                  {evaluation?.cases.map((row) => (
                    <p key={row.id}>
                      {row.id} · {row.passed ? copy.passed : copy.needsReview}
                    </p>
                  ))}
                </>
              )}
              {page === 'audit' &&
                state.audit.map((row) => (
                  <article className="panel core-record" key={row.id}>
                    <h3>{row.action}</h3>
                    <p>
                      {row.date} · {row.target}
                    </p>
                  </article>
                ))}
            </section>
          )}
        </>
      )}
    </main>
  );
}
