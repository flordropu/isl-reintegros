/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // ----- Paleta ISL -----
        // Azul institucional (extraído del logo: #86C1ED)
        isl: {
          50:  '#F0F8FE',
          100: '#DCEEFB',
          200: '#BFE0F7',
          300: '#A2D2F2',
          400: '#86C1ED',
          500: '#5BA8DF',
          600: '#3989C7',
          700: '#286BA0',
          800: '#1E5078',
          900: '#143651',
        },
        // Verde institucional (extraído del logo: #93C13D)
        verde: {
          50:  '#F4FAEA',
          100: '#E5F3CC',
          200: '#CFE89E',
          300: '#B6DC6E',
          400: '#A2D052',
          500: '#93C13D',
          600: '#7AA82E',
          700: '#5E8525',
          800: '#4C9239',
          900: '#365B1A',
        },
        brand: {
          DEFAULT: '#286BA0',
          hover:   '#1E5078',
          light:   '#86C1ED',
          accent:  '#4C9239',
        },
        sla: {
          ok:    '#4C9239',
          warn:  '#EF9F27',
          alert: '#E24B4A',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02)',
        'card-hover': '0 4px 12px rgba(0, 0, 0, 0.06), 0 2px 4px rgba(0, 0, 0, 0.04)',
      },
    },
  },
  plugins: [],
}
