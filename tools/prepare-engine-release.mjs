import { readFile, writeFile, mkdir, stat } from 'node:fs/promises';
import { resolve } from 'node:path';
import { createHash } from 'node:crypto';
import { z } from 'zod';
import { renderTemplate } from './prepare-frontend-release.mjs';

const integer = z.number().int().positive();
const image = z.string().regex(/^[a-z0-9./:_-]+@sha256:[a-f0-9]{64}$/);
export const engineDeploymentSchema = z.object({
  projectSlug: z.string().regex(/^[a-z][a-z0-9-]+$/),
  releaseId: z.string().regex(/^[a-z0-9-]+$/),
  engineImage: z.string().regex(/^voicebridge-engine:[a-z0-9-]+$/),
  pythonImage: image,
  postgresImage: image,
  mailpitImage: image,
  hostname: z.string().regex(/^[a-z0-9.-]+$/),
  hostPort: integer.max(65535),
  containerPort: integer.max(65535),
  containerBindHost: z.ipv4(),
  dbPort: integer.max(65535),
  smtpHost: z.string().regex(/^[a-z0-9-]+$/),
  smtpPort: integer.max(65535),
  frontendHostPort: integer.max(65535),
  uid: integer,
  gid: integer,
  engineMemory: integer.max(1024),
  engineCpu: z.number().positive().max(1),
  dbMemory: integer.max(1024),
  dbCpu: z.number().positive().max(1),
  mailMemory: integer.max(256),
  mailCpu: z.number().positive().max(0.5),
  observerMemory: integer.max(256),
  observerCpu: z.number().positive().max(0.25),
  observationDataPath: z.string().regex(/^\/srv\/apps\/voicebridge[^\s]*\/observation$/),
  pids: integer.max(128),
  logSize: integer.max(20),
  logFiles: integer.max(5),
  healthInterval: integer,
  healthTimeout: integer,
  healthRetries: integer,
  dbName: z.string().regex(/^[a-z_][a-z0-9_]+$/),
  dbOwner: z.string().regex(/^[a-z_][a-z0-9_]+$/),
  dbRuntime: z.string().regex(/^[a-z_][a-z0-9_]+$/),
  postgresUid: integer,
  postgresGid: integer,
  postgresDataPath: z.string().regex(/^\/srv\/apps\/voicebridge[^\s]*\/postgres$/),
  mailpitDataPath: z.string().regex(/^\/srv\/apps\/voicebridge[^\s]*\/mailpit$/),
  captureMessages: integer.max(10000),
});

export async function prepareEngineRelease(configurationFile) {
  const settings = engineDeploymentSchema.parse(
    JSON.parse(await readFile(configurationFile, 'utf8')),
  );
  const output = resolve('.local/engine-releases', settings.releaseId);
  try {
    await stat(output);
    throw new Error('Release already exists; use a new release ID');
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
  }
  await mkdir(output, { recursive: true });
  const values = Object.fromEntries(
    Object.entries(settings).map(([k, v]) => [
      k.replace(/[A-Z]/g, (c) => '_' + c).toUpperCase(),
      v,
    ]),
  );
  Object.assign(values, {
    ENGINE_HOST_PORT: settings.hostPort,
    FRONTEND_HOST_PORT: settings.frontendHostPort,
    ENGINE_MEMORY: settings.engineMemory,
    ENGINE_CPU: settings.engineCpu,
    HEALTH_URL: `http://127.0.0.1:${settings.containerPort}/health/ready`,
  });
  for (const [template, name] of [
    ['engine-compose.yaml.template', 'compose.yaml'],
    ['engine-site.caddy.template', 'site.caddy'],
  ]) {
    const content = renderTemplate(await readFile(resolve('deploy', template), 'utf8'), values);
    await writeFile(resolve(output, name), content);
  }
  await writeFile(
    resolve(output, 'provider-profiles.json'),
    await readFile(resolve('config/provider-profiles.json')),
  );
  const manifest = {
    releaseId: settings.releaseId,
    files: {},
    status: 'PREPARED_PRIVATE_NOT_PUBLIC',
  };
  for (const name of ['compose.yaml', 'site.caddy', 'provider-profiles.json']) {
    manifest.files[name] = createHash('sha256')
      .update(await readFile(resolve(output, name)))
      .digest('hex');
  }
  await writeFile(resolve(output, 'release.json'), JSON.stringify(manifest, null, 2) + '\n');
  return { output, files: 3, releaseId: settings.releaseId };
}
if (process.argv[1] && resolve(process.argv[1]) === resolve(import.meta.filename))
  console.log(JSON.stringify(await prepareEngineRelease(process.argv[2])));
