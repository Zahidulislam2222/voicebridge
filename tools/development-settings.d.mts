export interface DevelopmentSettings {
  host: string;
  port: number;
  watch: { usePolling: boolean; interval: number };
  coreProxy: string;
}
export function developmentSettings(
  environment: Record<string, string | undefined>,
): DevelopmentSettings;
