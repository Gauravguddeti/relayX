/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Design System Colors
        text: '#FAFAFA',
        background: '#161616',
        primary: '#DAED6E',
        secondary: '#000000',
        accent: '#FFFFFF',
        // Additional shades
        'bg-dark': '#161616',
        'bg-darker': '#0A0A0A',
        'bg-lighter': '#1E1E1E',
        'text-primary': '#FAFAFA',
        'text-secondary': '#A0A0A0',
      },
      fontSize: {
        'title': '32px',
        'body': '18px',
        'small': '14px',
      },
      fontFamily: {
        'title': ['Space Grotesk', 'sans-serif'],
        'body': ['Ubuntu', 'sans-serif'],
      },
      fontWeight: {
        'title': '700',
        'body': '400',
        'body-bold': '700',
      }
    },
  },
  plugins: [],
};
