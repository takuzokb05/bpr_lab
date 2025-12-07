/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            fontFamily: {
                sans: ['"Zen Maru Gothic"', "sans-serif"],
            },
            colors: {
                "cream": "#FFFDF5",
                "text-main": "#4B5563",
                "accent-pink": "#FDA4AF",
                "accent-mint": "#6EE7B7",
                "border-main": "#D1D5DB",
            },
            boxShadow: {
                'comic': '4px 4px 0px 0px #000000',
            }
        },
    },
    plugins: [],
}
