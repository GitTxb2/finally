import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}', './lib/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Project palette per PLAN.md §2
        bg: {
          base: '#0d1117',
          panel: '#11161d',
          raised: '#161c25',
          deep: '#0a0d12',
          night: '#1a1a2e',
        },
        edge: {
          DEFAULT: '#1f2630',
          strong: '#2a323e',
          hot: '#3a4452',
        },
        ink: {
          DEFAULT: '#e6edf3',
          dim: '#9aa4b2',
          mute: '#6b7585',
          ghost: '#4b5563',
        },
        accent: {
          yellow: '#ecad0a',
          blue: '#209dd7',
          purple: '#753991',
        },
        tape: {
          up: '#3ddc97',
          down: '#ff5f6d',
          flat: '#9aa4b2',
        },
      },
      fontFamily: {
        display: ['var(--font-display)', 'ui-sans-serif', 'system-ui'],
        mono: ['var(--font-mono)', 'ui-monospace', 'SFMono-Regular', 'Menlo'],
      },
      letterSpacing: {
        wider2: '0.18em',
        wider3: '0.28em',
      },
      keyframes: {
        flashUp: {
          '0%': { backgroundColor: 'rgba(61, 220, 151, 0.45)' },
          '100%': { backgroundColor: 'rgba(61, 220, 151, 0)' },
        },
        flashDown: {
          '0%': { backgroundColor: 'rgba(255, 95, 109, 0.45)' },
          '100%': { backgroundColor: 'rgba(255, 95, 109, 0)' },
        },
        pulseDot: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.35' },
        },
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
      },
      animation: {
        'flash-up': 'flashUp 500ms ease-out',
        'flash-down': 'flashDown 500ms ease-out',
        'pulse-dot': 'pulseDot 1.6s ease-in-out infinite',
        scanline: 'scanline 8s linear infinite',
      },
      boxShadow: {
        panel: '0 1px 0 rgba(255,255,255,0.02) inset, 0 1px 24px rgba(0,0,0,0.35)',
      },
    },
  },
  plugins: [],
};

export default config;
