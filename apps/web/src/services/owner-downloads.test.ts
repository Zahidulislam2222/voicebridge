import { afterEach, describe, expect, it, vi } from 'vitest';
import { OwnerDownloads } from './owner-downloads';
import { CoreClient, CoreRequestError } from './core-client';

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});
function browser() {
  vi.useFakeTimers();
  const anchor = { href: '', download: '', click: vi.fn(), remove: vi.fn() };
  vi.stubGlobal('document', { createElement: () => anchor, body: { append: vi.fn() } });
  const create = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:test');
  const revoke = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});
  return { anchor, create, revoke };
}
describe('owner download lifecycle', () => {
  it('allows reuse after effect cancellation and only saves the latest request', async () => {
    const { create } = browser();
    const pending: ((value: { blob: Blob; filename: string }) => void)[] = [];
    vi.spyOn(CoreClient.prototype, 'download').mockImplementation(
      () => new Promise((resolve) => pending.push(resolve)),
    );
    const downloads = new OwnerDownloads(new CoreClient('test-key'));
    downloads.cancel();
    const first = downloads.save('/api/exports/snapshot');
    const second = downloads.save('/api/calls/test-call/transcript-export');
    pending[0]!({ blob: new Blob(['old']), filename: 'old.json' });
    expect(await first).toBe(false);
    pending[1]!({ blob: new Blob(['new']), filename: 'new.json' });
    expect(await second).toBe(true);
    expect(create).toHaveBeenCalledOnce();
    downloads.dispose();
  });
  it('downloads the exact attachment and releases its URL after click', async () => {
    const { anchor, create, revoke } = browser();
    const blob = new Blob(['{"schema_version":1}'], { type: 'application/json' });
    vi.spyOn(CoreClient.prototype, 'download').mockResolvedValue({
      blob,
      filename: 'test-records.json',
    });
    const downloads = new OwnerDownloads(new CoreClient('test-key'));
    expect(await downloads.save('/api/exports/snapshot')).toBe(true);
    expect(create).toHaveBeenCalledWith(blob);
    expect(anchor.download).toBe('test-records.json');
    expect(anchor.click).toHaveBeenCalledOnce();
    expect(anchor.remove).toHaveBeenCalledOnce();
    vi.runAllTimers();
    expect(revoke).toHaveBeenCalledExactlyOnceWith('blob:test');
    downloads.dispose();
    expect(revoke).toHaveBeenCalledOnce();
  });
  it.each(['cancel', 'dispose'] as const)(
    'discards a late result after %s even when transport ignores abort',
    async (method) => {
      const { create } = browser();
      let resolve!: (value: { blob: Blob; filename: string }) => void;
      let signal!: AbortSignal;
      vi.spyOn(CoreClient.prototype, 'download').mockImplementation((_path, received) => {
        signal = received;
        return new Promise((done) => {
          resolve = done;
        });
      });
      const downloads = new OwnerDownloads(new CoreClient('test-key'));
      const result = downloads.save('/api/exports/snapshot');
      downloads[method]();
      expect(signal.aborted).toBe(true);
      resolve({ blob: new Blob(['private']), filename: 'test.json' });
      expect(await result).toBe(false);
      expect(create).not.toHaveBeenCalled();
    },
  );
  it('surfaces session denial without creating an attachment', async () => {
    const { create } = browser();
    vi.spyOn(CoreClient.prototype, 'download').mockRejectedValue(
      new CoreRequestError('session_expired'),
    );
    await expect(
      new OwnerDownloads(new CoreClient('test-key')).save('/api/exports/snapshot'),
    ).rejects.toThrow('session expired');
    expect(create).not.toHaveBeenCalled();
  });
  it('releases a started URL synchronously on connection cleanup', async () => {
    const { revoke } = browser();
    vi.spyOn(CoreClient.prototype, 'download').mockResolvedValue({
      blob: new Blob(['private']),
      filename: 'test.json',
    });
    const downloads = new OwnerDownloads(new CoreClient('test-key'));
    await downloads.save('/api/exports/snapshot');
    downloads.dispose();
    expect(revoke).toHaveBeenCalledExactlyOnceWith('blob:test');
    vi.runAllTimers();
    expect(revoke).toHaveBeenCalledOnce();
    expect(await downloads.save('/api/exports/snapshot')).toBe(false);
  });
});
