/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'sans-serif'],
      },
      colors: {
        brand: {
          primary: 'var(--color-brand-primary)',
          hover: 'var(--color-brand-hover)',
          soft: 'var(--color-brand-soft)',
        },
        surface: {
          sidebar: 'var(--color-surface-sidebar)',
          app: 'var(--color-surface-app)',
          card: 'var(--color-surface-card)',
        },
      },
      boxShadow: {
        card: 'var(--shadow-card)',
        float: 'var(--shadow-float)',
        auth: 'var(--shadow-auth)',
      },
    },
  },
  plugins: [],
};
