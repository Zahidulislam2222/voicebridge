import { useReducedMotion } from './utils/motion-preference';
import { useEffect, useRef, useState, useSyncExternalStore } from 'react';
import { AnimatePresence, MotionConfig, motion } from 'motion/react';
import { content, initialState, pageIds } from './data';
import { settings } from './config/settings';
import type { PageId, Role } from './types';
import { WorkspaceContext } from './workspace';
import type { ModalState, Mutation } from './workspace';
import { confirmBooking } from './services/demo-service';
import { Badge, Brand, Button, Icon, Modal, Notice } from './components/ui';
import { Showcase } from './components/showcase';
import { isPublicPage } from './protocol';
import { Conversation } from './components/conversation';
import { RecordDetails } from './components/details';
import { CoreConsole } from './components/core-console';
import { Overview } from './pages/overview';
import { Appointments, Audit, Automations, Calls, Contacts, Knowledge } from './pages/records';
import { Agents, Evaluations, Integrations, Usage, Voices } from './pages/configuration';

function route() {
  const raw = window.location.hash.replace(/^#\//, '') || 'welcome';
  const [path, params] = raw.split('?');
  const [page, id] = path?.split('/') ?? [];
  return {
    page:
      page === 'engine'
        ? 'engine'
        : isPublicPage(page ?? '')
          ? page!
          : pageIds.includes(page as PageId)
            ? (page as PageId)
            : 'overview',
    id,
    simulate: new URLSearchParams(params).get('demo') === '1',
  };
}
function subscribeViewport(callback: () => void) {
  window.addEventListener('resize', callback);
  window.addEventListener('hashchange', callback);
  return () => {
    window.removeEventListener('resize', callback);
    window.removeEventListener('hashchange', callback);
  };
}
function mobileSnapshot() {
  const toggle = document.getElementById('mobile-navigation-toggle');
  return !!toggle && getComputedStyle(toggle).display !== 'none';
}
const pages: Record<PageId, React.ComponentType> = {
  overview: Overview,
  agents: Agents,
  voices: Voices,
  calls: Calls,
  appointments: Appointments,
  contacts: Contacts,
  automations: Automations,
  knowledge: Knowledge,
  evaluations: Evaluations,
  integrations: Integrations,
  usage: Usage,
  audit: Audit,
};
export function App() {
  const [state, setState] = useState(initialState);
  const stateRef = useRef(state);
  const roleRef = useRef<Role>(settings.role);
  const [agentEditor, setAgentEditor] = useState(state.agent);
  const [current, setCurrent] = useState(route);
  const [role, setRole] = useState<Role>(settings.role);
  const [query, setQuery] = useState('');
  const [menu, setMenu] = useState(false);
  const [modal, setModal] = useState<ModalState>(null);
  const [toast, setToast] = useState('');
  const sidebarRef = useRef<HTMLElement>(null);
  const mobile = useSyncExternalStore(subscribeViewport, mobileSnapshot, () => false);
  const reduced = useReducedMotion();
  useEffect(() => {
    if (!mobile || !menu) return;
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const sidebar = sidebarRef.current;
    const controls = Array.from(
      sidebar?.querySelectorAll<HTMLElement>('a[href],button:not(:disabled)') ?? [],
    ).filter((el) => getComputedStyle(el).display !== 'none');
    (sidebar?.querySelector<HTMLElement>('.nav-link.active') ?? controls[0])?.focus();
    function trap(event: KeyboardEvent) {
      if (event.key !== 'Tab') return;
      const first = controls[0],
        last = controls.at(-1);
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first?.focus();
      }
    }
    sidebar?.addEventListener('keydown', trap);
    return () => {
      sidebar?.removeEventListener('keydown', trap);
      previous?.focus();
    };
  }, [mobile, menu]);
  useEffect(() => {
    function change() {
      const next = route();
      setCurrent(next);
      setMenu(false);
      setQuery('');
      setModal(null);
      window.scrollTo({ top: 0, behavior: 'instant' });
    }
    window.addEventListener('hashchange', change);
    return () => window.removeEventListener('hashchange', change);
  }, []);
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(''), settings.notificationMs);
    return () => clearTimeout(timer);
  }, [toast]);
  useEffect(() => {
    function key(e: KeyboardEvent) {
      if (e.key === 'Escape') setMenu(false);
    }
    window.addEventListener('keydown', key);
    return () => window.removeEventListener('keydown', key);
  }, []);
  const mutate: Mutation = (operation, message) => {
    try {
      const previous = stateRef.current;
      const next = operation(previous, roleRef.current);
      stateRef.current = next;
      setState(next);
      if (next.agent.voiceId !== previous.agent.voiceId)
        setAgentEditor((editor) => ({ ...editor, voiceId: next.agent.voiceId }));
      setToast(message);
      return undefined;
    } catch (error) {
      const message = error instanceof Error ? error.message : content.messages.invalid;
      setToast(message);
      return message;
    }
  };
  const pageId = current.page as PageId;
  const page = content.nav.find((x) => x.id === pageId);
  const Page = pages[pageId];
  const routeModal: ModalState =
    current.page === 'calls' && current.id
      ? { type: 'call', id: current.id }
      : current.simulate
        ? { type: 'simulation' }
        : null;
  const activeModal = modal ?? routeModal;
  function close() {
    setModal(null);
    if (routeModal) window.location.hash = `#/${current.page}`;
  }
  function open(value: ModalState) {
    if (routeModal && value) window.history.replaceState(null, '', `#/${current.page}`);
    setModal(value);
    if (routeModal) setCurrent({ ...current, id: undefined, simulate: false });
  }
  const title =
    activeModal?.type === 'simulation'
      ? content.labels.simulate
      : activeModal?.type === 'call'
        ? content.labels.conversation
        : activeModal?.type === 'contact'
          ? content.labels.contact
          : activeModal?.type === 'appointment'
            ? content.labels.booking
            : activeModal?.type === 'job'
              ? content.labels.action
              : content.labels.details;
  return (
    <MotionConfig reducedMotion={reduced ? 'always' : 'never'}>
      <WorkspaceContext.Provider
        value={{ state, role, query, setQuery, mutate, open, agentEditor, setAgentEditor }}
      >
        <a
          className="skip-link"
          href="#main-content"
          onClick={(e) => {
            e.preventDefault();
            document.getElementById('main-content')?.focus();
          }}
        >
          {content.fixedLabels.skip}
        </a>
        {current.page === 'engine' ? (
          <CoreConsole />
        ) : isPublicPage(current.page) ? (
          <Showcase page={current.page} articleId={current.id} />
        ) : (
          <div className="workspace-shell">
            <aside
              ref={sidebarRef}
              className={`sidebar ${menu ? 'sidebar-open' : ''}`}
              aria-label={content.labels.workspace}
              role={mobile ? 'dialog' : undefined}
              aria-modal={mobile && menu ? true : undefined}
              aria-hidden={mobile && !menu ? true : undefined}
              inert={mobile && !menu}
            >
              <div className="sidebar-brand">
                <Brand />
                <button
                  className="mobile-close icon-button"
                  onClick={() => setMenu(false)}
                  aria-label={content.labels.close}
                >
                  <Icon name="x" />
                </button>
              </div>
              <div className="workspace-switch">
                <span className="workspace-avatar">N</span>
                <span>
                  <strong>{content.workspace}</strong>
                  <small>{content.labels.demo}</small>
                </span>
                <Icon name="chevron" size={16} />
              </div>
              <nav aria-label={content.labels.workspace}>
                {['workspace', 'manage'].map((group) => (
                  <div className="nav-group" key={group}>
                    <p>
                      {group === 'workspace' ? content.labels.workspace : content.labels.manage}
                    </p>
                    {content.nav
                      .filter((x) => x.group === group)
                      .map((item) => (
                        <a
                          key={item.id}
                          href={`#/${item.id}`}
                          className={`nav-link ${pageId === item.id ? 'active' : ''}`}
                          aria-current={pageId === item.id ? 'page' : undefined}
                        >
                          <Icon name={item.icon} size={18} />
                          <span>{item.label}</span>
                          {item.id === 'automations' &&
                            state.jobs.some((x) => x.status === 'Failed') && (
                              <span className="nav-count">
                                {state.jobs.filter((x) => x.status === 'Failed').length}
                              </span>
                            )}
                        </a>
                      ))}
                  </div>
                ))}
              </nav>
              <div className="sidebar-foot">
                <span className="user-avatar">DM</span>
                <div>
                  <strong>{content.fixedLabels.operatorName}</strong>
                  <small>
                    {role === 'operator' ? content.labels.operator : content.labels.viewer}
                  </small>
                </div>
                <Icon name="shield" size={18} />
              </div>
            </aside>
            {menu && (
              <button
                className="mobile-scrim"
                onClick={() => setMenu(false)}
                aria-label={content.labels.close}
              />
            )}
            <div className="workspace-main" inert={mobile && menu}>
              <header className="topbar">
                <div className="topbar-left">
                  <button
                    className="mobile-menu icon-button"
                    id="mobile-navigation-toggle"
                    aria-label={content.labels.menu}
                    aria-expanded={menu}
                    onClick={() => setMenu(!menu)}
                  >
                    <Icon name="menu" />
                  </button>
                  <span className="breadcrumb">
                    {content.workspace}
                    <Icon name="chevron" size={13} />
                    <strong>{page?.label}</strong>
                  </span>
                </div>
                <div className="topbar-right">
                  <Badge tone="blue">{content.labels.demo}</Badge>
                  <label className="role-switch">
                    <span className="sr-only">{content.labels.operator}</span>
                    <select
                      value={role}
                      onChange={(e) => {
                        const next = e.target.value as Role;
                        roleRef.current = next;
                        setRole(next);
                      }}
                    >
                      <option value="operator">{content.labels.operator}</option>
                      <option value="viewer">{content.labels.viewer}</option>
                    </select>
                  </label>
                </div>
              </header>
              <main className="page-content" id="main-content" tabIndex={-1}>
                <div className="page-heading">
                  <div>
                    <p className="eyebrow">
                      {content.labels.today} <span>·</span> {content.labels.sample}
                    </p>
                    <h1>
                      {pageId === 'overview' ? content.hero.title.replace('\n', ' ') : page?.label}
                    </h1>
                    <p>{content.pageDescriptions[pageId]}</p>
                  </div>
                  <Button icon="play" onClick={() => open({ type: 'simulation' })}>
                    {content.labels.simulate}
                  </Button>
                </div>
                {role === 'viewer' && <Notice warning>{content.labels.viewerNotice}</Notice>}
                {[
                  'calls',
                  'contacts',
                  'appointments',
                  'knowledge',
                  'automations',
                  'audit',
                ].includes(pageId) && (
                  <div className="search-field">
                    <Icon name="search" size={19} />
                    <input
                      aria-label={`${content.labels.search} ${page?.label}`}
                      placeholder={`${content.labels.search} ${page?.label?.toLowerCase()}…`}
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                    />
                    {query && (
                      <button
                        className="icon-button"
                        onClick={() => setQuery('')}
                        aria-label={content.labels.clearSearch}
                      >
                        <Icon name="x" size={17} />
                      </button>
                    )}
                  </div>
                )}
                <AnimatePresence mode="wait" initial={false}>
                  <motion.div
                    key={pageId}
                    initial={reduced ? false : { opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={reduced ? {} : { opacity: 0 }}
                    transition={{ duration: settings.animationSeconds }}
                  >
                    {Page && <Page />}
                  </motion.div>
                </AnimatePresence>
                <footer className="workspace-footer">
                  <span>
                    <Icon name="shield" size={14} />
                    {content.labels.demoNotice}
                  </span>
                  <a href="#/welcome">
                    {content.labels.showcase}
                    <Icon name="arrow" size={14} />
                  </a>
                </footer>
              </main>
            </div>
          </div>
        )}
        {activeModal && (
          <Modal
            key={`${activeModal.type}${'id' in activeModal ? activeModal.id : ''}`}
            title={title}
            onClose={close}
            wide={activeModal.type === 'simulation'}
          >
            {activeModal.type === 'simulation' ? (
              <Conversation
                role={role}
                onConfirm={(input) =>
                  mutate(
                    (state, role) => confirmBooking(state, role, input, settings),
                    content.messages.bookingCreated,
                  )
                }
              />
            ) : (
              <RecordDetails modal={activeModal} />
            )}
          </Modal>
        )}
        <AnimatePresence>
          {toast && (
            <motion.div
              role="status"
              className="toast"
              initial={reduced ? false : { opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: settings.animationSeconds }}
            >
              <Icon name="check" size={18} />
              <span>{toast}</span>
              <button
                className="icon-button"
                onClick={() => setToast('')}
                aria-label={content.labels.dismiss}
              >
                <Icon name="x" size={17} />
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </WorkspaceContext.Provider>
    </MotionConfig>
  );
}
