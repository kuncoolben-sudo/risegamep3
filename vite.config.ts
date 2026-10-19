import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// VITE_BASE is set by the Pages workflow (e.g. /risegamep4/); local dev uses /
export default defineConfig({ base: process.env.VITE_BASE ?? '/', plugins: [react()] });
