import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

// Verification fixtures must not inherit a developer's private environment files.
export default defineConfig({ plugins: [react()], envDir: false });
