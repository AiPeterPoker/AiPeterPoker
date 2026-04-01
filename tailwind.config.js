/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx,html}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['Outfit', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'SF Mono', 'monospace'],
      },
      colors: {
        hud: {
          bg: 'rgba(8, 10, 16, 0.94)',
          panel: 'rgba(255, 255, 255, 0.03)',
          border: 'rgba(80, 200, 120, 0.18)',
        },
        accent: {
          DEFAULT: '#50c878',
          dim: 'rgba(80, 200, 120, 0.15)',
        },
        accent2: {
          DEFAULT: '#f0b429',
          dim: 'rgba(240, 180, 41, 0.15)',
        },
      },
    },
  },
  plugins: [],
};
