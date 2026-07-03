/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./backend/app1/templates/**/*.html", // Ищи внутри папки бэкенда от корня
    "./backend/app1/static/js/**/*.js",
  ],
  safelist: [
    'fixed',
    'inset-0',
    'bg-black/20',
    'backdrop-blur-sm',
    'z-30',
    'translate-x-full',
    'translate-x-0',
    '-translate-x-full'
  ],
  theme: { extend: {} },
  plugins: [],
}
