import type { CoreClient } from './core-client';

/** Session-scoped downloads: stale responses never reach a browser attachment. */
export class OwnerDownloads {
  private active: AbortController | null = null;
  private disposed = false;
  private readonly urls = new Map<string, ReturnType<typeof setTimeout>>();
  constructor(private readonly client: CoreClient) {}

  async save(path: string): Promise<boolean> {
    if (this.disposed) return false;
    this.cancel();
    const controller = new AbortController();
    this.active = controller;
    try {
      const { blob, filename } = await this.client.download(path, controller.signal);
      if (controller.signal.aborted || this.disposed || this.active !== controller) return false;
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = filename;
      document.body.append(anchor);
      try {
        anchor.click();
      } finally {
        anchor.remove();
        this.urls.set(
          url,
          setTimeout(() => this.release(url), 0),
        );
      }
      return true;
    } catch (error) {
      if (controller.signal.aborted || this.disposed) return false;
      throw error;
    } finally {
      if (this.active === controller) this.active = null;
    }
  }

  private release(url: string) {
    clearTimeout(this.urls.get(url));
    URL.revokeObjectURL(url);
    this.urls.delete(url);
  }
  cancel() {
    this.active?.abort();
    this.active = null;
    for (const url of this.urls.keys()) this.release(url);
  }
  dispose() {
    this.disposed = true;
    this.cancel();
  }
}
