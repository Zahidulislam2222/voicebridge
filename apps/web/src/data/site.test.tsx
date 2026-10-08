import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { Showcase } from '../components/showcase';
import { publicPageKeys, isPublicPage } from '../protocol';
import { content, initialState } from './index';
import raw from './site.json';
import { site, validateSite } from './site';

const prohibited =
  /\b(?:demo(?:nstration)?|sample|synthetic|simulat(?:e|ed|ion)|illustrative|prototype|placeholder)\b/i;
function strings(value: unknown): string[] {
  if (typeof value === 'string') return [value];
  if (Array.isArray(value)) return value.flatMap(strings);
  if (value && typeof value === 'object') return Object.values(value).flatMap(strings);
  return [];
}
describe('complete public frontend contracts', () => {
  it('recognizes all eight public routes without accepting unknown routes', () => {
    for (const page of publicPageKeys) expect(isPublicPage(page)).toBe(true);
    expect(isPublicPage('unknown')).toBe(false);
    expect(isPublicPage('overview')).toBe(false);
  });
  it('requires complete maintained copy and rejects invalid renderer settings', () => {
    for (const key of Object.keys(raw.labels)) {
      const changed = structuredClone(raw);
      delete (changed.labels as Record<string, string>)[key];
      expect(() => validateSite(changed), key).toThrow();
    }
    const changed = structuredClone(raw);
    changed.visual.maxPixelRatio = 8;
    expect(() => validateSite(changed)).toThrow();
  });
  it('rejects duplicate public content identities', () => {
    const changed = structuredClone(raw);
    changed.resources[1]!.id = changed.resources[0]!.id;
    expect(() => validateSite(changed)).toThrow('Duplicate');
  });
  it('keeps prohibited presentation labels out of maintained visible content', () => {
    for (const value of [...strings(site), ...strings(content), ...strings(initialState())])
      expect(value).not.toMatch(prohibited);
  });
  for (const page of publicPageKeys)
    it(`renders complete ${page} structure and shared navigation`, () => {
      const html = renderToStaticMarkup(<Showcase page={page} />);
      expect(html).toContain(`data-public-page="${page}"`);
      expect(html).toContain('<h1');
      expect(html).toContain('site-footer');
      for (const link of site.nav) expect(html).toContain(`href="#/${link.id}"`);
    });
  it('provides substantial homepage sections and readable resource articles', () => {
    const html = renderToStaticMarkup(<Showcase />);
    for (const part of [
      'how-it-works',
      'product-overview',
      'site-capabilities',
      'site-industries',
      'site-integrations',
      'site-faq',
      'site-final',
    ])
      expect(html).toContain(part);
    for (const article of site.resources) {
      const rendered = renderToStaticMarkup(<Showcase page="resources" articleId={article.id} />);
      for (const paragraph of article.paragraphs)
        expect(rendered).toContain(paragraph.replaceAll('&', '&amp;'));
    }
  });
});
