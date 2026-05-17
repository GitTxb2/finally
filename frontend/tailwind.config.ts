import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        accent: '#ecad0a',
        primary: '#209dd7',
        submit: '#753991',
        'bg-base': '#0d1117',
        'bg-elevated': '#1a1a2e',
        'flash-up': 'rgba(34, 197, 94, 0.35)',
        'flash-down': 'rgba(239, 68, 68, 0.35)',
      },
      transitionDuration: {
        flash: '500ms',
      },
      fontFamily: {
        mono: [
          'ui-monospace',
          'SFMono-Regular',
          'Menlo',
          'Monaco',
          'Consolas',
          'monospace',
        ],
      },
    },
  },
  plugins: [],
};

export default config;
