import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { engineDeploymentSchema } from './prepare-engine-release.mjs';
import { renderTemplate } from './prepare-frontend-release.mjs';

test('engine boundary refuses unconstrained resource limits and unpinned images', () => {
  assert.throws(() => engineDeploymentSchema.parse({ engineMemory: 4096 }));
  assert.throws(() => engineDeploymentSchema.shape.pythonImage.parse('python:latest'));
  assert.throws(() => engineDeploymentSchema.shape.engineCpu.parse(2));
  assert.throws(() =>
    engineDeploymentSchema.shape.postgresDataPath.parse('/srv/apps/unrelated/postgres'),
  );
});

test('engine services preserve private DB, loopback gateway, constraints and capture delivery', async () => {
  const source = await readFile(
    new URL('../deploy/engine-compose.yaml.template', import.meta.url),
    'utf8',
  );
  assert.match(source, /ports: \["127\.0\.0\.1:/);
  assert.match(source, /private: \{internal: true\}/);
  assert.match(source, /POSTGRES_PASSWORD_FILE/);
  assert.match(source, /cap_drop: \[ALL\]/);
  assert.match(source, /read_only: true/);
  assert.match(
    source,
    /\.\/provider-profiles\.json:\/run\/voicebridge\/provider-profiles\.json:ro/,
  );
  assert.doesNotMatch(source, /MP_SMTP_RELAY/);
  const database = source.split('  postgres:')[1].split('  mailpit:')[0];
  assert.doesNotMatch(database, /ports:/);
  assert.throws(() => renderTemplate(source, {}), /Missing template value/);
});

test('Docker context is an allowlist with no credential or memory inclusion', async () => {
  const source = await readFile(new URL('../.dockerignore', import.meta.url), 'utf8');
  assert.ok(source.startsWith('**\n'));
  assert.doesNotMatch(source, /!.*(?:CREDENTIALS|memory|\.local|\.env)/);
});
