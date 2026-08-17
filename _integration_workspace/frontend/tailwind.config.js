/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./main.jsx",
    "./App.jsx",
    "./pages/**/*.{js,jsx}",
    "./components/**/*.{js,jsx}",
    "./theme/**/*.{js,jsx}"
  ],
  darkMode: 'class',
  corePlugins: {
    preflight: false
  },
  theme: {
    extend: {}
  }
}
