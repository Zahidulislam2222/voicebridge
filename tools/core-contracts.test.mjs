import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import openapiTS, { astToString, COMMENT_HEADER } from 'openapi-typescript';
import { format } from 'prettier';

test('generated frontend contracts match the reviewed OpenAPI artifact', async () => {
  const schema = JSON.parse(
    await readFile(new URL('../docs/api/core-openapi.json', import.meta.url), 'utf8'),
  );
  const options = JSON.parse(
    await readFile(new URL('../.prettierrc.json', import.meta.url), 'utf8'),
  );
  const expected = await format(COMMENT_HEADER + astToString(await openapiTS(schema)), {
    ...options,
    parser: 'typescript',
  });
  const actual = await readFile(
    new URL('../apps/web/src/generated/core-api.ts', import.meta.url),
    'utf8',
  );
  assert.equal(actual, expected);
});
