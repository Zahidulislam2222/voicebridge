import { readFile, writeFile, mkdir, stat } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { resolve } from 'node:path';
import { z } from 'zod';

const port = z.number().int().min(1024).max(65535);
const safeHeader = z
  .string()
  .min(1)
  .max(300)
  .regex(/^[^"\r\n\\]+$/);
const schema = z.object({
  projectSlug: z.string().regex(/^[a-z][a-z0-9-]{1,50}$/),
  hostname: z.string().regex(/^(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}$/),
  releaseId: z.string().regex(/^[a-z0-9][a-z0-9-]{1,70}$/),
  loopbackPort: port,
  engineHostPort: port.optional(),
  containerPort: port,
  containerUid: z.number().int().positive(),
  containerGid: z.number().int().positive(),
  cpuLimit: z.number().positive().max(2),
  memoryLimitMiB: z.number().int().min(64).max(512),
  pidLimit: z.number().int().min(16).max(128),
  logMaxSizeMiB: z.number().int().min(1).max(20),
  logMaxFiles: z.number().int().min(1).max(5),
  healthIntervalSeconds: z.number().int().min(5).max(60),
  healthTimeoutSeconds: z.number().int().min(1).max(10),
  healthRetries: z.number().int().min(1).max(5),
  image: z.string().regex(/^nginx@sha256:[a-f0-9]{64}$/),
  securityHeaders: z
    .object({
      'Referrer-Policy': safeHeader,
      'X-Content-Type-Options': z.literal('nosniff'),
      'X-Frame-Options': z.literal('DENY'),
      'Permissions-Policy': safeHeader,
      'Cache-Control': z.literal('no-store, no-transform'),
    })
    .strict(),
});
/** Typed deployment boundary: unknown access/credential fields are never copied into releases.
 * @param {unknown} input
 */
export function deploymentSettings(input) {
  return schema.parse(input);
}
/** @param {string} template @param {Record<string, string|number>} values */
export function renderTemplate(template, values) {
  const rendered = template.replace(/\{\{([A-Z_]+)\}\}/g, (_, key) => {
    if (!Object.hasOwn(values, key)) throw new Error(`Missing template value: ${key}`);
    return String(values[key]);
  });
  if (/\{\{|\}\}/.test(rendered)) throw new Error('Malformed or unresolved template token');
  return rendered;
}
const digest = (value) => createHash('sha256').update(value).digest('hex');
const hashSource = (value) =>
  "'sha256-" + createHash('sha256').update(value).digest('base64') + "'";
/** @param {string} html */
export function contentPolicy(html, sameOriginConnections = false) {
  const scripts = [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)].map((match) =>
    hashSource(match[1]),
  );
  const styles = [...html.matchAll(/<style\b[^>]*>([\s\S]*?)<\/style>/g)].map((match) =>
    hashSource(match[1]),
  );
  if (!scripts.length || !styles.length) throw new Error('Expected packaged script and styles');
  return `default-src 'none'; script-src ${scripts.join(' ')}; style-src ${styles.join(' ')}; style-src-attr 'unsafe-inline'; img-src data:; font-src data:; connect-src ${sameOriginConnections ? "'self'" : "'none'"}; worker-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'`;
}
export async function prepareRelease(root, configurationFile) {
  const settings = deploymentSettings(JSON.parse(await readFile(configurationFile, 'utf8')));
  const output = resolve(root, '.local/releases', settings.releaseId);
  try {
    await stat(output);
    throw new Error('Release already exists; use a new release ID');
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
  }
  const html = await readFile(resolve(root, 'VoiceBridge-preview.html'), 'utf8');
  const values = {
    PROJECT_SLUG: settings.projectSlug,
    HOSTNAME: settings.hostname,
    IMAGE: settings.image,
    HOST_PORT: settings.loopbackPort,
    CONTAINER_PORT: settings.containerPort,
    UID: settings.containerUid,
    GID: settings.containerGid,
    CPU: settings.cpuLimit,
    MEMORY: settings.memoryLimitMiB,
    PIDS: settings.pidLimit,
    LOG_SIZE: settings.logMaxSizeMiB,
    LOG_FILES: settings.logMaxFiles,
    HEALTH_INTERVAL: settings.healthIntervalSeconds,
    HEALTH_TIMEOUT: settings.healthTimeoutSeconds,
    HEALTH_RETRIES: settings.healthRetries,
    CSP: contentPolicy(html, settings.engineHostPort !== undefined),
    ENGINE_HOST_PORT: settings.engineHostPort ?? settings.loopbackPort,
    FRONTEND_HOST_PORT: settings.loopbackPort,
    SECURITY_HEADERS: Object.entries(settings.securityHeaders)
      .map(([key, value]) => `    add_header ${key} "${value}" always;`)
      .join('\n'),
  };
  const files = new Map([['html/index.html', html]]);
  for (const [template, destination] of [
    ['compose.yaml.template', 'compose.yaml'],
    ['nginx.conf.template', 'nginx.conf'],
    [
      settings.engineHostPort === undefined ? 'site.caddy.template' : 'engine-site.caddy.template',
      'site.caddy',
    ],
  ])
    files.set(
      destination,
      renderTemplate(await readFile(resolve(root, 'deploy', template), 'utf8'), values),
    );
  await mkdir(resolve(output, 'html'), { recursive: true });
  const hashes = {};
  for (const [name, contents] of files) {
    await writeFile(resolve(output, name), contents);
    hashes[name] = digest(contents);
  }
  await writeFile(
    resolve(output, 'SHA256SUMS'),
    Object.entries(hashes)
      .map(([name, hash]) => `${hash}  ${name}`)
      .join('\n') + '\n',
  );
  await writeFile(
    resolve(output, 'release.json'),
    JSON.stringify(
      {
        releaseId: settings.releaseId,
        projectSlug: settings.projectSlug,
        hostname: settings.hostname,
        loopbackPort: settings.loopbackPort,
        image: settings.image,
        files: hashes,
        status: 'PREPARED_LOCALLY_NOT_PUBLISHED',
      },
      null,
      2,
    ) + '\n',
  );
  return { output, files: files.size, releaseId: settings.releaseId };
}
if (process.argv[1] && resolve(process.argv[1]) === resolve(import.meta.filename)) {
  if (!process.argv[2]) throw new Error('Pass the existing deployment settings JSON path');
  console.log(JSON.stringify(await prepareRelease(resolve('.'), resolve(process.argv[2]))));
}
