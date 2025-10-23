import { initPlasmicLoader } from '@plasmicapp/loader-nextjs';

export const PLASMIC = initPlasmicLoader({
  projects: [
    {
      id: process.env.REACT_APP_PLASMIC_PROJECT_ID || process.env.VITE_PLASMIC_PROJECT_ID || '',
      token: process.env.REACT_APP_PLASMIC_PROJECT_TOKEN || process.env.VITE_PLASMIC_PROJECT_TOKEN || '',
    },
  ],
  preview: process.env.NODE_ENV === 'development',
});