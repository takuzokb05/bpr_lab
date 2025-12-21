/** @type {import('tailwindcss').Config} */
import colors from 'tailwindcss/colors';

export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                gray: colors.zinc,
                primary: colors.zinc[900],
            },
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
            },
            animation: {
                'pulse-fast': 'pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite'
            }
        },
    },
    plugins: [],
}
