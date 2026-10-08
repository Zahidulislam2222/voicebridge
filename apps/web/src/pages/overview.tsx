import { content } from '../data';
import { settings } from '../config/settings';
import { artworkSource } from '../config/artwork';
import { useWorkspace } from '../workspace';
import { Badge, Button, Icon } from '../components/ui';
import { duration, formatDate, outcomeTone } from '../utils/format';
import type { CallRecord } from '../types';

export function CallsTable({ calls, compact = false }: { calls: CallRecord[]; compact?: boolean }) {
  return (
    <div className="table-scroll">
      <table className={`records-table ${compact ? 'compact-table' : ''}`}>
        <thead>
          <tr>
            <th>{content.labels.contact}</th>
            <th>{content.labels.outcome}</th>
            {!compact && <th>{content.labels.service}</th>}
            <th>{content.labels.duration}</th>
            <th>{content.labels.today}</th>
            <th>
              <span className="sr-only">{content.labels.details}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {calls.map((call) => (
            <tr key={call.id}>
              <td>
                <a className="person-link" href={`#/calls/${call.id}`}>
                  <span className="avatar">{call.initials}</span>
                  <span>
                    <strong>{call.name}</strong>
                    <small>{call.phone}</small>
                  </span>
                </a>
              </td>
              <td>
                <Badge tone={outcomeTone(call.outcome)}>{call.outcome}</Badge>
              </td>
              {!compact && <td>{call.service}</td>}
              <td className="tabular">{duration(call.duration)}</td>
              <td className="muted tabular">{formatDate(call.date, true)}</td>
              <td>
                <a
                  className="icon-button"
                  href={`#/calls/${call.id}`}
                  aria-label={`${content.labels.openCall}: ${call.name}`}
                >
                  <Icon name="chevron" size={17} />
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
export function Overview() {
  const { state, open } = useWorkspace();
  const booked = state.calls.filter((x) => x.outcome === 'Booked').length;
  const minutes = Math.round(state.calls.reduce((sum, x) => sum + x.duration, 0) / 60);
  const active = state.appointments
    .filter((x) => x.status === 'Confirmed')
    .sort((a, b) => a.date.localeCompare(b.date));
  const failed = state.jobs.filter((x) => x.status === 'Failed');
  const metrics = [
    { label: content.labels.totalCalls, value: state.calls.length, icon: 'phone' },
    { label: content.labels.bookings, value: active.length, icon: 'calendar' },
    {
      label: content.labels.rate,
      value: `${Math.round((booked / Math.max(state.calls.length, 1)) * 100)}%`,
      icon: 'chart',
    },
    { label: content.labels.minutes, value: minutes, icon: 'clock' },
  ];
  const hours = content.chartHours;
  const values = hours.map(
    (hour) =>
      state.calls.filter(
        (call) =>
          Number(
            new Intl.DateTimeFormat(settings.locale, {
              hour: 'numeric',
              hourCycle: 'h23',
              numberingSystem: 'latn',
              timeZone: settings.timezone,
            }).format(new Date(call.date)),
          ) === hour,
      ).length,
  );
  const max = Math.max(...values, 1);
  return (
    <>
      <section className="overview-banner">
        <div>
          <span className="eyebrow">{content.business}</span>
          <h2>{content.labels.guideTitle}</h2>
          <p>{content.labels.guideDetail}</p>
          <Button variant="secondary" icon="play" onClick={() => open({ type: 'simulation' })}>
            {content.labels.simulate}
          </Button>
        </div>
        <img src={artworkSource(content.assets.hero)} alt="" width="1536" height="1024" />
        <span className="banner-corner">
          <Icon name="wave" size={20} />
        </span>
      </section>
      <section className="metrics" aria-label={content.labels.sample}>
        {metrics.map((metric) => (
          <article className="metric" key={metric.label}>
            <div>
              <span>{metric.label}</span>
              <Icon name={metric.icon} size={18} />
            </div>
            <strong>{metric.value}</strong>
            <small>{content.labels.sample}</small>
          </article>
        ))}
      </section>
      <div className="overview-middle">
        <section className="panel rhythm-panel">
          <div className="panel-header">
            <div>
              <h2>{content.labels.callVolume}</h2>
              <p>{content.labels.callVolumeSub}</p>
            </div>
            <Badge>{content.labels.sample}</Badge>
          </div>
          <div
            className="chart"
            role="img"
            aria-label={`${content.labels.callVolume}: ${hours.map((h, i) => `${h}:00 ${values[i]}`).join(', ')}`}
          >
            <div className="chart-grid" aria-hidden="true">
              <span />
              <span />
              <span />
            </div>
            {hours.map((hour, i) => (
              <div className="chart-column" key={hour}>
                <span className="chart-value">{values[i]}</span>
                <div
                  className={`chart-bar ${values[i] === max ? 'peak' : ''}`}
                  style={{ height: `${12 + ((values[i] ?? 0) / max) * 100}px` }}
                />
                <span className="chart-label">{String(hour).padStart(2, '0')}:00</span>
              </div>
            ))}
          </div>
        </section>
        <section className="panel next-panel">
          <div className="panel-header">
            <div>
              <h2>{content.labels.upNext}</h2>
              <p>
                {content.labels.sample} · {content.labels.bookings}
              </p>
            </div>
            <a href="#/appointments" className="text-link">
              {content.labels.viewAll}
              <Icon name="arrow" size={16} />
            </a>
          </div>
          <div className="next-list">
            {active.slice(0, 3).map((apt) => (
              <button
                className="next-item"
                key={apt.id}
                onClick={() => open({ type: 'appointment', id: apt.id })}
              >
                <span className="date-stamp">
                  <strong>{apt.date.slice(8, 10)}</strong>
                  <small>{formatDate(apt.date).split(' ')[0]}</small>
                </span>
                <span>
                  <strong>{apt.name}</strong>
                  <small>{apt.service}</small>
                  <span className="next-time">{formatDate(apt.date, true)}</span>
                </span>
                <Icon name="chevron" size={16} />
              </button>
            ))}
          </div>
        </section>
      </div>
      {failed.length > 0 && (
        <a className="attention-bar" href="#/automations">
          <span className="attention-icon">
            <Icon name="alert" size={18} />
          </span>
          <span>
            <strong>{content.labels.attention}</strong>
            <small>{content.labels.attentionDetail}</small>
          </span>
          <span className="text-link">
            {content.labels.review}
            <Icon name="arrow" size={17} />
          </span>
        </a>
      )}
      <section className="panel recent-panel">
        <div className="panel-header">
          <div>
            <h2>{content.labels.recentCalls}</h2>
            <p>{content.labels.demoNotice}</p>
          </div>
          <a href="#/calls" className="text-link">
            {content.labels.viewAll}
            <Icon name="arrow" size={16} />
          </a>
        </div>
        <CallsTable calls={state.calls.slice(0, 5)} compact />
      </section>
    </>
  );
}
