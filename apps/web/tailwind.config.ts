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
          yellow: '#F5A623',
          green:  '#4CAF50',
          blue:   '#42A5F5',
          purple: '#AB47BC',
        },
        game: {
          bg:              '#0d1a0e',
          tile:            '#1a3a1e',
          'tile-selected': '#2d5e35',
          'tile-hover':    '#243f28',
          accent:          '#F5A623',
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
