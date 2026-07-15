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
        "primary": "#1b7898",
        "background-light": "#f9fafa",
        "background-dark": "#22252a",
      },
      fontFamily: {
        "display": ["Manrope", "sans-serif"]
      },
    },
  },
  plugins: [],
}
