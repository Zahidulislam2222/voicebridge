import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { createHash, randomBytes } from 'node:crypto';
import { resolve } from 'node:path';
import {
  engineDeploymentSchema,
  nativeApiMounts,
  prepareEngineRelease,
  workerNetworks,
} from './prepare-engine-release.mjs';
import { renderTemplate } from './prepare-frontend-release.mjs';

test('engine boundary refuses unconstrained resource limits and unpinned images', () => {
  assert.throws(() => engineDeploymentSchema.parse({ engineMemory: 4096 }));
  assert.throws(() => engineDeploymentSchema.shape.pythonImage.parse('python:latest'));
  assert.throws(() => engineDeploymentSchema.shape.engineCpu.parse(2));
  assert.throws(() =>
    engineDeploymentSchema.shape.postgresDataPath.parse('/srv/apps/unrelated/postgres'),
  );
});

test('live provider profile source is explicit and confined to ignored releases', async () => {
  const source = engineDeploymentSchema.shape.providerProfileSource;
  assert.equal(
    source.parse('.local/engine-releases/20261013-native-capture-06/provider-profiles.json'),
    '.local/engine-releases/20261013-native-capture-06/provider-profiles.json',
  );
  assert.throws(() => source.parse('../CREDENTIALS.md'));
  assert.throws(() => source.parse('.local/credentials/provider-profiles.json'));

  const suffix = randomBytes(8).toString('hex');
  const sourceId = `test-profile-source-${suffix}`;
  const releaseId = `test-profile-release-${suffix}`;
  const sourceDir = resolve('.local/engine-releases', sourceId);
  const releaseDir = resolve('.local/engine-releases', releaseId);
  const sourcePath = resolve(sourceDir, 'provider-profiles.json');
  const configPath = resolve(sourceDir, 'settings.json');
  const profile = Buffer.from('{"approvedTestProfile":true}\n');
  const pinned = `example@sha256:${'a'.repeat(64)}`;
  try {
    await mkdir(sourceDir, { recursive: true });
    await writeFile(sourcePath, profile);
    await writeFile(
      configPath,
      JSON.stringify({
        projectSlug: 'voicebridge-test',
        releaseId,
        engineImage: 'voicebridge-engine:test-release',
        providerProfileSource: `.local/engine-releases/${sourceId}/provider-profiles.json`,
        pythonImage: pinned,
        postgresImage: pinned,
        mailpitImage: pinned,
        hostname: 'example.test',
        hostPort: 18092,
        containerPort: 18080,
        containerBindHost: '127.0.0.1',
        dbPort: 5432,
        smtpHost: 'mailpit',
        smtpPort: 1025,
        frontendHostPort: 18091,
        uid: 10001,
        gid: 10001,
        engineMemory: 512,
        engineCpu: 0.5,
        dbMemory: 512,
        dbCpu: 0.5,
        mailMemory: 128,
        mailCpu: 0.1,
        observerMemory: 128,
        observerCpu: 0.1,
        observationDataPath: '/srv/apps/voicebridge-test/observation',
        pids: 96,
        logSize: 5,
        logFiles: 3,
        healthInterval: 15,
        healthTimeout: 5,
        healthRetries: 4,
        dbName: 'voicebridge_test',
        dbOwner: 'voicebridge_owner',
        dbRuntime: 'voicebridge_runtime',
        postgresUid: 999,
        postgresGid: 999,
        postgresDataPath: '/srv/apps/voicebridge-test/postgres',
        mailpitDataPath: '/srv/apps/voicebridge-test/mailpit',
        captureMessages: 100,
      }),
    );
    await prepareEngineRelease(configPath);
    const copied = await readFile(resolve(releaseDir, 'provider-profiles.json'));
    const manifest = JSON.parse(await readFile(resolve(releaseDir, 'release.json'), 'utf8'));
    assert.deepEqual(copied, profile);
    assert.equal(
      manifest.files['provider-profiles.json'],
      createHash('sha256').update(profile).digest('hex'),
    );
  } finally {
    await rm(releaseDir, { recursive: true, force: true });
    await rm(sourceDir, { recursive: true, force: true });
  }
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

test('worker egress is explicitly typed, disabled by default and leaves other services private', async () => {
  assert.equal(engineDeploymentSchema.shape.workerExternalAccess.parse(undefined), false);
  assert.throws(() => engineDeploymentSchema.shape.workerExternalAccess.parse('true'));
  assert.equal(workerNetworks(false), '[private]');
  assert.equal(workerNetworks(true), '[private, identity]');
  const source = await readFile(
    new URL('../deploy/engine-compose.yaml.template', import.meta.url),
    'utf8',
  );
  const worker = source.split('  worker:')[1].split('  observer:')[0];
  assert.match(worker, /networks: \{\{WORKER_NETWORKS\}\}/);
  for (const service of ['observer', 'postgres', 'mailpit']) {
    const section = source.split('\n  ' + service + ':\n')[1].split(/^  \w+:/m)[0];
    assert.match(section, /networks: \[private\]/);
  }
});

test('private native files mount read-only on API only when explicitly enabled', async () => {
  assert.equal(engineDeploymentSchema.shape.nativeApiMounts.parse(undefined), false);
  assert.throws(() => engineDeploymentSchema.shape.nativeApiMounts.parse('true'));
  assert.equal(nativeApiMounts(false), '');
  const mounted = nativeApiMounts(true);
  const names = [
    'runtime.env',
    'access.json',
    'provider-profiles.json',
    'native-request-bodies.json',
    'native-retell-approved.json',
    'native-free-entitlement.json',
  ];
  assert.equal(mounted.match(/:ro/g).length, 3);
  assert.equal(mounted.match(/create_host_path: false/g).length, 3);
  for (const name of names.slice(0, 3))
    assert.match(mounted, new RegExp(`\\./${name.replaceAll('.', '\\.')}:`));
  for (const name of names.slice(3))
    assert.match(mounted, new RegExp(`source: \\./${name.replaceAll('.', '\\.')}`));
  const source = await readFile(
    new URL('../deploy/engine-compose.yaml.template', import.meta.url),
    'utf8',
  );
  const api = source.split('  api:')[1].split('  worker:')[0];
  const worker = source.split('  worker:')[1].split('  observer:')[0];
  const observer = source.split('  observer:')[1].split('  postgres:')[0];
  assert.match(api, /\{\{NATIVE_API_MOUNTS\}\}/);
  for (const section of [worker, observer]) {
    for (const name of names.slice(3)) assert.doesNotMatch(section, new RegExp(name));
  }
});
