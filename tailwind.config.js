/** @type {import('tailwindcss').Config} */
// NOTE: In Tailwind v4, this file is used only for content scanning.
// All design tokens (colors, spacing, fonts) are defined in src/index.css via @theme.
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
}
