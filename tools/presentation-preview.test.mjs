import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile, readdir } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { artworkElementId, artworkDataPattern } from './presentation-protocol.mjs';

const html = await readFile(new URL('../VoiceBridge-preview.html', import.meta.url), 'utf8');

test('presentation preserves the compiled application and its validated product data', async () => {
  const assets = new URL('../apps/web/dist/assets/', import.meta.url);
  const name = (await readdir(assets)).find((file) => /^index-.*\.js$/.test(file));
  assert.ok(name, 'compiled application must exist');
  const original = await readFile(new URL(name, assets), 'utf8');
  const script = html.match(/<script type="module">([\s\S]*?)<\/script>/);
  assert.ok(script, 'embedded application module must exist');
  const fingerprint = (text) =>
    createHash('sha256').update(text.replaceAll('<\\/script', '</script')).digest('hex');
  assert.equal(fingerprint(script[1]), fingerprint(original));
});

test('presentation embeds the exact original PNG separately from product data', async () => {
  const meta = html.match(new RegExp(`<meta id="${artworkElementId}" content="([^"]+)">`));
  assert.ok(meta, 'separate artwork transport must exist');
  assert.match(meta[1], artworkDataPattern);
  const content = JSON.parse(
    await readFile(new URL('../apps/web/src/data/content.json', import.meta.url), 'utf8'),
  );
  const original = await readFile(
    new URL('../apps/web/dist/' + content.assets.hero, import.meta.url),
  );
  const embedded = Buffer.from(meta[1].split(',')[1], 'base64');
  assert.deepEqual(embedded, original);
  assert.equal(html.split(`id="${artworkElementId}"`).length - 1, 1);
});

test('presentation resolves its fonts and build files without external assets', () => {
  assert.equal((html.match(/data:font\/woff2;base64,/g) ?? []).length, 2);
  assert.doesNotMatch(html, /fonts\.googleapis\.com|fonts\.gstatic\.com|(?:src|href)="\/assets\//);
});
