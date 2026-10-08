import type { ReactNode } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import { Showcase } from '../components/showcase';
import { content, initialState } from '../data';
import type { Workspace } from '../workspace';
import { WorkspaceContext } from '../workspace';
import { Overview } from './overview';
import { Appointments, Audit, Automations, Calls, Contacts, Knowledge } from './records';
import { Agents, Evaluations, Integrations, Usage, Voices } from './configuration';

function render(view: ReactNode, overrides: Partial<Workspace> = {}) {
  const state = initialState();
  const workspace: Workspace = {
    state,
    role: 'operator',
    query: '',
    agentEditor: state.agent,
    setQuery: () => {},
    setAgentEditor: () => {},
    open: () => {},
    mutate: () => {
      throw new Error('Rendering must not mutate state');
    },
    ...overrides,
  };
  return renderToStaticMarkup(
    <WorkspaceContext.Provider value={workspace}>{view}</WorkspaceContext.Provider>,
  );
}

describe('workspace component contracts', () => {
  it('uses separately embedded artwork in both introduction and overview', () => {
    const embedded = 'data:image/png;base64,dGVzdA==';
    vi.stubGlobal('document', { getElementById: () => ({ getAttribute: () => embedded }) });
    try {
      for (const view of [<Showcase />, <Overview />]) {
        const html = render(view);
        expect(html).toContain(`src="${embedded}"`);
        expect(html).not.toContain(`src="${content.assets.hero}"`);
      }
    } finally {
      vi.unstubAllGlobals();
    }
  });
  const pages = {
    Overview,
    Agents,
    Voices,
    Calls,
    Appointments,
    Contacts,
    Automations,
    Knowledge,
    Evaluations,
    Integrations,
    Usage,
    Audit,
  };
  for (const [name, Page] of Object.entries(pages)) {
    it(`renders ${name} with the validated synthetic fixture`, () => {
      expect(render(<Page />)).toMatch(/<(?:section|div|table)\b/);
    });
  }
  it('disables every agent form control for a viewer while preserving operator editing', () => {
    const controls = (html: string) =>
      html.match(/<(?:input|textarea|select|button)\b[^>]*>/g) ?? [];
    const operator = controls(render(<Agents />));
    const viewer = controls(render(<Agents />, { role: 'viewer' }));
    expect(operator.length).toBeGreaterThan(0);
    expect(viewer).toHaveLength(operator.length);
    expect(operator.every((tag) => !tag.includes('disabled'))).toBe(true);
    expect(viewer.every((tag) => tag.includes('disabled'))).toBe(true);
  });
  it('escapes uploaded script-like knowledge content during component rendering', () => {
    const state = initialState();
    const unsafe = '<script>alert("test")</script>';
    state.documents[0]!.text = unsafe;
    const html = render(<Knowledge />, { state });
    expect(html).not.toContain(unsafe);
    expect(html).toContain('&lt;script&gt;');
  });
  it('disables the native knowledge file input for a viewer and allows operator upload', () => {
    const fileInput = (html: string) => html.match(/<input\b[^>]*type="file"[^>]*>/)?.[0];
    const viewer = fileInput(render(<Knowledge />, { role: 'viewer' }));
    const operator = fileInput(render(<Knowledge />));
    expect(viewer).toBeDefined();
    expect(operator).toBeDefined();
    expect(viewer).toContain('disabled');
    expect(operator).not.toContain('disabled');
  });
  it('uses the unsaved draft voice in both the editor and catalogue', () => {
    const state = initialState();
    const voice = content.voiceProfiles.find((item) => item.id !== state.agent.voiceId);
    if (!voice) throw new Error('A second voice is required for this regression');
    const agentEditor = { ...state.agent, voiceId: voice.id };
    expect(render(<Agents />, { agentEditor })).toContain(`<h2>${voice.name}</h2>`);
    const cards =
      render(<Voices />, { agentEditor }).match(/<article\b[^>]*>[\s\S]*?<\/article>/g) ?? [];
    const selected = cards.filter((card) => card.includes(`>${content.labels.selected}</span>`));
    expect(selected).toHaveLength(1);
    expect(selected[0]).toContain(`<h2>${voice.name}</h2>`);
  });
});
