import type { Config } from 'tailwindcss';

export default {
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        category: {
          yellow: '#F9DF6D',
          green: '#A0C35A',
          blue: '#B0C4EF',
          purple: '#BA81C5',
        },
        game: {
          bg: '#1a1a2e',
          tile: '#2d2d44',
          'tile-selected': '#4a4a6a',
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
