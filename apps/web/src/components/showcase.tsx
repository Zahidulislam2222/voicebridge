import { useReducedMotion } from '../utils/motion-preference';
import './public-site.css';
import { useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import {
  AnimatePresence,
  motion,
  useMotionValueEvent,
  useScroll,
  useSpring,
  useTransform,
} from 'motion/react';
import { content, initialState } from '../data';
import { settings } from '../config/settings';
import { site } from '../data/site';
import type { PublicPage } from '../protocol';
import { artworkSource } from '../config/artwork';
import { Brand, Icon } from './ui';
import { VoiceSculpture } from './voice-sculpture';
import { normalizeIntake } from '../services/intake';

function Lines({ text }: { text: string }) {
  return (
    <>
      {text.split('\n').map((line, i) => (
        <span key={line}>
          {i > 0 && <br />}
          {line}
        </span>
      ))}
    </>
  );
}
function Reveal({
  children,
  className = '',
  delay = 0,
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
}) {
  const reduced = useReducedMotion();
  return (
    <motion.div
      className={`site-reveal ${className}`}
      initial={reduced ? false : { opacity: 0, y: site.motion.revealDistance }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: site.motion.viewportAmount }}
      transition={{ duration: site.motion.revealSeconds, delay: reduced ? 0 : delay }}
    >
      {children}
    </motion.div>
  );
}
function Action({
  href = '#/get-started',
  children,
  secondary = false,
}: {
  href?: string;
  children?: ReactNode;
  secondary?: boolean;
}) {
  return (
    <a href={href} className={`site-button ${secondary ? 'site-button-outline' : ''}`}>
      {children ?? site.labels.getStarted}
      <Icon name="arrow" size={18} />
    </a>
  );
}
function SectionHeading({
  eyebrow,
  title,
  text,
  center = false,
}: {
  eyebrow: string;
  title: string;
  text?: string;
  center?: boolean;
}) {
  return (
    <Reveal className={`site-heading ${center ? 'site-heading-center' : ''}`}>
      <p className="site-eyebrow">{eyebrow}</p>
      <h2>
        <Lines text={title} />
      </h2>
      {text && <p className="site-description">{text}</p>}
    </Reveal>
  );
}
function VoiceCard({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`site-voice-card ${compact ? 'site-voice-compact' : ''}`}>
      <div className="voice-card-top">
        <span className="site-avatar">
          <Icon name="wave" size={21} />
        </span>
        <span>
          <strong>{site.labels.caller}</strong>
          <small>{site.labels.voice}</small>
        </span>
        <span className="voice-status" />
      </div>
      <div className="site-waveform" aria-hidden="true">
        {content.voiceProfiles[0]!.bars.map((height, i) => (
          <i
            key={i}
            style={{ height: `${height}%`, animationDelay: `${i * site.motion.staggerSeconds}s` }}
          />
        ))}
      </div>
      <p>{site.labels.callText}</p>
      <div className="voice-card-bottom">
        <span>{site.labels.conversation}</span>
        <Icon name="phone" size={16} />
      </div>
    </div>
  );
}
function BookingCard() {
  return (
    <div className="site-booking-card">
      <span className="site-booking-icon">
        <Icon name="check" size={20} />
      </span>
      <span>
        <strong>{site.labels.booking}</strong>
        <small>{site.labels.callTime}</small>
      </span>
      <Icon name="calendar" size={18} />
    </div>
  );
}
function Hero() {
  const target = useRef<HTMLElement>(null);
  const reduced = useReducedMotion();
  const { scrollYProgress } = useScroll({ target, offset: ['start start', 'end start'] });
  const y = useTransform(scrollYProgress, [0, 1], [0, site.motion.heroParallax]);
  const [paused, setPaused] = useState(false);
  return (
    <section className={`site-hero ${paused ? 'motion-paused' : ''}`} ref={target}>
      <div className="hero-grain" aria-hidden="true" />
      <div className="site-container site-hero-grid">
        <div className="site-hero-copy">
          <Reveal>
            <p className="site-eyebrow">
              <span className="eyebrow-dot" />
              {site.hero.eyebrow}
            </p>
          </Reveal>
          <motion.h1
            initial={reduced ? false : { opacity: 0, y: site.motion.revealDistance }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: site.motion.revealSeconds }}
          >
            {site.hero.lines.map((line, i) => (
              <span key={line} className={i ? 'hero-accent' : ''}>
                {line}
              </span>
            ))}
          </motion.h1>
          <Reveal delay={site.motion.staggerSeconds}>
            <p className="site-hero-description">{site.hero.description}</p>
            <div className="site-actions">
              <Action />
              <button
                className="site-text-button"
                onClick={() =>
                  document
                    .getElementById('how-it-works')
                    ?.scrollIntoView({ behavior: reduced ? 'instant' : 'smooth' })
                }
              >
                <span className="site-play">
                  <Icon name="play" size={15} />
                </span>
                {site.labels.how}
              </button>
            </div>
            <ul className="hero-assurances">
              {site.hero.points.map((point) => (
                <li key={point}>
                  <Icon name="check" size={15} />
                  {point}
                </li>
              ))}
            </ul>
          </Reveal>
        </div>
        <motion.div className="site-hero-visual" style={{ y: reduced ? 0 : y }}>
          <div className="hero-orbit orbit-one" />
          <div className="hero-orbit orbit-two" />
          <VoiceSculpture paused={paused} />
          <motion.div
            className="hero-floating-voice"
            animate={reduced || paused ? {} : { y: [0, -site.motion.floatDistance, 0] }}
            transition={{ duration: site.motion.floatSeconds, repeat: Infinity, ease: 'easeInOut' }}
          >
            <VoiceCard />
          </motion.div>
          <motion.div
            className="hero-floating-booking"
            animate={reduced || paused ? {} : { y: [0, site.motion.floatDistance, 0] }}
            transition={{ duration: site.motion.floatSeconds, repeat: Infinity, ease: 'easeInOut' }}
          >
            <BookingCard />
          </motion.div>
          <span className="hero-visual-label">{site.labels.activity}</span>
          <button
            className="motion-control"
            aria-label={paused ? site.labels.play : site.labels.pause}
            aria-pressed={paused}
            onClick={() => setPaused((value) => !value)}
          >
            <Icon name={paused ? 'play' : 'pause'} size={16} />
          </button>
        </motion.div>
      </div>
      <div className="site-container hero-bottom">
        <span>{site.hero.scroll}</span>
        <button
          aria-label={site.labels.how}
          onClick={() =>
            document
              .getElementById('product-overview')
              ?.scrollIntoView({ behavior: reduced ? 'instant' : 'smooth' })
          }
        >
          <Icon name="arrow" size={20} />
        </button>
        <span className="hero-bottom-index">01 / {content.brand}</span>
      </div>
    </section>
  );
}
function BusinessStrip() {
  return (
    <div className="business-strip site-container">
      <p>{site.labels.businessStrip}</p>
      <div>
        {site.industries.map((item) => (
          <span key={item.id}>
            <Icon name={item.icon} size={20} />
            {item.label}
          </span>
        ))}
      </div>
    </div>
  );
}
function ProductWindow() {
  const records = initialState();
  const appointments = records.appointments.filter((item) => item.status === 'Confirmed');
  const primaryContact = records.contacts[0]!;
  const { scrollYProgress } = useScroll();
  const scale = useTransform(
    scrollYProgress,
    [0, 0.3],
    [site.motion.visualScaleStart, site.motion.visualScaleEnd],
  );
  const reduced = useReducedMotion();
  return (
    <section className="site-section product-overview" id="product-overview">
      <div className="site-container">
        <SectionHeading
          eyebrow={site.labels.introProductEyebrow}
          title={site.labels.introProductTitle}
          text={site.labels.introProductText}
          center
        />
        <motion.a
          href="#/overview"
          className="product-window"
          style={{ scale: reduced ? 1 : scale }}
          aria-label={site.labels.workspace}
        >
          <div className="window-chrome">
            <span>
              <i />
              <i />
              <i />
            </span>
            <p>
              {content.brand} / {content.workspace}
            </p>
            <Icon name="arrow" size={16} />
          </div>
          <div className="product-window-body">
            <aside>
              <div className="window-brand">
                <Icon name="wave" size={23} />
                <strong>{content.brand}</strong>
              </div>
              {content.nav.slice(0, 7).map((item, i) => (
                <span key={item.id} className={i === 0 ? 'selected' : ''}>
                  <Icon name={item.icon} size={16} />
                  {item.label}
                </span>
              ))}
            </aside>
            <div className="window-workspace">
              <div className="window-heading">
                <span>
                  <small>{content.business}</small>
                  <h3>{site.labels.introProductTitle.split('\n')[0]}</h3>
                </span>
                <span className="window-pill">{site.labels.selected}</span>
              </div>
              <div className="window-metrics">
                {[
                  [content.labels.totalCalls, String(records.calls.length)],
                  [content.labels.bookings, String(appointments.length)],
                  [
                    content.labels.rate,
                    `${Math.round((records.calls.filter((item) => item.outcome === 'Booked').length / records.calls.length) * 100)}%`,
                  ],
                ].map(([label, value]) => (
                  <div key={label}>
                    <span>{label}</span>
                    <strong>{value}</strong>
                    <span className="window-trend">
                      <Icon name="arrow" size={12} />
                      {content.labels.today}
                    </span>
                  </div>
                ))}
              </div>
              <div className="window-charts">
                <div className="window-chart">
                  <h4>{content.labels.callVolume}</h4>
                  <div>
                    {content.chartHours.map((hour, i) => (
                      <span key={hour}>
                        <i
                          style={{
                            height: `${content.voiceProfiles[0]!.bars[i % content.voiceProfiles[0]!.bars.length]}%`,
                          }}
                        />
                        <small>{hour}:00</small>
                      </span>
                    ))}
                  </div>
                </div>
                <div className="window-appointments">
                  <h4>{content.labels.upNext}</h4>
                  <BookingCard />
                  <div className="window-person">
                    <span>
                      {primaryContact.name
                        .split(' ')
                        .map((word) => word.charAt(0))
                        .join('')}
                    </span>
                    <div>
                      <strong>{primaryContact.name}</strong>
                      <small>{content.services[0]}</small>
                    </div>
                    <Icon name="chevron" size={16} />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.a>
        <Reveal className="product-window-link">
          <Action href="#/features" secondary>
            {site.labels.explore}
          </Action>
        </Reveal>
      </div>
    </section>
  );
}
function Workflow() {
  const target = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({ target, offset: ['start start', 'end end'] });
  const reduced = useReducedMotion();
  const [stage, setStage] = useState(0);
  const translate = useTransform(
    scrollYProgress,
    [0, 1],
    [site.motion.storyParallax, -site.motion.storyParallax],
  );
  useMotionValueEvent(scrollYProgress, 'change', (value) =>
    setStage(Math.min(site.workflow.length - 1, Math.floor(value * site.workflow.length))),
  );
  return (
    <section className="site-workflow" id="how-it-works" ref={target}>
      <div className="site-container workflow-heading">
        <SectionHeading
          eyebrow={site.labels.storyEyebrow}
          title={site.labels.storyTitle}
          text={site.labels.storyText}
        />
      </div>
      <div className="site-container workflow-grid">
        <div className="workflow-sticky">
          <div className="workflow-visual">
            <img src={artworkSource(content.assets.hero)} alt="" loading="lazy" />
            <span className="workflow-visual-caption">{site.workflow[stage]!.label}</span>
            <motion.div className="workflow-card" style={{ y: reduced ? 0 : translate }}>
              <AnimatePresence mode="wait" initial={false}>
                <motion.div
                  key={stage}
                  initial={reduced ? false : { opacity: 0, y: site.motion.revealDistance / 2 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={reduced ? {} : { opacity: 0, y: -site.motion.revealDistance / 2 }}
                  transition={{ duration: site.motion.revealSeconds / 2 }}
                >
                  <span className="workflow-icon">
                    <Icon name={site.workflow[stage]!.icon} size={26} />
                  </span>
                  <h3>{site.workflow[stage]!.detail}</h3>
                  <p>{site.workflow[stage]!.detailText}</p>
                  <div className="workflow-dots">
                    {site.workflow.map((item, i) => (
                      <i key={item.label} className={i === stage ? 'active' : ''} />
                    ))}
                  </div>
                </motion.div>
              </AnimatePresence>
            </motion.div>
          </div>
        </div>
        <div className="workflow-steps">
          {site.workflow.map((item, i) => (
            <Reveal className={`workflow-step ${stage === i ? 'active' : ''}`} key={item.label}>
              <span className="workflow-step-line" />
              <p className="site-eyebrow">{item.label}</p>
              <h3>{item.title}</h3>
              <p>{item.description}</p>
              <a href="#/features">
                {site.labels.learn}
                <Icon name="arrow" size={18} />
              </a>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
function FeatureGrid({ full = false }: { full?: boolean }) {
  const [selected, setSelected] = useState(site.features[0]!.id);
  return (
    <section className="site-section site-capabilities">
      <div className="site-container">
        <SectionHeading eyebrow={site.labels.sectionFeatures} title={site.labels.featureHeading} />
        <div className="capability-grid">
          {site.features.map((feature, i) => (
            <Reveal delay={(i % 3) * site.motion.staggerSeconds} key={feature.id}>
              <button
                className={`capability-card ${selected === feature.id ? 'active' : ''}`}
                aria-pressed={selected === feature.id}
                onClick={() => setSelected(feature.id)}
              >
                <span className="capability-icon">
                  <Icon name={feature.icon} size={25} />
                </span>
                <span className="capability-number">0{i + 1}</span>
                <h3>{feature.title}</h3>
                <p>{feature.text}</p>
                <span className="capability-arrow">
                  <Icon name="arrow" size={20} />
                </span>
              </button>
            </Reveal>
          ))}
        </div>
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            className="capability-detail"
            key={selected}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <Icon name={site.features.find((item) => item.id === selected)!.icon} size={24} />
            <p>{site.features.find((item) => item.id === selected)!.detail}</p>
            <a href={full ? '#/get-started' : '#/features'}>
              {full ? site.labels.getStarted : site.labels.all}
              <Icon name="arrow" size={17} />
            </a>
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  );
}
function Industries() {
  const [selected, setSelected] = useState(site.industries[0]!.id);
  const industry = site.industries.find((item) => item.id === selected)!;
  return (
    <section className="site-section site-industries">
      <div className="site-container">
        <SectionHeading eyebrow={site.labels.industryEyebrow} title={site.labels.industryHeading} />
        <div className="industry-tabs" role="tablist" aria-label={site.labels.industry}>
          {site.industries.map((item, i) => (
            <button
              id={`industry-tab-${item.id}`}
              key={item.id}
              role="tab"
              aria-selected={selected === item.id}
              aria-controls="industry-panel"
              tabIndex={selected === item.id ? 0 : -1}
              onClick={() => setSelected(item.id)}
              onKeyDown={(event) => {
                if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
                event.preventDefault();
                const next =
                  event.key === 'Home'
                    ? 0
                    : event.key === 'End'
                      ? site.industries.length - 1
                      : (i + (event.key === 'ArrowRight' ? 1 : -1) + site.industries.length) %
                        site.industries.length;
                setSelected(site.industries[next]!.id);
                document.getElementById(`industry-tab-${site.industries[next]!.id}`)?.focus();
              }}
            >
              <Icon name={item.icon} size={17} />
              {item.label}
            </button>
          ))}
        </div>
        <div
          className="industry-panel"
          id="industry-panel"
          role="tabpanel"
          aria-labelledby={`industry-tab-${selected}`}
        >
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              className="industry-copy"
              key={selected}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <h3>
                <Lines text={industry.headline} />
              </h3>
              <p>{industry.text}</p>
              <ul>
                {industry.items.map((item) => (
                  <li key={item}>
                    <Icon name="check" size={17} />
                    {item}
                  </li>
                ))}
              </ul>
              <Action href="#/contact" secondary>
                {site.labels.contact}
              </Action>
            </motion.div>
          </AnimatePresence>
          <div className={`industry-conversation industry-${selected}`}>
            <p className="site-eyebrow">{industry.tag}</p>
            <div className="industry-orb">
              <Icon name={industry.icon} size={34} />
            </div>
            <blockquote>{industry.quote}</blockquote>
            <div className="industry-reply">
              <Icon name="wave" size={20} />
              <p>{industry.reply}</p>
            </div>
            <span className="industry-caption">{site.labels.conversation}</span>
          </div>
        </div>
      </div>
    </section>
  );
}
function IntegrationsSection() {
  return (
    <section className="site-section site-integrations">
      <div className="site-container integration-layout">
        <SectionHeading
          eyebrow={site.labels.integrationsEyebrow}
          title={site.labels.integrationsHeading}
          text={site.labels.integrationsText}
        />
        <Reveal className="integration-constellation">
          <div className="integration-ring" />
          <div className="integration-hub">
            <Icon name="wave" size={40} />
          </div>
          {site.integrations.map((name, i) => (
            <div className={`integration-node integration-node-${i}`} key={name}>
              <span>{name.charAt(0)}</span>
              <strong>{name}</strong>
            </div>
          ))}
        </Reveal>
      </div>
      <div className="site-container">
        <Action href="#/integrations" secondary>
          {site.labels.integrationAction}
        </Action>
      </div>
    </section>
  );
}
function FAQ() {
  return (
    <section className="site-section site-faq">
      <div className="site-container faq-layout">
        <SectionHeading eyebrow={site.labels.faq} title={site.labels.faqHeading} />
        <div>
          {site.faq.map((item) => (
            <details key={item.question}>
              <summary>
                {item.question}
                <span>
                  <Icon name="plus" size={18} />
                </span>
              </summary>
              <p>{item.answer}</p>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}
function FinalAction() {
  return (
    <section className="site-final">
      <div className="site-container final-layout">
        <Reveal>
          <p className="site-eyebrow">{site.labels.ctaEyebrow}</p>
          <h2>
            <Lines text={site.labels.ctaHeading} />
          </h2>
          <p>{site.labels.ctaText}</p>
          <div className="site-actions">
            <Action />
            <Action href="#/contact" secondary>
              {site.labels.contact}
            </Action>
          </div>
        </Reveal>
        <div className="final-hello" aria-hidden="true">
          Hello<span>.</span>
          <i />
          <i />
        </div>
      </div>
    </section>
  );
}
function PageHero({
  page,
}: {
  page: 'features' | 'solutions' | 'pricing' | 'company' | 'resources';
}) {
  const copy = site.pages[page];
  return (
    <section className={`site-page-hero site-page-${page}`}>
      <div className="site-container">
        <Reveal>
          <p className="site-eyebrow">{copy.eyebrow}</p>
          <h1>
            <Lines text={copy.title} />
          </h1>
          <p>{copy.text}</p>
        </Reveal>
        <div className="page-hero-symbol" aria-hidden="true">
          <Icon
            name={
              page === 'features'
                ? 'wave'
                : page === 'solutions'
                  ? 'users'
                  : page === 'pricing'
                    ? 'grid'
                    : page === 'company'
                      ? 'spark'
                      : 'book'
            }
            size={100}
          />
        </div>
      </div>
    </section>
  );
}
function Pricing() {
  return (
    <>
      <PageHero page="pricing" />
      <section className="site-section pricing-section">
        <div className="site-container">
          <div className="pricing-grid">
            {site.plans.map((plan, i) => (
              <Reveal key={plan.name} delay={i * site.motion.staggerSeconds}>
                <article className={`pricing-card ${plan.featured ? 'featured' : ''}`}>
                  <p className="site-eyebrow">{plan.eyebrow}</p>
                  <h2>{plan.name}</h2>
                  <p>{plan.description}</p>
                  <div className="plan-price">
                    <strong>{plan.price}</strong>
                    <small>{plan.priceNote}</small>
                  </div>
                  <Action href="#/contact" secondary={!plan.featured}>
                    {site.labels.planAction}
                  </Action>
                  <ul>
                    {plan.features.map((item) => (
                      <li key={item}>
                        <Icon name="check" size={17} />
                        {item}
                      </li>
                    ))}
                  </ul>
                </article>
              </Reveal>
            ))}
          </div>
          <div className="pricing-comparison">
            <table>
              <thead>
                <tr>
                  <th>{site.labels.all}</th>
                  {site.plans.map((plan) => (
                    <th key={plan.name}>{plan.name}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {site.comparison.map((row) => (
                  <tr key={row.label}>
                    <th scope="row">{row.label}</th>
                    {row.values.map((value, i) => (
                      <td key={i}>{value}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>
      <FAQ />
      <FinalAction />
    </>
  );
}
function Company() {
  return (
    <>
      <PageHero page="company" />
      <section className="site-section company-story">
        <div className="site-container company-grid">
          <Reveal className="company-art">
            <img src={artworkSource(content.assets.hero)} alt="" loading="lazy" />
            <span>{content.brand}</span>
          </Reveal>
          <div>
            <SectionHeading eyebrow={site.companyStory.eyebrow} title={site.companyStory.title} />
            {site.companyStory.paragraphs.map((paragraph) => (
              <Reveal className="company-paragraph" key={paragraph}>
                <p>{paragraph}</p>
              </Reveal>
            ))}
          </div>
        </div>
      </section>
      <section className="site-section site-values">
        <div className="site-container">
          {site.values.map((item) => (
            <Reveal key={item.number}>
              <article>
                <span>{item.number}</span>
                <h2>{item.title}</h2>
                <p>{item.text}</p>
              </article>
            </Reveal>
          ))}
        </div>
      </section>
      <FinalAction />
    </>
  );
}
function Resources({ articleId }: { articleId?: string }) {
  const article = site.resources.find((item) => item.id === articleId);
  return article ? (
    <section className="site-article site-container">
      <a className="article-back" href="#/resources">
        <Icon name="arrow" size={18} />
        {site.labels.back}
      </a>
      <Reveal>
        <p className="site-eyebrow">
          {article.category} · {article.minutes}
        </p>
        <h1>{article.title}</h1>
        <p className="article-intro">{article.summary}</p>
      </Reveal>
      <div className="article-body">
        {article.paragraphs.map((text, i) => (
          <Reveal key={text}>
            <p>
              <span>0{i + 1}</span>
              {text}
            </p>
          </Reveal>
        ))}
      </div>
      <Action href="#/features" secondary>
        {site.labels.explore}
      </Action>
    </section>
  ) : (
    <>
      <PageHero page="resources" />
      <section className="site-section site-resources">
        <div className="site-container resource-grid">
          {site.resources.map((item, i) => (
            <Reveal key={item.id} delay={i * site.motion.staggerSeconds}>
              <a href={`#/resources/${item.id}`} className="resource-card">
                <div className={`resource-art resource-art-${i}`}>
                  <Icon name={i === 0 ? 'wave' : i === 1 ? 'flow' : 'book'} size={66} />
                  <span>0{i + 1}</span>
                </div>
                <div className="resource-copy">
                  <p className="site-eyebrow">
                    {item.category} · {item.minutes}
                  </p>
                  <h2>{item.title}</h2>
                  <p>{item.summary}</p>
                  <span>
                    {site.labels.read}
                    <Icon name="arrow" size={18} />
                  </span>
                </div>
              </a>
            </Reveal>
          ))}
        </div>
      </section>
      <FAQ />
      <FinalAction />
    </>
  );
}
function Intake({ onboarding = false }: { onboarding?: boolean }) {
  const [step, setStep] = useState(0);
  const [review, setReview] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    name: '',
    email: '',
    company: '',
    industry: site.industries[0]!.id,
    voice: content.voiceProfiles[0]!.id,
    message: '',
    team: site.teamChoices[0]!,
  });
  const field = (key: keyof typeof form, label: string, type = 'text') => (
    <label className="site-field">
      <span>{label}</span>
      <input
        name={key}
        type={type}
        required
        value={form[key]}
        maxLength={settings.maxTextLength}
        onChange={(event) => setForm({ ...form, [key]: event.target.value })}
      />
    </label>
  );
  return (
    <section className="site-intake">
      <div className="site-container intake-grid">
        <div className="intake-heading">
          <p className="site-eyebrow">
            {onboarding ? site.labels.onboardingEyebrow : site.labels.contactEyebrow}
          </p>
          <h1>
            <Lines text={onboarding ? site.labels.onboardingHeading : site.labels.contactHeading} />
          </h1>
          <p>{onboarding ? site.labels.onboardingText : site.labels.contactText}</p>
          <div className="intake-decoration">
            <Icon name="wave" size={65} />
            <span>{content.brand}</span>
          </div>
        </div>
        <div className="intake-card">
          {onboarding && (
            <ol className="intake-steps">
              {[site.labels.detailsStep, site.labels.preferencesStep, site.labels.readyStep].map(
                (label, i) => (
                  <li key={label} className={i === step ? 'active' : ''}>
                    <span>{i + 1}</span>
                    {label}
                  </li>
                ),
              )}
            </ol>
          )}
          {review ? (
            <div className="intake-review">
              <span className="review-icon">
                <Icon name="check" size={32} />
              </span>
              <p className="site-eyebrow">{site.labels.request}</p>
              <h2>{site.labels.reviewHeading}</h2>
              <p>{site.labels.reviewText}</p>
              <dl>
                {[
                  [site.labels.name, form.name],
                  [site.labels.company, form.company],
                  [site.labels.email, form.email],
                  [
                    site.labels.industry,
                    site.industries.find((item) => item.id === form.industry)!.label,
                  ],
                  ...(onboarding
                    ? [
                        [
                          site.labels.voiceLabel,
                          content.voiceProfiles.find((item) => item.id === form.voice)!.name,
                        ],
                      ]
                    : [
                        [site.labels.team, form.team],
                        [site.labels.message, form.message],
                      ]),
                ].map(([label, value]) => (
                  <div key={label}>
                    <dt>{label}</dt>
                    <dd>{value}</dd>
                  </div>
                ))}
              </dl>
              <div className="site-actions">
                <Action href="#/overview">{site.labels.reviewAction}</Action>
                <button
                  className="site-text-button"
                  onClick={() => {
                    setReview(false);
                    setStep(0);
                  }}
                >
                  {site.labels.edit}
                </button>
              </div>
            </div>
          ) : (
            <form
              onSubmit={(event) => {
                event.preventDefault();
                try {
                  setForm(
                    normalizeIntake(form, {
                      onboarding,
                      maxTextLength: settings.maxTextLength,
                      industryIds: site.industries.map((item) => item.id),
                      voiceIds: content.voiceProfiles.map((item) => item.id),
                      teamChoices: site.teamChoices,
                    }),
                  );
                  setError('');
                } catch {
                  setError(site.labels.invalidForm);
                  return;
                }
                if (onboarding && step === 0) {
                  setStep(1);
                  return;
                }
                setReview(true);
                setStep(2);
              }}
            >
              {error && (
                <p className="form-error" role="alert">
                  {error}
                </p>
              )}
              {(!onboarding || step === 0) && (
                <>
                  {field('name', site.labels.name)}
                  {field('email', site.labels.email, 'email')}
                  {field('company', site.labels.company)}
                </>
              )}
              {(!onboarding || step === 1) && (
                <>
                  <label className="site-field">
                    <span>{site.labels.industry}</span>
                    <select
                      value={form.industry}
                      onChange={(event) => setForm({ ...form, industry: event.target.value })}
                    >
                      {site.industries.map((item) => (
                        <option value={item.id} key={item.id}>
                          {item.label}
                        </option>
                      ))}
                    </select>
                  </label>
                  {onboarding ? (
                    <label className="site-field">
                      <span>{site.labels.voiceLabel}</span>
                      <select
                        value={form.voice}
                        onChange={(event) => setForm({ ...form, voice: event.target.value })}
                      >
                        {content.voiceProfiles.map((item) => (
                          <option value={item.id} key={item.id}>
                            {item.name} · {item.style}
                          </option>
                        ))}
                      </select>
                    </label>
                  ) : (
                    <>
                      <label className="site-field">
                        <span>{site.labels.team}</span>
                        <select
                          value={form.team}
                          onChange={(event) => setForm({ ...form, team: event.target.value })}
                        >
                          {site.teamChoices.map((item) => (
                            <option key={item}>{item}</option>
                          ))}
                        </select>
                      </label>
                      <label className="site-field">
                        <span>{site.labels.message}</span>
                        <textarea
                          required
                          rows={4}
                          maxLength={settings.maxTextLength}
                          value={form.message}
                          onChange={(event) => setForm({ ...form, message: event.target.value })}
                        />
                      </label>
                    </>
                  )}
                </>
              )}
              <div className="intake-submit">
                <button className="site-button" type="submit">
                  {onboarding && step === 0 ? site.labels.next : site.labels.review}
                  <Icon name="arrow" size={18} />
                </button>
                {onboarding && step === 1 && (
                  <button type="button" className="site-text-button" onClick={() => setStep(0)}>
                    {site.labels.edit}
                  </button>
                )}
              </div>
              <p className="intake-privacy">
                <Icon name="shield" size={14} />
                {site.labels.privacy}
              </p>
            </form>
          )}
        </div>
      </div>
    </section>
  );
}
function SiteHeader({ page }: { page: PublicPage }) {
  const [menu, setMenu] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const trigger = useRef<HTMLButtonElement>(null);
  const navigation = useRef<HTMLElement>(null);
  const { scrollY } = useScroll();
  useMotionValueEvent(scrollY, 'change', (value) => setScrolled(value > 0));
  useEffect(() => {
    if (!menu) return;
    const nav = navigation.current;
    const menuTrigger = trigger.current;
    const links = Array.from(nav?.querySelectorAll<HTMLAnchorElement>('a[href]') ?? []);
    links[0]?.focus();
    const key = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setMenu(false);
      }
      if (event.key === 'Tab') {
        const first = links[0],
          last = links.at(-1);
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }
    };
    const resize = () => {
      if (menuTrigger && getComputedStyle(menuTrigger).display === 'none') setMenu(false);
    };
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const background = Array.from(
      nav?.closest('.public-site')?.querySelectorAll<HTMLElement>('main, footer') ?? [],
    );
    const previousInert = background.map((element) => element.inert);
    background.forEach((element) => {
      element.inert = true;
    });
    document.addEventListener('keydown', key);
    window.addEventListener('resize', resize);
    return () => {
      document.removeEventListener('keydown', key);
      window.removeEventListener('resize', resize);
      document.body.style.overflow = previousOverflow;
      background.forEach((element, index) => {
        element.inert = previousInert[index] ?? false;
      });
      if (menuTrigger?.isConnected) {
        if (getComputedStyle(menuTrigger).display !== 'none') menuTrigger.focus();
        else background.find((element) => element.tagName === 'MAIN')?.focus();
      }
    };
  }, [menu]);
  return (
    <header className={`site-header ${scrolled ? 'site-header-scrolled' : ''}`}>
      <div className="site-container header-inner">
        <Brand />
        <nav className="site-desktop-nav" aria-label={site.labels.pageNav}>
          {site.nav.map((item) => (
            <a
              key={item.id}
              href={`#/${item.id}`}
              aria-current={page === item.id ? 'page' : undefined}
            >
              {item.label}
            </a>
          ))}
        </nav>
        <div className="site-header-actions">
          <a className="header-workspace" href="#/overview">
            {site.labels.workspace}
            <Icon name="arrow" size={15} />
          </a>
          <Action />
          <button
            className="site-menu-toggle"
            ref={trigger}
            aria-label={menu ? site.labels.close : site.labels.menu}
            aria-expanded={menu}
            aria-controls="public-mobile-navigation"
            onClick={() => setMenu((value) => !value)}
          >
            <Icon name={menu ? 'x' : 'menu'} size={22} />
          </button>
        </div>
      </div>
      <nav
        id="public-mobile-navigation"
        className="site-mobile-nav"
        ref={navigation}
        aria-label={site.labels.pageNav}
        role={menu ? 'dialog' : undefined}
        aria-modal={menu ? true : undefined}
        aria-hidden={!menu}
        inert={!menu}
        hidden={!menu}
      >
        <a href="#/welcome" onClick={() => setMenu(false)}>
          {site.labels.home}
        </a>
        {site.nav.map((item) => (
          <a key={item.id} href={`#/${item.id}`} onClick={() => setMenu(false)}>
            {item.label}
            <Icon name="arrow" size={19} />
          </a>
        ))}
        <a href="#/contact" onClick={() => setMenu(false)}>
          {site.labels.contact}
        </a>
        <a href="#/get-started" onClick={() => setMenu(false)}>
          {site.labels.getStarted}
        </a>
        <a href="#/overview" onClick={() => setMenu(false)}>
          {site.labels.workspace}
        </a>
      </nav>
    </header>
  );
}
function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="site-container footer-grid">
        <div>
          <Brand />
          <p>{site.labels.footerNote}</p>
        </div>
        <nav aria-label={site.labels.pageNav}>
          {site.nav.map((item) => (
            <a key={item.id} href={`#/${item.id}`}>
              {item.label}
            </a>
          ))}
        </nav>
        <div className="footer-action">
          <span>{site.labels.ctaEyebrow}</span>
          <a href="#/contact">
            {site.labels.contact}
            <Icon name="arrow" size={24} />
          </a>
          <a href="#/overview">
            {site.labels.workspace}
            <Icon name="arrow" size={16} />
          </a>
        </div>
      </div>
      <div className="site-container footer-bottom">
        <span>{site.labels.copyright}</span>
        <span>{site.labels.footerNote}</span>
        <a href="#/welcome">
          {site.labels.home}
          <Icon name="arrow" size={14} />
        </a>
      </div>
    </footer>
  );
}
export function Showcase({
  page = 'welcome',
  articleId,
}: {
  page?: PublicPage;
  articleId?: string;
}) {
  const { scrollYProgress } = useScroll();
  const progress = useSpring(scrollYProgress, {
    stiffness: site.motion.springStiffness,
    damping: site.motion.springDamping,
  });
  const reduced = useReducedMotion();
  useEffect(() => {
    document.title = `${content.brand} · ${page === 'welcome' ? site.labels.home : (site.nav.find((item) => item.id === page)?.label ?? (page === 'contact' ? site.labels.contact : site.labels.getStarted))}`;
  }, [page]);
  let body: ReactNode;
  switch (page) {
    case 'features':
      body = (
        <>
          <PageHero page="features" />
          <ProductWindow />
          <FeatureGrid full />
          <Workflow />
          <IntegrationsSection />
          <FAQ />
          <FinalAction />
        </>
      );
      break;
    case 'solutions':
      body = (
        <>
          <PageHero page="solutions" />
          <Industries />
          <Workflow />
          <FAQ />
          <FinalAction />
        </>
      );
      break;
    case 'pricing':
      body = <Pricing />;
      break;
    case 'company':
      body = <Company />;
      break;
    case 'resources':
      body = <Resources articleId={articleId} />;
      break;
    case 'contact':
      body = <Intake />;
      break;
    case 'get-started':
      body = <Intake onboarding />;
      break;
    default:
      body = (
        <>
          <Hero />
          <BusinessStrip />
          <ProductWindow />
          <Workflow />
          <FeatureGrid />
          <Industries />
          <IntegrationsSection />
          <FAQ />
          <FinalAction />
        </>
      );
  }
  return (
    <div className={`public-site public-page-${page}`} data-public-page={page}>
      <motion.div
        className="site-scroll-progress"
        style={{ scaleX: reduced ? scrollYProgress : progress }}
      />
      <SiteHeader page={page} key={page} />
      <main id="main-content" tabIndex={-1} key={`${page}/${articleId ?? ''}`}>
        {body}
      </main>
      <SiteFooter />
    </div>
  );
}
