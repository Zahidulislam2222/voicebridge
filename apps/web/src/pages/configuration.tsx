import { useReducedMotion } from '../utils/motion-preference';
import { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { content } from '../data';
import { settings } from '../config/settings';
import { useWorkspace } from '../workspace';
import {
  runEvaluations,
  saveAgent,
  selectVoice,
  toggleIntegration,
} from '../services/demo-service';
import { Badge, Button, Field, Icon, Notice } from '../components/ui';
import { outcomeTone } from '../utils/format';

export function Agents() {
  const { role, mutate, agentEditor: draft, setAgentEditor: setDraft } = useWorkspace();
  const [error, setError] = useState('');
  const voice = content.voiceProfiles.find((x) => x.id === draft.voiceId);
  function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(
      mutate((state, role) => saveAgent(state, role, draft, settings), content.messages.saved) ??
        '',
    );
  }
  return (
    <div className="agent-layout">
      <section className="panel agent-form">
        <div className="panel-header">
          <div>
            <h2>{content.labels.agentDraft}</h2>
            <p>{content.labels.agentNotice}</p>
          </div>
          <Badge tone="blue">{content.labels.sample}</Badge>
        </div>
        <form onSubmit={submit}>
          <Field label={content.labels.name}>
            <input
              maxLength={settings.maxTextLength}
              required
              value={draft.name}
              onChange={(e) => setDraft({ ...draft, name: e.target.value })}
              disabled={role === 'viewer'}
            />
          </Field>
          <Field label={content.labels.greeting}>
            <textarea
              rows={4}
              required
              maxLength={settings.maxTextLength}
              value={draft.greeting}
              onChange={(e) => setDraft({ ...draft, greeting: e.target.value })}
              disabled={role === 'viewer'}
            />
          </Field>
          <Field label={content.labels.selected}>
            <select
              value={draft.voiceId}
              onChange={(e) => setDraft({ ...draft, voiceId: e.target.value })}
              disabled={role === 'viewer'}
            >
              {content.voiceProfiles.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name} · {v.style}
                </option>
              ))}
            </select>
          </Field>
          <Field label={content.labels.handoff}>
            <input
              maxLength={settings.maxTextLength}
              required
              value={draft.handoff}
              onChange={(e) => setDraft({ ...draft, handoff: e.target.value })}
              disabled={role === 'viewer'}
            />
          </Field>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          <div className="form-actions">
            <Button type="submit" disabled={role === 'viewer'} icon="check">
              {content.labels.save}
            </Button>
            <span>{content.labels.sessionNotice}</span>
          </div>
        </form>
      </section>
      <aside className="agent-preview">
        <div className="voice-presence">
          <Icon name="wave" size={42} />
        </div>
        <span className="eyebrow">{content.labels.selected}</span>
        <h2>{voice?.name}</h2>
        <p>{voice?.style}</p>
        <blockquote>{draft.greeting}</blockquote>
        <span className="preview-caption">{content.labels.agentNotice}</span>
        <a className="button button-secondary" href="#/voices">
          {content.labels.voiceProfiles}
          <Icon name="arrow" size={17} />
        </a>
      </aside>
    </div>
  );
}
export function Voices() {
  const { agentEditor, setAgentEditor, role, mutate } = useWorkspace();
  const [playing, setPlaying] = useState<string | null>(null);
  const reduced = useReducedMotion();
  useEffect(() => {
    if (!playing) return;
    const timer = setTimeout(() => setPlaying(null), settings.notificationMs);
    return () => clearTimeout(timer);
  }, [playing]);
  return (
    <>
      <Notice>{content.labels.textPreview}</Notice>
      <div className="voice-grid">
        {content.voiceProfiles.map((voice, i) => (
          <article
            className={`voice-card ${agentEditor.voiceId === voice.id ? 'voice-selected' : ''}`}
            key={voice.id}
          >
            <div className="voice-card-top">
              <span className={`voice-avatar voice-avatar-${i}`}>
                <Icon name="wave" size={36} />
              </span>
              {agentEditor.voiceId === voice.id && (
                <Badge tone="blue">{content.labels.selected}</Badge>
              )}
            </div>
            <span className="eyebrow">{voice.style}</span>
            <h2>{voice.name}</h2>
            <p>{voice.description}</p>
            <div className="waveform" aria-hidden="true">
              {voice.bars.map((height, j) => (
                <motion.span
                  key={j}
                  style={{ height: `${height}%` }}
                  animate={
                    playing === voice.id && !reduced ? { scaleY: [0.45, 1, 0.6, 1] } : { scaleY: 1 }
                  }
                  transition={{
                    duration: settings.animationSeconds * 3,
                    repeat: playing === voice.id && !reduced ? Infinity : 0,
                    delay: j * 0.015,
                  }}
                />
              ))}
            </div>
            <div className="voice-tags">
              <span>{voice.accent}</span>
              <span>{voice.tone}</span>
            </div>
            <footer>
              <Button
                variant="secondary"
                icon={playing === voice.id ? 'pause' : 'play'}
                onClick={() => setPlaying(playing === voice.id ? null : voice.id)}
                aria-pressed={playing === voice.id}
              >
                {content.labels.preview}
              </Button>
              <Button
                variant="ghost"
                disabled={role === 'viewer' || agentEditor.voiceId === voice.id}
                onClick={() => {
                  const failure = mutate(
                    (state, role) => selectVoice(state, role, voice.id),
                    content.messages.voiceSelected,
                  );
                  if (!failure) setAgentEditor({ ...agentEditor, voiceId: voice.id });
                }}
              >
                {content.labels.select}
              </Button>
            </footer>
          </article>
        ))}
      </div>
    </>
  );
}
export function Integrations() {
  const { state, role, mutate } = useWorkspace();
  return (
    <>
      <Notice>{content.labels.connectionNotice}</Notice>
      <div className="integration-grid">
        {state.integrations.map((integration) => (
          <article className="panel integration-card" key={integration.id}>
            <div className="integration-top">
              <span className={`integration-logo integration-${integration.id}`}>
                {integration.name.slice(0, 2)}
              </span>
              <Badge tone={integration.connected ? 'blue' : 'muted'}>
                {integration.connected ? content.labels.demo : content.fixedLabels.disconnected}
              </Badge>
            </div>
            <span className="eyebrow">{integration.category}</span>
            <h2>{integration.name}</h2>
            <p>{integration.description}</p>
            <Button
              variant="secondary"
              disabled={role === 'viewer'}
              icon="link"
              onClick={() =>
                mutate(
                  (state, role) => toggleIntegration(state, role, integration.id),
                  content.messages.connected,
                )
              }
            >
              {integration.connected ? content.labels.disconnect : content.labels.connect}
            </Button>
          </article>
        ))}
      </div>
    </>
  );
}
export function Evaluations() {
  const { state, role, mutate } = useWorkspace();
  const [busy, setBusy] = useState(false);
  async function run() {
    if (busy) return;
    setBusy(true);
    await new Promise((resolve) => setTimeout(resolve, settings.simulationDelayMs));
    mutate((state, role) => runEvaluations(state, role), content.messages.evaluation);
    setBusy(false);
  }
  return (
    <>
      <Notice>{content.messages.evaluation}</Notice>
      <div className="page-toolbar">
        <span>
          {content.labels.sample} · {state.evaluations.length}{' '}
          {content.labels.conversation.toLowerCase()}
        </span>
        <Button icon="play" disabled={role === 'viewer' || busy} onClick={() => void run()}>
          {busy ? content.labels.loading : content.labels.run}
        </Button>
      </div>
      <section className="panel evaluation-list">
        {state.evaluations.map((evaluation, i) => (
          <article key={evaluation.id}>
            <span className="evaluation-number">0{i + 1}</span>
            <div>
              <h2>{evaluation.name}</h2>
              <p>{evaluation.expectation}</p>
            </div>
            <Badge tone={outcomeTone(evaluation.result)}>{evaluation.result}</Badge>
          </article>
        ))}
      </section>
    </>
  );
}
export function Usage() {
  const { state } = useWorkspace();
  const metrics = [
    {
      label: content.labels.totalCalls,
      value: state.calls.length,
      unit: content.usageUnits.conversation,
      icon: 'phone',
    },
    {
      label: content.labels.minutes,
      value: Math.round(state.calls.reduce((s, c) => s + c.duration, 0) / 60),
      unit: content.usageUnits.minute,
      icon: 'clock',
    },
    {
      label: content.labels.bookings,
      value: state.appointments.filter((x) => x.status === 'Confirmed').length,
      unit: content.labels.bookings.toLowerCase(),
      icon: 'calendar',
    },
    {
      label: content.labels.log,
      value: state.jobs.length,
      unit: content.usageUnits.job,
      icon: 'flow',
    },
  ];
  return (
    <>
      <Notice>{content.labels.usageNotice}</Notice>
      <section className="usage-panel panel">
        <div className="panel-header">
          <div>
            <h2>{content.labels.workspace}</h2>
            <p>
              {content.business} · {content.labels.sample}
            </p>
          </div>
          <Badge>{content.labels.demo}</Badge>
        </div>
        {metrics.map((metric) => (
          <div className="usage-row" key={metric.label}>
            <span className="usage-icon">
              <Icon name={metric.icon} size={20} />
            </span>
            <div>
              <h3>{metric.label}</h3>
              <p>{metric.unit}</p>
            </div>
            <strong>{metric.value}</strong>
          </div>
        ))}
      </section>
      <div className="usage-footer">
        <Icon name="shield" size={22} />
        <p>
          {content.labels.usageNotice}
          <br />
          {content.labels.sessionNotice}
        </p>
      </div>
    </>
  );
}
