import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@app': path.resolve(__dirname, './src/app'),
      '@features': path.resolve(__dirname, './src/features'),
      '@shared': path.resolve(__dirname, './src/shared'),
      '@core': path.resolve(__dirname, './src/core'),
      '@assets': path.resolve(__dirname, './src/assets'),
    },
  },
  server: {
    port: 6770,
    proxy: {
      '/api': {
        target: 'http://localhost:6769',
        changeOrigin: true,
        // Generous timeouts for long-running requests such as a bulk employee
        // import, which the dev proxy would otherwise abort.
        timeout: 600000,
        proxyTimeout: 600000,
      },
    },
  },
  // Pre-bundle deps up front so Vite never discovers a new dependency
  // mid-session and forces a full-page reload to re-optimize.
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-dom/client',
      'react-router-dom',
      'react-redux',
      '@reduxjs/toolkit',
      '@tanstack/react-query',
      'axios',
      'react-hook-form',
      '@hookform/resolvers/zod',
      'zod',
      'primereact/api',
      'primereact/avatar',
      'primereact/badge',
      'primereact/button',
      'primereact/calendar',
      'primereact/card',
      'primereact/column',
      'primereact/confirmdialog',
      'primereact/datatable',
      'primereact/dialog',
      'primereact/divider',
      'primereact/dropdown',
      'primereact/inputnumber',
      'primereact/inputswitch',
      'primereact/inputtext',
      'primereact/inputtextarea',
      'primereact/menu',
      'primereact/message',
      'primereact/password',
      'primereact/progressspinner',
      'primereact/tag',
      'primereact/toast',
      'primereact/toolbar',
      'primereact/tooltip',
      'primereact/tree',
    ],
  },
});
