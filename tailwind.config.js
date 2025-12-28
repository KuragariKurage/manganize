/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./web/templates/**/*.html",
    "./web/static/**/*.js",
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
