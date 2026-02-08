/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./apps/web/manganize_web/templates/**/*.html",
    "./apps/web/manganize_web/static/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        'manga-pink': '#FFB6C1',
        'manga-blue': '#87CEEB',
        'manga-yellow': '#FFE4B5',
      },
    },
  },
  plugins: [],
}
