/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        dark: {
          bg: '#0f0f10',
          card: '#1a1a1d',
          hover: '#222226',
          border: '#2a2a2e',
        },
        accent: {
          DEFAULT: '#00a2a7',
          hover: '#00babe',
          light: '#2cd3d8',
          dark: '#00797d',
        },
      },
    },
  },
  plugins: [],
}
