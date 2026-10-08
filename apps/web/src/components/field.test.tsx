import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { Field } from './ui';

describe('field accessible name', () => {
  it('names a select from its label and describes its hint separately', () => {
    const html = renderToStaticMarkup(
      <Field label="Service" hint="Business timezone">
        <select>
          <option>Choose a service</option>
        </select>
      </Field>,
    );
    expect(html).toContain('aria-labelledby=');
    expect(html).toContain('aria-describedby=');
  });
});
