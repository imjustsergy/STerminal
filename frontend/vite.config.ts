/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vite.dev/config/
export default defineConfig({
  plugins: [svelte()],
  // Vitest necesita que el plugin de Svelte compile en modo cliente (no SSR) para que
  // los componentes se puedan montar en jsdom — ver
  // https://vite-plugin-svelte.svelte.dev/docs/faq#vitest
  resolve: process.env.VITEST ? { conditions: ['browser'] } : undefined,
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
  },
})
