import { readFileSync } from 'node:fs';

/** @typedef {{host:string, port:number, watch:{usePolling:boolean, interval:number}, coreProxy:string}} DevelopmentSettings */
/** @param {Record<string,string|undefined>} environment @returns {DevelopmentSettings} */
export function developmentSettings(environment) {
  const defaults = JSON.parse(
    readFileSync(new URL('../config/development.json', import.meta.url), 'utf8'),
  );
  const host = environment.VITE_DEV_HOST ?? defaults.host;
  const port = Number(environment.VITE_DEV_PORT ?? defaults.port);
  const polling = environment.VITE_DEV_POLLING ?? String(defaults.polling);
  const interval = Number(environment.VITE_DEV_POLL_INTERVAL_MS ?? defaults.pollIntervalMs);
  const coreProxy = environment.VITE_CORE_PROXY_TARGET ?? defaults.coreProxy;
  if (coreProxy) {
    const target = new URL(coreProxy);
    if (
      target.protocol !== 'http:' ||
      !['localhost', '127.0.0.1', '[::1]'].includes(target.hostname) ||
      target.username ||
      target.password ||
      target.search ||
      target.hash ||
      target.pathname !== '/'
    )
      throw new Error('Development core proxy must use a loopback origin');
  }
  if (!['127.0.0.1', 'localhost', '::1'].includes(host))
    throw new Error('Local preview host must be loopback');
  if (!Number.isInteger(port) || port < 1024 || port > 65535)
    throw new Error('Invalid VITE_DEV_PORT');
  if (!['true', 'false'].includes(polling)) throw new Error('Invalid VITE_DEV_POLLING');
  if (!Number.isInteger(interval) || interval < 100) throw new Error('Invalid polling interval');
  return { host, port, watch: { usePolling: polling === 'true', interval }, coreProxy };
}
