import { readFile, writeFile, readdir, rename } from 'node:fs/promises';
import { resolve } from 'node:path';
import { artworkElementId, artworkDataPattern } from './presentation-protocol.mjs';

const root = resolve(process.argv[2] ?? '.');
const dist = resolve(root, 'apps/web/dist');
const files = await readdir(resolve(dist, 'assets'));
const jsName = files.find((name) => /^index-.*\.js$/.test(name));
const cssName = files.find((name) => /^index-.*\.css$/.test(name));
if (!jsName || !cssName) throw new Error('Build frontend before creating the presentation preview');
const content = JSON.parse(await readFile(resolve(root, 'apps/web/src/data/content.json'), 'utf8'));
const image = await readFile(resolve(dist, content.assets.hero));
const imageUrl = 'data:image/png;base64,' + image.toString('base64');
if (!artworkDataPattern.test(imageUrl)) throw new Error('Invalid embedded artwork transport');
const js = (await readFile(resolve(dist, 'assets', jsName), 'utf8')).replaceAll(
  '</script',
  '<\\/script',
);
let css = await readFile(resolve(dist, 'assets', cssName), 'utf8');
const fontReferences = [...css.matchAll(/url\((['"]?)\/fonts\/([a-z-]+\.woff2)\1\)/g)];
for (const match of fontReferences) {
  const font = await readFile(resolve(dist, 'fonts', match[2]));
  css = css.replaceAll(match[0], `url(data:font/woff2;base64,${font.toString('base64')})`);
}
if (/@import|url\(['"]?https?:|url\(['"]?\/fonts\//.test(css))
  throw new Error('Presentation styles still reference external resources');
const favicon = await readFile(resolve(dist, 'favicon.svg'), 'utf8');
let html = await readFile(resolve(dist, 'index.html'), 'utf8');
html = html
  .replace('</head>', () => `<meta id="${artworkElementId}" content="${imageUrl}"></head>`)
  .replace(
    /<script type="module" crossorigin src="[^"]+"><\/script>/,
    () => `<script type="module">${js}</script>`,
  )
  .replace(/<link rel="stylesheet" crossorigin href="[^"]+">/, () => `<style>${css}</style>`)
  .replace('href="/favicon.svg"', `href="data:image/svg+xml,${encodeURIComponent(favicon)}"`);
if (html.includes('src="/assets/') || html.includes('href="/assets/'))
  throw new Error('Preview still references external build files');
const output = resolve(root, 'VoiceBridge-preview.html');
await writeFile(output + '.tmp', html);
await rename(output + '.tmp', output);
console.log(`Presentation preview written (${Buffer.byteLength(html)} bytes)`);
