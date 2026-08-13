import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from '@app/App';

// Self-hosted font (no external CDN)
import '@fontsource/dm-sans/400.css';
import '@fontsource/dm-sans/500.css';
import '@fontsource/dm-sans/600.css';
import '@fontsource/dm-sans/700.css';

// PrimeReact CSS
import 'primereact/resources/themes/lara-light-blue/theme.css';
import 'primereact/resources/primereact.min.css';
import 'primeicons/primeicons.css';
import 'primeflex/primeflex.css';

// Emcure theme overrides (must come after PrimeReact CSS)
import '@assets/styles/theme-overrides.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
