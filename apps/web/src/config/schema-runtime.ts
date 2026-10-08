import { z } from 'zod';

// Strict browser CSP forbids runtime code generation. Configure before any schema.
z.config({ jitless: true });
export { z };
