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
test('owner voice release permits only the pinned media origins and rejects injected origins', () => {
  const media = {
    retellOrigin: 'https://api.example.test',
    dailyOrigins: [
      'https://*.media.example.test',
      'https://*.fallback1.example.test',
      'https://*.fallback2.example.test',
    ],
    dailySocketOrigins: [
      'wss://*.media.example.test',
      'wss://*.fallback1.example.test',
      'wss://*.fallback2.example.test',
    ],
    dailyIceOrigin: 'https://ice.example.test',
  };
  const policy = contentPolicy('<style>body{}</style><script>void 0</script>', true, media);
  assert.ok(policy.includes("connect-src 'self' https://api.example.test"));
  assert.ok(policy.includes("frame-src 'self' https://*.media.example.test"));
  assert.ok(policy.includes("worker-src 'self' blob:"));
  for (const origin of [...media.dailyOrigins, ...media.dailySocketOrigins, media.dailyIceOrigin])
    assert.ok(policy.includes(origin));
  assert.ok(!policy.includes("'unsafe-eval'"));
  assert.throws(() => contentPolicy('<style>x</style><script>x</script>', false, media));
  const baseline = {
    projectSlug: 'test-project',
    hostname: 'example.test',
    releaseId: 'test-release',
    loopbackPort: 18080,
    engineHostPort: 18081,
    containerPort: 8080,
    containerUid: 10001,
    containerGid: 10001,
    cpuLimit: 1,
    memoryLimitMiB: 128,
    pidLimit: 64,
    logMaxSizeMiB: 5,
    logMaxFiles: 2,
    healthIntervalSeconds: 10,
    healthTimeoutSeconds: 3,
    healthRetries: 3,
    image: 'nginx@sha256:' + '0'.repeat(64),
    securityHeaders: {
      'Referrer-Policy': 'no-referrer',
      'X-Content-Type-Options': 'nosniff',
      'X-Frame-Options': 'DENY',
      'Permissions-Policy': 'microphone=(self)',
      'Cache-Control': 'no-store, no-transform',
    },
    voiceMedia: media,
  };
  assert.deepEqual(deploymentSettings(baseline).voiceMedia.dailyOrigins, media.dailyOrigins);
  assert.throws(() =>
    deploymentSettings({
      ...baseline,
      voiceMedia: {
        ...media,
        dailyOrigins: ['https://bad.test; connect-src *', ...media.dailyOrigins.slice(1)],
      },
    }),
  );
});
test('deployment boundary rejects injected hostnames and incomplete configuration', () => {
  assert.throws(() =>
    deploymentSettings({ hostname: 'example.invalid\nreverse_proxy attacker.invalid' }),
  );
  assert.throws(() => deploymentSettings({}));
});
