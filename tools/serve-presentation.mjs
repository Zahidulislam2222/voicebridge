import { readFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { developmentSettings } from './development-settings.mjs';

const settings = developmentSettings(process.env);
const artifact = new URL('../VoiceBridge-preview.html', import.meta.url);
await readFile(artifact);
const server = createServer(async (request, response) => {
  const pathname = (request.url ?? '/').split('?')[0];
  if (pathname !== '/' || !['GET', 'HEAD'].includes(request.method ?? '')) {
    response.writeHead(404);
    response.end();
    return;
  }
  try {
    const html = await readFile(artifact);
    response.writeHead(200, {
      'Content-Type': 'text/html; charset=utf-8',
      'X-Content-Type-Options': 'nosniff',
      'Cache-Control': 'no-store',
      'Referrer-Policy': 'no-referrer',
    });
    response.end(request.method === 'HEAD' ? undefined : html);
  } catch {
    response.writeHead(503);
    response.end();
  }
});
server.on('error', (error) => {
  console.error('Preview could not start:', error.message);
  process.exitCode = 1;
});
server.listen(settings.port, settings.host, () =>
  console.log(
    `VoiceBridge local demo: http://${settings.host}:${settings.port}\nKeep this terminal open. Ctrl+C stops the preview.`,
  ),
);
