import { test } from 'node:test';
import assert from 'node:assert/strict';
import { contentPolicy, deploymentSettings, renderTemplate } from './prepare-frontend-release.mjs';
import { createHash } from 'node:crypto';

test('publication CSP hashes exact script/style bytes and denies remote connections', () => {
  const script = 'const greeting = "hello";',
    style = 'body { color: black; }';
  const policy = contentPolicy(`<style>${style}</style><script type="module">${script}</script>`);
  for (const source of [script, style])
    assert.ok(policy.includes(createHash('sha256').update(source).digest('base64')));
  assert.ok(policy.includes("connect-src 'none'"));
  assert.ok(policy.includes("frame-ancestors 'none'"));
  assert.ok(!policy.includes("script-src 'unsafe-inline'"));
  assert.throws(() => contentPolicy('<html>Missing compiled assets</html>'));
});
test('unknown release-template values fail instead of publishing unresolved configuration', () => {
  assert.equal(renderTemplate('listen {{PORT}};', { PORT: 8080 }), 'listen 8080;');
  assert.throws(() => renderTemplate('{{MISSING}}', {}), /Missing/);
  for (const token of ['{{PORT2}}', '{{port}}', '{{PORT}', '{PORT}}', '{{'])
    assert.throws(() => renderTemplate(token, { PORT: 8080 }), /Malformed/);
});
test('authenticated pilot permits only same-origin API connections', () => {
  const policy = contentPolicy('<style>body{}</style><script>void 0</script>', true);
  assert.ok(policy.includes("connect-src 'self'"));
  assert.ok(!policy.includes('https:'));
  assert.ok(policy.includes("form-action 'none'"));
});
test('deployment boundary rejects injected hostnames and incomplete configuration', () => {
  assert.throws(() =>
    deploymentSettings({ hostname: 'example.invalid\nreverse_proxy attacker.invalid' }),
  );
  assert.throws(() => deploymentSettings({}));
});
